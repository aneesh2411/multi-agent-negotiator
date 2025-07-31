"""
Multi-LLM Service for the Multi-Agent Negotiation Framework
Supports OpenAI, Anthropic, and Google LLM providers with unified interface
"""

import asyncio
import random
import json
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from loguru import logger
import json

# LLM Provider imports
import openai
import anthropic
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

from utils.config import get_settings
from models.debate import Agent


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = None


class LLMSelectionStrategy:
    """Strategies for selecting LLM providers for agents"""
    
    @staticmethod
    def orchestrator_choice(scenario: str, agent_role: str, available_providers: List[str]) -> str:
        """
        Let the orchestrator choose the best LLM for each agent based on role and scenario.
        This is the most intelligent selection method.
        """
        # Define LLM strengths for different roles
        llm_strengths = {
            "openai": {
                "strengths": ["reasoning", "analysis", "technical", "structured_thinking"],
                "roles": ["analyst", "technical", "researcher", "data_scientist", "engineer"]
            },
            "anthropic": {
                "strengths": ["ethics", "philosophy", "nuanced_reasoning", "safety"],
                "roles": ["ethicist", "philosopher", "legal", "safety_officer", "compliance"]
            },
            "google": {
                "strengths": ["creativity", "diverse_perspectives", "multilingual", "general"],
                "roles": ["creative", "marketing", "general", "user_advocate", "designer"]
            }
        }
        
        # Score each provider based on role match
        scores = {}
        agent_role_lower = agent_role.lower()
        
        for provider in available_providers:
            if provider not in llm_strengths:
                continue
                
            score = 0
            provider_info = llm_strengths[provider]
            
            # Check role match
            for role_keyword in provider_info["roles"]:
                if role_keyword in agent_role_lower:
                    score += 10
            
            # Check strength match with scenario
            scenario_lower = scenario.lower()
            for strength in provider_info["strengths"]:
                if strength in scenario_lower or strength in agent_role_lower:
                    score += 5
            
            scores[provider] = score
        
        # If no clear winner, add some randomness for diversity
        if not scores or max(scores.values()) == 0:
            return random.choice(available_providers)
        
        # Return the highest scoring provider
        return max(scores, key=scores.get)
    
    @staticmethod
    def diverse_selection(agents: List[Agent], available_providers: List[str]) -> Dict[str, str]:
        """
        Ensure diverse LLM selection across all agents for maximum debate diversity
        """
        selections = {}
        provider_counts = {provider: 0 for provider in available_providers}
        
        # Sort agents by some criteria (e.g., role) for consistent selection
        sorted_agents = sorted(agents, key=lambda x: x.role)
        
        for agent in sorted_agents:
            # Find the least used provider
            min_count = min(provider_counts.values())
            least_used = [p for p, count in provider_counts.items() if count == min_count]
            
            # Among least used, prefer the one that matches the agent's role
            selected = LLMSelectionStrategy.orchestrator_choice(
                "general", agent.role, least_used
            )
            
            selections[agent.id] = selected
            provider_counts[selected] += 1
        
        return selections
    
    @staticmethod
    def random_selection(available_providers: List[str]) -> str:
        """Random selection for testing purposes"""
        return random.choice(available_providers)


