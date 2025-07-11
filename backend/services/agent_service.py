from typing import List, Optional
from models.debate import Agent
from utils.config import get_settings

# ADK imports
from google.adk.agents import Agent as ADKAgent, LlmAgent
from google.adk.models import GeminiModel

class AgentService:
    def __init__(self):
        self.settings = get_settings()
        # LLM client setup for ADK
        self.model = self._setup_adk_model()

    def _setup_adk_model(self):
        """
        Set up the ADK model for agent generation and reasoning.
        """
        # TODO: Configure with actual API keys and model settings from config
        return GeminiModel(
            model_name=self.settings.llm_model_name,
            # api_key=self.settings.google_api_key,  # Will be added in config update
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
        )

    async def generate_agents(
        self,
        scenario: str,
        agent_count: int = 5,
        custom_agents: Optional[List[Agent]] = None
    ) -> List[Agent]:
        """
        Generate a list of agents for the given scenario.
        If custom_agents are provided, use them directly.
        Otherwise, use the LLM to generate agent definitions.
        Returns our Agent models (not ADK agents - those are created in DebateService).
        """
        if custom_agents:
            return custom_agents

        # 1. Build a prompt for the LLM describing the scenario and agent requirements
        prompt = self._build_agent_generation_prompt(scenario, agent_count)

        # 2. Call the LLM (using ADK model) to generate agent definitions
        llm_response = await self._call_llm_via_adk(prompt)

        # 3. Parse the LLM output into Agent model instances
        agents = self._parse_llm_response_to_agents(llm_response)

        # 4. Return the list of agents
        return agents

    async def create_adk_agent(self, agent: Agent) -> ADKAgent:
        """
        Convert our Agent model to an ADK agent instance with full configuration.
        This is called by DebateService for agent registration.
        """
        # Create ADK LlmAgent with comprehensive configuration
        adk_agent = LlmAgent(
            name=agent.name,
            description=f"Role: {agent.role}. Personality: {agent.personality}",
            model=self.model,
            instruction=self._build_agent_instruction(agent),
            # tools=[],  # Add tools as needed
            # memory_config={},  # Add memory configuration
        )
        
        # TODO: Add agent-specific tools, memory, and behavior configuration
        return adk_agent

    def _build_agent_instruction(self, agent: Agent) -> str:
        """
        Build comprehensive instructions for the ADK agent based on our Agent model.
        """
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
        
        In this debate, you should:
        1. Stay true to your role and personality
        2. Pursue your goals while respecting your constraints
        3. Use your expertise to make informed arguments
        4. Communicate in your characteristic style
        5. Be open to changing your position if presented with compelling arguments
        6. Work towards consensus while maintaining your core principles
        
        Always respond as {agent.name} would, considering your unique perspective and motivations.
        """
        return instruction.strip()

    def _build_agent_generation_prompt(self, scenario: str, agent_count: int) -> str:
        """
        Build a prompt for the LLM to generate agent definitions.
        """
        prompt = (
            f"You are tasked with designing {agent_count} highly distinct and realistic agents for a multi-agent negotiation framework. "
            f"The goal is to simulate a dynamic and rich negotiation process where agents demonstrate complex reasoning, trade-offs, and interpersonal dynamics. "
            f"Each agent should embody a unique blend of characteristics that influence their decisions, argumentation, and collaboration strategies.\n\n"
            
            f"Scenario:\n{scenario}\n\n"

            f"For each agent, define the following attributes in detail:\n"
            f"1. **Name**: A creative and fitting name.\n"
            f"2. **Role**: What function or perspective the agent represents in the negotiation (e.g., environmental advocate, financial analyst, political mediator).\n"
            f"3. **Personality Traits**: Describe 3-5 key personality traits (e.g., assertive, analytical, empathetic, opportunistic, risk-averse).\n"
            f"4. **Primary Goals**: Define what the agent ultimately wants to achieve in the negotiation.\n"
            f"5. **Constraints and Limitations**: Outline factors that restrict the agent's flexibility (e.g., ethical boundaries, resource constraints, organizational policies).\n"
            f"6. **Domain Expertise**: Detail their areas of knowledge and specialization.\n"
            f"7. **Initial Stance**: What position or proposal does the agent begin the negotiation with?\n"
            f"8. **Reasoning Style**: Describe how the agent thinks and makes decisions (e.g., logical, heuristic, emotional, probabilistic).\n"
            f"9. **Communication Style**: How the agent communicates during negotiation (e.g., persuasive and charismatic, cautious and formal, blunt and direct).\n"
            f"10. **Tactics and Strategies**: Optional – what negotiation strategies might they employ (e.g., concession-based, aggressive anchoring, coalition building).\n\n"
            
            f"Return the agents as a **JSON array**, where each agent is an object with these fields:\n"
            f"name, role, personality_traits, primary_goals, constraints, expertise, initial_stance, reasoning_style, communication_style, tactics.\n\n"
            
            f"Ensure the agents are:\n"
            f"- Diverse in their roles and approaches.\n"
            f"- Realistic and internally consistent.\n"
            f"- Capable of conflicting, collaborating, and adapting during negotiation.\n\n"
            
            f"Output **only the JSON array** without extra commentary or formatting."
        )

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

    def _parse_llm_response_to_agents(self, llm_response: str) -> List[Agent]:
        """
        Parse the LLM's response into a list of Agent model instances.
        """
        # TODO: Implement JSON parsing and Agent model creation
        # This should parse the JSON array and create Agent objects
        raise NotImplementedError("LLM response parsing not yet implemented.") 