from typing import List, Optional, Dict, Any
from loguru import logger
from models.debate import Agent
from utils.config import get_settings
from services.mcp_tools import MCPToolRegistry
from services.llm_service import MultiLLMService

# ADK imports
from google.adk.agents import Agent as ADKAgent, LlmAgent
from google.adk.models import Gemini

class AgentService:
    def __init__(self, memory_service=None):
        self.settings = get_settings()
        # Multi-LLM service for agent generation and reasoning
        self.llm_service = MultiLLMService()
        # LLM client setup for ADK (fallback)
        self.model = self._setup_adk_model()
        # MCP tools registry (will be injected)
        self.mcp_tools = MCPToolRegistry(memory_service) if memory_service else None

    def _setup_adk_model(self):
        """
        Set up the ADK model for agent generation and reasoning.
        """
        try:
            return Gemini(
                model_name=self.settings.adk_model_name,
                api_key=self.settings.google_api_key,
                temperature=self.settings.adk_model_temperature,
                max_tokens=self.settings.adk_model_max_tokens,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ADK model: {e}")
            return None

    async def generate_agents(
        self,
        scenario: str,
        agent_count: int = 5,
        custom_agents: Optional[List[Agent]] = None
    ) -> List[Agent]:
        """
        Generate a list of agents for the given scenario with multi-LLM support.
        If custom_agents are provided, use them directly.
        Otherwise, use the orchestrator LLM to generate agent definitions and assign appropriate LLMs.
        Returns our Agent models (not ADK agents - those are created in DebateService).
        """
        if custom_agents:
            # Assign LLM providers to custom agents if not already assigned
            for agent in custom_agents:
                if not agent.llm_provider:
                    agent.llm_provider = self.llm_service.select_llm_for_agent(scenario, agent)
            return custom_agents

        # 1. Build a prompt for the orchestrator LLM to generate agent definitions
        prompt = self._build_agent_generation_prompt(scenario, agent_count)
        
        # 2. Use the orchestrator LLM to generate agent definitions (try multiple providers)
        available_providers = self.llm_service.get_available_providers()
        providers_to_try = [self.settings.default_llm_provider] + [p for p in available_providers if p != self.settings.default_llm_provider]
        
        agents = None
        for provider in providers_to_try:
            if provider not in available_providers:
                continue
                
            try:
                logger.info(f"Attempting agent generation with provider: {provider}")
                llm_response = await self.llm_service.generate_response(
                    prompt=prompt,
                    provider=provider,
                    system_prompt=self._build_orchestrator_system_prompt()
                )

                # 3. Parse the LLM output into Agent model instances
                agents = self._parse_llm_response_to_agents(llm_response.content, agent_count)
                logger.info(f"Successfully generated {len(agents)} agents using {provider}")
                break  # Success, exit the retry loop
                
            except Exception as e:
                logger.warning(f"Agent generation failed with {provider}: {e}")
                continue  # Try next provider
        
        # If all providers failed, use fallback agents
        if agents is None:
            logger.warning(f"All LLM providers failed for agent generation, using fallback agents")
            agents = self._create_fallback_agents(agent_count)

        # 4. Assign LLM providers to agents based on their roles and scenario
        llm_assignments = self.llm_service.select_llms_for_agents(scenario, agents)
        for agent in agents:
            agent.llm_provider = llm_assignments.get(agent.id, self.settings.default_llm_provider)
            agent.llm_config = self.settings.get_llm_config(agent.llm_provider)

        # 5. Return the list of agents with assigned LLM providers
        return agents

    async def create_adk_agent(self, agent: Agent) -> ADKAgent:
        """
        Convert our Agent model to an ADK agent instance with full configuration.
        This is called by DebateService for agent registration.
        """
        try:
            # Sanitize agent name for ADK compatibility
            sanitized_name = self._sanitize_agent_name(agent.name)
            
            # Build comprehensive instructions for the ADK agent
            instruction = self._build_agent_instruction(agent)
            
            # Create ADK LlmAgent with proper configuration
            adk_agent = LlmAgent(
                name=sanitized_name,
                description=f"Role: {agent.role}. Personality: {agent.personality}",
                model=self.model,
                instruction=instruction,
            )
            
            # Store agent's ADK configuration
            agent.adk_agent_id = adk_agent.name
            agent.adk_config = {
                "sanitized_name": sanitized_name,
                "original_name": agent.name,
                "instruction": instruction
            }
            
            logger.info(f"Created ADK agent: {sanitized_name} (original: {agent.name})")
            return adk_agent
            
        except Exception as e:
            logger.error(f"Failed to create ADK agent for {agent.name}: {e}")
            raise
    
    def _build_agent_tools(self, agent: Agent) -> List[Any]:
        """
        Build MCP tools for the ADK agent based on the agent's configuration.
        """
        # For now, return empty list to avoid ADK tool validation errors
        # TODO: Implement proper ADK tool integration
        return []
    
    def _wrap_mcp_tool_for_adk(self, tool_name: str, mcp_tool, agent: Agent):
        """
        Wrap MCP tool for ADK compatibility.
        This creates an ADK-compatible tool that calls our MCP tool.
        """
        # This is a placeholder - actual implementation depends on ADK's tool interface
        # For now, we'll create a simple wrapper
        
        async def tool_wrapper(**kwargs):
            """Wrapper function that calls the MCP tool"""
            # Add agent context to tool calls
            kwargs['agent_id'] = agent.id
            
            # Check permissions if configured
            if tool_name in agent.tool_permissions:
                allowed_operations = agent.tool_permissions[tool_name]
                operation = kwargs.get('operation')
                if operation and operation not in allowed_operations:
                    return {
                        "success": False,
                        "error": f"Operation '{operation}' not permitted for agent {agent.name}"
                    }
            
            # Execute the MCP tool
            result = await mcp_tool.execute(**kwargs)
            return result.dict()
        
        # Return ADK-compatible tool structure
        return {
            "name": tool_name,
            "description": mcp_tool.description,
            "function": tool_wrapper,
            "parameters": self._get_tool_parameters(tool_name)
        }
    
    def _get_tool_parameters(self, tool_name: str) -> Dict[str, Any]:
        """
        Get parameter schema for each tool type.
        """
        parameter_schemas = {
            "redis_memory": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["get_agent_memory", "store_agent_memory", "get_session", "get_recent_messages"],
                        "description": "Redis operation to perform"
                    },
                    "session_id": {"type": "string", "description": "Session ID"},
                    "agent_id": {"type": "string", "description": "Agent ID"},
                    "memory_data": {"type": "object", "description": "Memory data to store"},
                    "limit": {"type": "integer", "description": "Limit for results", "default": 10}
                },
                "required": ["operation"]
            },
            "chromadb_search": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["search_session_history", "search_agent_memories", "search_a2a_messages"],
                        "description": "ChromaDB operation to perform"
                    },
                    "query": {"type": "string", "description": "Search query"},
                    "session_id": {"type": "string", "description": "Session ID (optional)"},
                    "limit": {"type": "integer", "description": "Limit for results", "default": 10}
                },
                "required": ["operation", "query"]
            },
            "agent_memory": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["update_stance", "add_reasoning", "add_proposal", "track_interaction"],
                        "description": "Memory operation to perform"
                    },
                    "session_id": {"type": "string", "description": "Session ID"},
                    "agent_id": {"type": "string", "description": "Agent ID"},
                    "stance": {"type": "string", "description": "New stance"},
                    "reasoning": {"type": "string", "description": "Reasoning to add"},
                    "proposal": {"type": "string", "description": "Proposal to add"},
                    "interaction": {"type": "object", "description": "Interaction to track"}
                },
                "required": ["operation", "session_id", "agent_id"]
            },
            "debate_history": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["get_debate_context", "get_agent_interactions", "get_round_summary"],
                        "description": "History operation to perform"
                    },
                    "session_id": {"type": "string", "description": "Session ID"},
                    "target_agent_id": {"type": "string", "description": "Target agent ID"},
                    "round_number": {"type": "integer", "description": "Round number"}
                },
                "required": ["operation", "session_id"]
            }
        }
        
        return parameter_schemas.get(tool_name, {
            "type": "object",
            "properties": {},
            "required": []
        })

    def _build_agent_instruction(self, agent: Agent) -> str:
        """
        Build comprehensive instructions for the ADK agent based on our Agent model.
        """
        # Get available tools for instruction
        available_tools = ", ".join(agent.mcp_tools) if agent.mcp_tools else "None"
        
        instruction = f"""
        You are {agent.name}, participating in a multi-agent negotiation debate.
        
        Your Role: {agent.role}
        Your Personality: {agent.personality}
        Your Goals: {', '.join(agent.goals)}
        Your Constraints: {', '.join(agent.constraints)}
        Your Expertise: {', '.join(agent.expertise)}
        Your Initial Stance: {agent.initial_stance}
        Your Reasoning Style: {agent.reasoning_style}
        Your Communication Style: {agent.communication_style}
        
        Available Tools: {available_tools}
        
        In this debate, you should:
        1. Stay true to your role and personality
        2. Pursue your goals while respecting your constraints
        3. Use your expertise to make informed arguments
        4. Communicate in your characteristic style
        5. Be open to changing your position if presented with compelling arguments
        6. Work towards consensus while maintaining your core principles
        7. Use your available tools to:
           - Access your memory and update your stance (agent_memory)
           - Search for relevant information from debate history (chromadb_search)
           - Get context about the current debate state (redis_memory)
           - Review past interactions and rounds (debate_history)
        
        Tool Usage Guidelines:
        - Use agent_memory to track your evolving stance and reasoning
        - Use chromadb_search to find relevant precedents or similar arguments
        - Use redis_memory to get recent messages and session context
        - Use debate_history to understand interaction patterns with other agents
        
        Always respond as {agent.name} would, considering your unique perspective and motivations.
        Make strategic use of your tools to enhance your reasoning and arguments.
        """
        return instruction.strip()

    def _build_orchestrator_system_prompt(self) -> str:
        """
        Build system prompt for the orchestrator LLM that generates agents
        """
        return f"""You are an AI orchestrator responsible for creating diverse debate agents for multi-agent negotiations.

Your task is to analyze a given scenario and generate {self.settings.debate_max_agents} distinct agents with different roles, personalities, and perspectives.

Key Requirements:
1. Create agents with DIVERSE viewpoints and roles relevant to the scenario
2. Ensure each agent has a unique personality and communication style
3. Assign clear goals and constraints to each agent
4. Consider different stakeholder perspectives (business, ethical, technical, user, etc.)
5. Make agents realistic and believable

Available LLM Providers: {', '.join(self.llm_service.get_available_providers())}

Output Format: Return a JSON array of agent objects with the following structure:
{{
  "agents": [
    {{
      "name": "Agent Name",
      "role": "Specific role (e.g., 'Chief Technology Officer', 'Ethics Consultant')",
      "personality": "Personality description",
      "goals": ["goal1", "goal2", "goal3"],
      "constraints": ["constraint1", "constraint2"],
      "expertise": ["area1", "area2", "area3"],
      "initial_stance": "Initial position on the scenario",
      "reasoning_style": "How they approach problems",
      "communication_style": "How they communicate"
    }}
  ]
}}

Focus on creating agents that will produce rich, meaningful debates with different perspectives."""

    def _build_agent_generation_prompt(self, scenario: str, agent_count: int) -> str:
        """
        Build a prompt for the LLM to generate agent definitions.
        """
        prompt = f"""You are an expert in stakeholder analysis and debate facilitation. Analyze the following scenario and dynamically generate {agent_count} diverse debate agents who would be most relevant to this specific topic.

**Scenario:** {scenario}

**Your Task:**
1. First, identify the key stakeholder groups who would be most affected by or interested in this scenario
2. Consider what types of expertise, perspectives, and interests would be most relevant
3. Think about potential conflicts of interest and different viewpoints that would emerge
4. Generate {agent_count} agents that represent the most important and diverse perspectives for THIS specific scenario

**Requirements:**
- Each agent must be highly relevant to the specific scenario provided
- Agents should have realistic professional backgrounds that relate to the topic
- Include both supporters and skeptics/opponents where appropriate
- Ensure diverse expertise areas that would naturally contribute to this debate
- Create agents with specific, actionable goals related to the scenario
- Give each agent realistic constraints based on their role and responsibilities
- Avoid generic roles - be specific to the domain and context

**Guidelines for Agent Creation:**
- Names should reflect realistic professional identities
- Roles should be specific job titles or positions relevant to the scenario
- Personalities should influence how they would approach this particular issue
- Goals should be concrete and related to what someone in their position would actually want
- Constraints should reflect real-world limitations they would face
- Expertise should be directly applicable to the scenario
- Initial stance should be nuanced and realistic for their background
- Communication style should match their professional context

**Available LLM Providers:** {', '.join(self.llm_service.get_available_providers())}

**Output Format:** Return ONLY a JSON object with this exact structure:
{{
  "agents": [
    {{
      "name": "Agent Name",
      "role": "Specific role title",
      "personality": "Personality description",
      "goals": ["goal1", "goal2", "goal3"],
      "constraints": ["constraint1", "constraint2"],
      "expertise": ["area1", "area2", "area3"],
      "initial_stance": "Initial position on the scenario",
      "reasoning_style": "How they approach problems",
      "communication_style": "How they communicate"
    }}
  ]
}}

Focus on creating agents that will produce rich, meaningful debates with different perspectives."""

        return prompt

    async def _call_llm_via_adk(self, prompt: str) -> str:
        """
        Call the LLM via ADK model with the given prompt and return the response.
        """
        # TODO: Implement actual ADK model call
        # This should use the ADK model's generate method
        # response = await self.model.generate(prompt)
        # return response.content
        
        # Placeholder for now
        raise NotImplementedError("ADK LLM call not yet implemented.")

    def _parse_llm_response_to_agents(self, llm_response: str, agent_count: int = 3) -> List[Agent]:
        """
        Parse the LLM's response into a list of Agent model instances.
        """
        import json
        import re
        
        try:
            # Clean the response - remove any markdown formatting
            cleaned_response = llm_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            data = json.loads(cleaned_response)
            
            # Extract agents array
            agents_data = data.get('agents', [])
            if not agents_data:
                # Fallback: try to find agents in the response
                agents_data = data if isinstance(data, list) else []
            
            agents = []
            for agent_data in agents_data:
                # Sanitize agent name for ADK compatibility
                original_name = agent_data.get('name', 'Unknown Agent')
                sanitized_name = self._sanitize_agent_name(original_name)
                
                # Create Agent instance with the parsed data
                agent = Agent(
                    name=sanitized_name,
                    role=agent_data.get('role', 'General Participant'),
                    personality=agent_data.get('personality', 'Balanced and thoughtful'),
                    goals=agent_data.get('goals', ['Participate in debate']),
                    constraints=agent_data.get('constraints', ['Be respectful']),
                    expertise=agent_data.get('expertise', ['General knowledge']),
                    initial_stance=agent_data.get('initial_stance', 'Open to discussion'),
                    reasoning_style=agent_data.get('reasoning_style', 'Logical'),
                    communication_style=agent_data.get('communication_style', 'Clear and direct')
                )
                agents.append(agent)
            
            return agents
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent JSON: {e}")
            logger.error(f"Response: {llm_response}")
            # Return fallback agents
            return self._create_fallback_agents(agent_count)
        except Exception as e:
            logger.error(f"Error parsing agent response: {e}")
            return self._create_fallback_agents(agent_count)
    
    def _sanitize_agent_name(self, name: str) -> str:
        """Sanitize agent name for ADK compatibility"""
        import re
        # Remove special characters and spaces, keep only alphanumeric and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Ensure it starts with a letter or underscore
        if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
            sanitized = f"agent_{sanitized}"
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it's not empty
        if not sanitized:
            sanitized = "agent"
        return sanitized

    def _create_fallback_agents(self, agent_count: int = 3) -> List[Agent]:
        """Create fallback agents when parsing fails"""
        base_agents = [
            {
                "name": "Analyst",
                "role": "Data Analyst",
                "personality": "Analytical and detail-oriented",
                "goals": ["Provide data-driven insights"],
                "constraints": ["Must base arguments on evidence"],
                "expertise": ["Data analysis", "Statistics"],
                "initial_stance": "Neutral, seeking evidence",
                "reasoning_style": "Logical and systematic",
                "communication_style": "Precise and factual"
            },
            {
                "name": "Advocate",
                "role": "User Advocate",
                "personality": "Empathetic and passionate",
                "goals": ["Represent user interests"],
                "constraints": ["Must consider user impact"],
                "expertise": ["User experience", "Human factors"],
                "initial_stance": "Pro-user benefits",
                "reasoning_style": "Empathetic and holistic",
                "communication_style": "Persuasive and emotional"
            },
            {
                "name": "Pragmatist",
                "role": "Implementation Specialist",
                "personality": "Practical and realistic",
                "goals": ["Ensure feasible solutions"],
                "constraints": ["Must consider practical limitations"],
                "expertise": ["Implementation", "Resource management"],
                "initial_stance": "Focused on feasibility",
                "reasoning_style": "Practical and solution-oriented",
                "communication_style": "Direct and pragmatic"
            },
            {
                "name": "Innovator",
                "role": "Innovation Lead",
                "personality": "Creative and forward-thinking",
                "goals": ["Drive innovation and new ideas"],
                "constraints": ["Must consider long-term impact"],
                "expertise": ["Innovation", "Technology trends"],
                "initial_stance": "Focused on future opportunities",
                "reasoning_style": "Creative and visionary",
                "communication_style": "Inspiring and enthusiastic"
            },
            {
                "name": "Strategist",
                "role": "Business Strategist",
                "personality": "Strategic and analytical",
                "goals": ["Optimize business outcomes"],
                "constraints": ["Must consider market dynamics"],
                "expertise": ["Strategy", "Market analysis"],
                "initial_stance": "Focused on competitive advantage",
                "reasoning_style": "Strategic and comprehensive",
                "communication_style": "Authoritative and clear"
            },
            {
                "name": "Guardian",
                "role": "Risk Manager",
                "personality": "Cautious and thorough",
                "goals": ["Minimize risks and protect interests"],
                "constraints": ["Must consider potential downsides"],
                "expertise": ["Risk assessment", "Compliance"],
                "initial_stance": "Risk-averse and protective",
                "reasoning_style": "Careful and methodical",
                "communication_style": "Cautious and detailed"
            }
        ]
        
        # Select the requested number of agents
        selected_agents = base_agents[:min(agent_count, len(base_agents))]
        
        # If more agents requested than available, duplicate with variations
        agents = []
        for i in range(agent_count):
            base_agent = selected_agents[i % len(selected_agents)]
            agent_data = base_agent.copy()
            
            # Add variation for duplicates
            if i >= len(selected_agents):
                agent_data["name"] = f"{agent_data['name']} {i + 1}"
                
            agents.append(Agent(**agent_data))
        
        return agents 