class MultiLLMService:
    """Service for managing multiple LLM providers"""
    
    def __init__(self):
        self.settings = get_settings()
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients for available providers"""
        
        # Initialize OpenAI client
        if self.settings.openai_api_key:
            self.clients[LLMProvider.OPENAI] = openai.AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                organization=self.settings.openai_organization,
                timeout=self.settings.openai_timeout
            )
            logger.info("OpenAI client initialized")
        
        # Initialize Anthropic client
        if self.settings.anthropic_api_key:
            self.clients[LLMProvider.ANTHROPIC] = anthropic.AsyncAnthropic(
                api_key=self.settings.anthropic_api_key,
                timeout=self.settings.anthropic_timeout
            )
            logger.info("Anthropic client initialized")
        
        # Initialize Google client
        if self.settings.google_api_key:
            try:
                genai.configure(api_key=self.settings.google_api_key)
                self.clients[LLMProvider.GOOGLE] = genai.GenerativeModel(
                    model_name=self.settings.google_default_model
                )
                logger.info("Google Generative AI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google client: {e}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers"""
        return list(self.clients.keys())
    
    def _should_use_mock_mode(self) -> bool:
        """Check if we should use mock mode (no valid API keys available)"""
        # Check if API keys are placeholder values
        invalid_keys = [
            "your_openai_api_key_here",
            "your_anthropic_api_key_here", 
            "your_google_api_key_here"
        ]
        
        # Check if we have at least one valid API key
        openai_valid = (self.settings.openai_api_key and 
                       self.settings.openai_api_key not in invalid_keys and
                       self.settings.openai_api_key.startswith('sk-'))
        
        anthropic_valid = (self.settings.anthropic_api_key and 
                          self.settings.anthropic_api_key not in invalid_keys and
                          self.settings.anthropic_api_key.startswith('sk-ant-'))
        
        google_valid = (self.settings.google_api_key and 
                       self.settings.google_api_key not in invalid_keys and
                       len(self.settings.google_api_key) > 20)
        
        # Use mock mode only if NO valid API keys are available
        return not (openai_valid or anthropic_valid or google_valid)
    
    async def generate_response(
        self,
        prompt: str,
        provider: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response from specified LLM provider
        """
        # Check if we should use mock mode for agent generation
        if ("generate" in prompt.lower() and "agents" in prompt.lower()) or "debate agents" in prompt.lower():
            # Only use mock mode if all API keys are invalid
            if self._should_use_mock_mode():
                logger.info(f"Using mock agent generation due to invalid API keys")
                return await self._generate_mock_agent_response(prompt)
            else:
                logger.info(f"Using real LLM for dynamic agent generation")
        
        # Mock mode for debate responses when API keys are invalid (but NOT for agent generation)
        if (any(word in prompt.lower() for word in ['debate', 'argument', 'position', 'stance']) and 
            not ("generate" in prompt.lower() and "agents" in prompt.lower())):
            # Only use mock mode if no valid API keys are available
            if self._should_use_mock_mode():
                logger.info(f"Using mock debate responses due to invalid API keys")
                return await self._generate_mock_debate_response(prompt, provider, system_prompt)
            else:
                logger.info(f"Using real LLM for role-specific debate responses")
        
        if provider not in self.clients:
            raise ValueError(f"Provider {provider} not available. Available: {list(self.clients.keys())}")
        
        try:
            if provider == LLMProvider.OPENAI:
                return await self._generate_openai_response(
                    prompt, system_prompt, temperature, max_tokens, **kwargs
                )
            elif provider == LLMProvider.ANTHROPIC:
                return await self._generate_anthropic_response(
                    prompt, system_prompt, temperature, max_tokens, **kwargs
                )
            elif provider == LLMProvider.GOOGLE:
                return await self._generate_google_response(
                    prompt, system_prompt, temperature, max_tokens, **kwargs
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")
        
        except Exception as e:
            logger.error(f"Error generating response from {provider}: {e}")
            raise
    
    async def _generate_mock_agent_response(self, prompt: str) -> LLMResponse:
        """Generate mock topic-specific agents when API keys aren't available"""
        import re
        
        # Extract scenario from prompt
        scenario_match = re.search(r'\*\*Scenario:\*\*\s*(.+)', prompt, re.IGNORECASE)
        scenario = scenario_match.group(1).strip() if scenario_match else "general topic"
        logger.info(f"Extracted scenario: '{scenario}'")
        
        # Extract agent count
        count_match = re.search(r'(\d+)\s+agents', prompt)
        agent_count = int(count_match.group(1)) if count_match else 3
        
        # Generate topic-specific agent templates
        agent_templates = self._generate_topic_specific_agents(scenario, agent_count)
        
        mock_response = {
            "agents": agent_templates
        }
        
        return LLMResponse(
            content=json.dumps(mock_response, indent=2),
            provider="mock",
            model="topic-generator",
            tokens_used=len(prompt.split()) + len(str(mock_response).split())
        )
    
    def _generate_topic_specific_agents(self, scenario: str, agent_count: int) -> list:
        """Generate topic-specific agent configurations"""
        import json
        
        # Analyze scenario to determine relevant stakeholders
        scenario_lower = scenario.lower()
        logger.info(f"Analyzing scenario: '{scenario_lower}' for keywords")
        
        # Define agent templates based on topic categories
        if any(word in scenario_lower for word in ['energy', 'renewable', 'solar', 'wind', 'nuclear', 'fossil', 'climate', 'environment', 'carbon', 'emission']):
            logger.info("Using energy/environment-specific agents")
            base_agents = [
                {
                    "name": "Energy Engineer",
                    "role": "Renewable Energy Specialist",
                    "personality": "Technical and solution-oriented",
                    "goals": ["Promote sustainable energy solutions", "Ensure technical feasibility"],
                    "constraints": ["Must consider engineering limitations", "Balance cost and efficiency"],
                    "expertise": ["Renewable energy systems", "Grid integration", "Energy storage"],
                    "initial_stance": "Strongly supportive of renewable energy transition",
                    "reasoning_style": "Technical and data-driven",
                    "communication_style": "Precise and engineering-focused"
                },
                {
                    "name": "Environmental Scientist",
                    "role": "Climate Impact Researcher",
                    "personality": "Analytical and environmentally conscious",
                    "goals": ["Minimize environmental impact", "Promote evidence-based policy"],
                    "constraints": ["Must base arguments on scientific evidence"],
                    "expertise": ["Climate science", "Environmental impact assessment", "Sustainability metrics"],
                    "initial_stance": "Urgently supportive of clean energy",
                    "reasoning_style": "Scientific and evidence-based",
                    "communication_style": "Factual and research-oriented"
                },
                {
                    "name": "Utility Executive",
                    "role": "Energy Industry Leader",
                    "personality": "Business-focused and pragmatic",
                    "goals": ["Ensure grid stability", "Maintain profitability", "Meet regulatory requirements"],
                    "constraints": ["Must consider infrastructure costs", "Balance stakeholder interests"],
                    "expertise": ["Energy markets", "Grid operations", "Regulatory compliance"],
                    "initial_stance": "Cautiously supportive with concerns about costs",
                    "reasoning_style": "Business and risk-focused",
                    "communication_style": "Strategic and business-oriented"
                },
                {
                    "name": "Policy Economist",
                    "role": "Energy Policy Analyst",
                    "personality": "Analytical and policy-focused",
                    "goals": ["Optimize economic outcomes", "Design effective incentives"],
                    "constraints": ["Must consider budget implications", "Balance multiple objectives"],
                    "expertise": ["Energy economics", "Policy design", "Market mechanisms"],
                    "initial_stance": "Supportive with emphasis on economic efficiency",
                    "reasoning_style": "Economic and policy-analytical",
                    "communication_style": "Analytical and policy-focused"
                }
            ]
        elif any(word in scenario_lower for word in ['healthcare', 'medical', 'hospital', 'doctor', 'patient', 'medicine', 'health', 'treatment']):
            logger.info("Using healthcare-specific agents")
            base_agents = [
                {
                    "name": "Chief Medical Officer",
                    "role": "Senior Healthcare Executive",
                    "personality": "Patient-focused and evidence-based",
                    "goals": ["Improve patient outcomes", "Ensure medical quality"],
                    "constraints": ["Must follow medical ethics", "Consider patient safety"],
                    "expertise": ["Clinical medicine", "Healthcare administration", "Medical ethics"],
                    "initial_stance": "Focused on patient welfare and medical evidence",
                    "reasoning_style": "Medical and ethical",
                    "communication_style": "Professional and patient-centered"
                },
                {
                    "name": "Healthcare Administrator",
                    "role": "Hospital Operations Manager",
                    "personality": "Efficiency-focused and systematic",
                    "goals": ["Optimize healthcare delivery", "Manage resources effectively"],
                    "constraints": ["Must work within budget constraints", "Ensure regulatory compliance"],
                    "expertise": ["Healthcare operations", "Resource management", "Healthcare policy"],
                    "initial_stance": "Focused on operational efficiency and sustainability",
                    "reasoning_style": "Systematic and efficiency-focused",
                    "communication_style": "Direct and operations-oriented"
                },
                {
                    "name": "Patient Advocate",
                    "role": "Patient Rights Representative",
                    "personality": "Empathetic and advocacy-focused",
                    "goals": ["Protect patient rights", "Ensure accessible care"],
                    "constraints": ["Must represent diverse patient needs"],
                    "expertise": ["Patient advocacy", "Healthcare access", "Patient experience"],
                    "initial_stance": "Strongly focused on patient needs and access",
                    "reasoning_style": "Empathetic and patient-centered",
                    "communication_style": "Compassionate and advocacy-driven"
                },
                {
                    "name": "Public Health Expert",
                    "role": "Population Health Specialist",
                    "personality": "Data-driven and population-focused",
                    "goals": ["Improve population health outcomes", "Prevent disease"],
                    "constraints": ["Must consider public health data", "Balance individual vs. population needs"],
                    "expertise": ["Epidemiology", "Public health policy", "Health promotion"],
                    "initial_stance": "Focused on evidence-based population health strategies",
                    "reasoning_style": "Data-driven and population-focused",
                    "communication_style": "Scientific and public health-oriented"
                }
            ]
        elif any(word in scenario_lower for word in ['education', 'school', 'student', 'teacher', 'university', 'learning', 'academic']):
            logger.info("Using education-specific agents")
            base_agents = [
                {
                    "name": "Education Administrator",
                    "role": "School District Superintendent",
                    "personality": "Leadership-focused and systematic",
                    "goals": ["Improve educational outcomes", "Manage district resources"],
                    "constraints": ["Must work within budget", "Follow educational regulations"],
                    "expertise": ["Educational leadership", "Policy implementation", "Resource management"],
                    "initial_stance": "Focused on systemic educational improvement",
                    "reasoning_style": "Strategic and administrative",
                    "communication_style": "Professional and leadership-oriented"
                },
                {
                    "name": "Classroom Teacher",
                    "role": "Frontline Educator",
                    "personality": "Student-focused and practical",
                    "goals": ["Help students learn effectively", "Create positive learning environment"],
                    "constraints": ["Must work with available resources", "Follow curriculum requirements"],
                    "expertise": ["Classroom instruction", "Student engagement", "Curriculum delivery"],
                    "initial_stance": "Focused on practical classroom impact",
                    "reasoning_style": "Practical and student-centered",
                    "communication_style": "Direct and classroom-focused"
                },
                {
                    "name": "Parent Representative",
                    "role": "Parent-Teacher Association Leader",
                    "personality": "Child-focused and community-oriented",
                    "goals": ["Advocate for student needs", "Support family involvement"],
                    "constraints": ["Must represent diverse family perspectives"],
                    "expertise": ["Parent advocacy", "Community engagement", "Student support"],
                    "initial_stance": "Strongly focused on student and family needs",
                    "reasoning_style": "Family-centered and advocacy-driven",
                    "communication_style": "Passionate and parent-focused"
                },
                {
                    "name": "Education Researcher",
                    "role": "Educational Policy Analyst",
                    "personality": "Research-focused and evidence-based",
                    "goals": ["Promote evidence-based practices", "Improve educational effectiveness"],
                    "constraints": ["Must base recommendations on research"],
                    "expertise": ["Educational research", "Policy analysis", "Learning science"],
                    "initial_stance": "Focused on research-backed educational strategies",
                    "reasoning_style": "Research-based and analytical",
                    "communication_style": "Academic and evidence-focused"
                }
            ]
        elif any(word in scenario_lower for word in ['work', 'employee', 'company', 'business', 'corporate']):
            logger.info("Using work/business-specific agents")
            base_agents = [
                {
                    "name": "HR Director",
                    "role": "Human Resources Leader",
                    "personality": "People-focused and policy-oriented",
                    "goals": ["Ensure employee wellbeing", "Maintain company culture"],
                    "constraints": ["Must consider legal compliance", "Balance employee and company needs"],
                    "expertise": ["Employee relations", "HR policies", "Workplace dynamics"],
                    "initial_stance": "Cautiously supportive of employee benefits",
                    "reasoning_style": "Policy-based and people-centered",
                    "communication_style": "Professional and empathetic"
                },
                {
                    "name": "Operations Manager",
                    "role": "Business Operations Specialist",
                    "personality": "Results-driven and efficiency-focused",
                    "goals": ["Maximize operational efficiency", "Ensure business continuity"],
                    "constraints": ["Must maintain productivity levels", "Consider operational costs"],
                    "expertise": ["Operations management", "Process optimization", "Resource allocation"],
                    "initial_stance": "Concerned about operational impact",
                    "reasoning_style": "Data-driven and practical",
                    "communication_style": "Direct and fact-based"
                },
                {
                    "name": "Employee Representative",
                    "role": "Worker Advocate",
                    "personality": "Passionate and employee-focused",
                    "goals": ["Advocate for worker rights", "Improve work-life balance"],
                    "constraints": ["Must represent diverse employee interests"],
                    "expertise": ["Labor relations", "Employee needs", "Work-life balance"],
                    "initial_stance": "Strongly supportive of employee benefits",
                    "reasoning_style": "Empathetic and advocacy-based",
                    "communication_style": "Passionate and persuasive"
                },
                {
                    "name": "Financial Controller",
                    "role": "Financial Analyst",
                    "personality": "Conservative and numbers-focused",
                    "goals": ["Protect company financial health", "Ensure cost effectiveness"],
                    "constraints": ["Must maintain fiscal responsibility"],
                    "expertise": ["Financial analysis", "Cost-benefit analysis", "Budget management"],
                    "initial_stance": "Skeptical of costly changes",
                    "reasoning_style": "Analytical and conservative",
                    "communication_style": "Precise and data-focused"
                }
            ]
        elif any(word in scenario_lower for word in ['tech', 'ai', 'software', 'engineer', 'developer']):
            base_agents = [
                {
                    "name": "Senior Developer",
                    "role": "Technical Expert",
                    "personality": "Analytical and innovation-focused",
                    "goals": ["Advance technical capabilities", "Ensure code quality"],
                    "constraints": ["Must consider technical feasibility"],
                    "expertise": ["Software development", "Technical architecture", "Code quality"],
                    "initial_stance": "Optimistic about technological advancement",
                    "reasoning_style": "Technical and logical",
                    "communication_style": "Precise and technical"
                },
                {
                    "name": "Product Manager",
                    "role": "Product Strategy Lead",
                    "personality": "Strategic and user-focused",
                    "goals": ["Deliver valuable products", "Meet user needs"],
                    "constraints": ["Must balance features with timeline"],
                    "expertise": ["Product strategy", "User experience", "Market analysis"],
                    "initial_stance": "Focused on user value",
                    "reasoning_style": "Strategic and user-centered",
                    "communication_style": "Clear and goal-oriented"
                },
                {
                    "name": "Industry Veteran",
                    "role": "Experienced Professional",
                    "personality": "Cautious and experience-based",
                    "goals": ["Share industry wisdom", "Prevent common mistakes"],
                    "constraints": ["Must consider historical context"],
                    "expertise": ["Industry trends", "Historical patterns", "Risk assessment"],
                    "initial_stance": "Cautiously optimistic with historical perspective",
                    "reasoning_style": "Experience-based and cautious",
                    "communication_style": "Thoughtful and measured"
                },
                {
                    "name": "Innovation Advocate",
                    "role": "Technology Evangelist",
                    "personality": "Enthusiastic and forward-thinking",
                    "goals": ["Promote innovation", "Drive technological progress"],
                    "constraints": ["Must consider practical adoption"],
                    "expertise": ["Emerging technologies", "Innovation trends", "Future planning"],
                    "initial_stance": "Enthusiastically supportive of advancement",
                    "reasoning_style": "Visionary and optimistic",
                    "communication_style": "Inspiring and enthusiastic"
                }
            ]
        else:
            # Generic agents for other topics
            base_agents = [
                {
                    "name": "Policy Expert",
                    "role": "Policy Analyst",
                    "personality": "Analytical and policy-focused",
                    "goals": ["Develop sound policies", "Consider long-term implications"],
                    "constraints": ["Must consider regulatory requirements"],
                    "expertise": ["Policy analysis", "Regulatory compliance", "Strategic planning"],
                    "initial_stance": "Focused on policy implications",
                    "reasoning_style": "Systematic and policy-oriented",
                    "communication_style": "Professional and structured"
                },
                {
                    "name": "Community Representative",
                    "role": "Stakeholder Advocate",
                    "personality": "Community-focused and empathetic",
                    "goals": ["Represent community interests", "Ensure inclusive outcomes"],
                    "constraints": ["Must consider diverse perspectives"],
                    "expertise": ["Community engagement", "Stakeholder management", "Social impact"],
                    "initial_stance": "Focused on community benefit",
                    "reasoning_style": "Inclusive and community-centered",
                    "communication_style": "Empathetic and inclusive"
                },
                {
                    "name": "Subject Matter Expert",
                    "role": "Domain Specialist",
                    "personality": "Knowledgeable and detail-oriented",
                    "goals": ["Provide expert insights", "Ensure accuracy"],
                    "constraints": ["Must base arguments on evidence"],
                    "expertise": ["Domain knowledge", "Research methods", "Technical accuracy"],
                    "initial_stance": "Evidence-based and neutral",
                    "reasoning_style": "Expert and evidence-based",
                    "communication_style": "Authoritative and detailed"
                },
                {
                    "name": "Practical Implementer",
                    "role": "Implementation Specialist",
                    "personality": "Practical and results-oriented",
                    "goals": ["Ensure feasible implementation", "Deliver practical solutions"],
                    "constraints": ["Must consider resource limitations"],
                    "expertise": ["Project management", "Implementation planning", "Resource optimization"],
                    "initial_stance": "Focused on practical feasibility",
                    "reasoning_style": "Practical and solution-oriented",
                    "communication_style": "Direct and pragmatic"
                }
            ]
        
        # Select and customize agents based on requested count
        selected_agents = []
        for i in range(agent_count):
            base_agent = base_agents[i % len(base_agents)].copy()
            
            # Customize for duplicates
            if i >= len(base_agents):
                base_agent["name"] = f"{base_agent['name']} {i + 1}"
            
            selected_agents.append(base_agent)
        
        return selected_agents
    
    async def _generate_mock_debate_response(self, prompt: str, provider: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate mock debate responses when API keys aren't available"""
        import re
        
        # Debug: Log a portion of both prompts to see their structure
        logger.info(f"User prompt preview (first 100 chars): {prompt[:100]}...")
        if system_prompt:
            logger.info(f"System prompt preview (first 200 chars): {system_prompt[:200]}...")
        
        # Extract agent name and role from system prompt (where agent identity is defined)
        agent_name = "Agent"
        role = "Participant"
        
        if system_prompt:
            # Extract agent name from system prompt
            agent_match = re.search(r'You are ([A-Za-z_]+)', system_prompt)
            if agent_match:
                agent_name = agent_match.group(1)
            
            # Extract role from system prompt - try multiple patterns
            role_match = re.search(r'Your Role: ([^\\n]+)', system_prompt)
            if not role_match:
                # Try the format: "You are AgentName, a RoleTitle participating..."
                role_match = re.search(r'You are [A-Za-z_]+, a ([^\\n]+) participating', system_prompt)
            if role_match:
                role = role_match.group(1).strip()
        
        # Extract scenario context - try multiple patterns
        scenario_match = re.search(r'\*\*DEBATE SCENARIO:\*\*\s*(.+)', prompt, re.IGNORECASE)
        if not scenario_match:
            scenario_match = re.search(r'\*\*Scenario:\*\*\s*(.+)', prompt, re.IGNORECASE)
        if not scenario_match:
            scenario_match = re.search(r'scenario[:\s]*([^\\n]+)', prompt, re.IGNORECASE)
        scenario = scenario_match.group(1).strip() if scenario_match else "the topic"
        logger.info(f"Debate response - Agent: {agent_name}, Role: {role}, Scenario: {scenario}")
        
        # Generate contextual responses based on role and scenario
        responses = self._get_role_based_responses(agent_name, role, scenario)
        
        # Select a random response
        response_content = random.choice(responses)
        
        return LLMResponse(
            content=response_content,
            provider=f"mock-{provider}",
            model="debate-simulator",
            tokens_used=len(prompt.split()) + len(response_content.split())
        )
    
    def _get_role_based_responses(self, agent_name: str, role: str, scenario: str) -> List[str]:
        """Generate role-appropriate debate responses"""
        
        role_lower = role.lower()
        scenario_lower = scenario.lower()
        
        if "hr" in role_lower or "human resources" in role_lower:
            return [
                f"As an HR professional, I believe we need to carefully consider the employee impact of {scenario}. Our primary concern should be maintaining a positive work environment while ensuring legal compliance.",
                f"From a human resources perspective, {scenario} presents both opportunities and challenges. We must balance employee satisfaction with organizational needs.",
                f"I've seen similar situations in my HR experience, and the key is transparent communication with all stakeholders about {scenario}."
            ]
        elif "operations" in role_lower or "manager" in role_lower:
            return [
                f"Looking at this from an operational standpoint, {scenario} could significantly impact our day-to-day processes. We need to ensure business continuity.",
                f"My primary concern with {scenario} is maintaining our operational efficiency. We can't afford disruptions to our core business functions.",
                f"Based on operational data, {scenario} would require substantial process adjustments. We need to weigh the costs against the benefits."
            ]
        elif "employee" in role_lower or "worker" in role_lower or "advocate" in role_lower:
            return [
                f"Speaking for the employees, {scenario} represents an important step toward better work-life balance and job satisfaction.",
                f"Workers have been asking for changes like {scenario} for years. It's time we prioritize employee wellbeing.",
                f"From the employee perspective, {scenario} isn't just a nice-to-have - it's essential for maintaining morale and reducing burnout."
            ]
        elif "financial" in role_lower or "controller" in role_lower or "analyst" in role_lower:
            return [
                f"From a financial perspective, {scenario} needs to be evaluated based on cost-benefit analysis and long-term fiscal impact.",
                f"The numbers show that {scenario} could have significant budget implications. We need to ensure financial sustainability.",
                f"My analysis suggests that while {scenario} has costs, we should also consider the financial benefits of improved productivity and retention."
            ]
        elif "developer" in role_lower or "technical" in role_lower or "engineer" in role_lower:
            return [
                f"From a technical standpoint, {scenario} aligns with modern development practices and could improve code quality and team collaboration.",
                f"As a developer, I see {scenario} as an opportunity to adopt better technical practices and reduce technical debt.",
                f"The technical community has been moving toward approaches like {scenario}. It's important we stay current with industry trends."
            ]
        elif "product" in role_lower:
            return [
                f"From a product perspective, {scenario} could enhance our ability to deliver value to users and respond to market demands.",
                f"User research indicates that teams implementing {scenario} often deliver better products with higher user satisfaction.",
                f"As a product manager, I'm focused on how {scenario} impacts our ability to build and iterate on great products."
            ]
        elif "veteran" in role_lower or "experienced" in role_lower:
            return [
                f"In my years of experience, I've seen trends like {scenario} come and go. We should proceed cautiously and learn from past implementations.",
                f"Having worked in this industry for decades, {scenario} reminds me of similar initiatives. The key is proper planning and realistic expectations.",
                f"My experience suggests that {scenario} can work, but only with strong leadership commitment and gradual implementation."
            ]
        elif "innovation" in role_lower or "evangelist" in role_lower:
            return [
                f"{scenario} represents exactly the kind of forward-thinking approach we need to stay competitive and attract top talent.",
                f"Innovation requires bold moves like {scenario}. We can't afford to fall behind while our competitors embrace new approaches.",
                f"The future belongs to organizations that embrace change like {scenario}. This is our opportunity to lead rather than follow."
            ]
        else:
            # Generic responses
            return [
                f"Regarding {scenario}, I believe we need to carefully weigh all perspectives and consider the long-term implications.",
                f"My position on {scenario} is that we should proceed thoughtfully, considering both the benefits and potential challenges.",
                f"When it comes to {scenario}, I think the key is finding a balanced approach that addresses everyone's concerns."
            ]
    
    async def _generate_openai_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI"""
        client = self.clients[LLMProvider.OPENAI]
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=self.settings.openai_default_model,
            messages=messages,
            temperature=temperature or self.settings.openai_temperature,
            max_tokens=max_tokens or self.settings.openai_max_tokens,
            **kwargs
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            provider=LLMProvider.OPENAI,
            model=self.settings.openai_default_model,
            tokens_used=response.usage.total_tokens if response.usage else None,
            finish_reason=response.choices[0].finish_reason,
            metadata={"response_id": response.id}
        )
    
    async def _generate_anthropic_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Anthropic"""
        client = self.clients[LLMProvider.ANTHROPIC]
        
        # Anthropic uses system parameter separately
        message_kwargs = {
            "model": self.settings.anthropic_default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature or self.settings.anthropic_temperature,
            "max_tokens": max_tokens or self.settings.anthropic_max_tokens,
            **kwargs
        }
        
        if system_prompt:
            message_kwargs["system"] = system_prompt
        
        response = await client.messages.create(**message_kwargs)
        
        return LLMResponse(
            content=response.content[0].text,
            provider=LLMProvider.ANTHROPIC,
            model=self.settings.anthropic_default_model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason,
            metadata={"response_id": response.id}
        )
    
    async def _generate_google_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Google Generative AI"""
        model = self.clients[LLMProvider.GOOGLE]
        
        # Combine system prompt with user prompt for Google
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=temperature or self.settings.google_temperature,
            max_output_tokens=max_tokens or self.settings.google_max_tokens,
        )
        
        # Generate response
        response = await model.generate_content_async(
            full_prompt,
            generation_config=generation_config
        )
        
        return LLMResponse(
            content=response.text,
            provider=LLMProvider.GOOGLE,
            model=self.settings.google_default_model,
            tokens_used=None,  # Google doesn't provide token count in basic API
            finish_reason=str(response.candidates[0].finish_reason) if response.candidates else None,
            metadata={"response_id": getattr(response, 'id', None)}
        )
    
    def select_llm_for_agent(self, scenario: str, agent: Agent) -> str:
        """
        Select the best LLM provider for a specific agent based on scenario and role
        """
        available_providers = self.get_available_providers()
        
        if not available_providers:
            raise ValueError("No LLM providers available")
        
        if len(available_providers) == 1:
            return available_providers[0]
        
        # Use orchestrator choice strategy
        if self.settings.llm_selection_strategy == "orchestrator_choice":
            return LLMSelectionStrategy.orchestrator_choice(
                scenario, agent.role, available_providers
            )
        elif self.settings.llm_selection_strategy == "random":
            return LLMSelectionStrategy.random_selection(available_providers)
        else:
            # Default to orchestrator choice
            return LLMSelectionStrategy.orchestrator_choice(
                scenario, agent.role, available_providers
            )
    
    def select_llms_for_agents(self, scenario: str, agents: List[Agent]) -> Dict[str, str]:
        """
        Select LLM providers for all agents ensuring diversity
        """
        available_providers = self.get_available_providers()
        
        if not available_providers:
            raise ValueError("No LLM providers available")
        
        if len(available_providers) == 1:
            return {agent.id: available_providers[0] for agent in agents}
        
        # Use diverse selection for multiple agents
        return LLMSelectionStrategy.diverse_selection(agents, available_providers)
    
    async def generate_agent_response(
        self,
        agent: Agent,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response for a specific agent using their assigned LLM provider
        """
        if not provider:
            # If no provider specified, use default or select one
            provider = getattr(agent, 'llm_provider', self.settings.default_llm_provider)
        
        return await self.generate_response(
            prompt=prompt,
            provider=provider,
            system_prompt=system_prompt,
            **kwargs
        )
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about available providers"""
        info = {}
        
        for provider in self.get_available_providers():
            config = self.settings.get_llm_config(provider)
            info[provider] = {
                "model": config.get("model"),
                "available": True,
                "configured": True
            }
        
        return info 