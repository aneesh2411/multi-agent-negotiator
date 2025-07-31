from typing import List, Dict, Any, Optional
from models.debate import DebateSession, Agent, DebateMessage, ConsensusResult
from services.memory_service import MemoryService
from services.agent_service import AgentService
from services.llm_service import MultiLLMService
from utils.config import get_settings
import asyncio
from loguru import logger
from datetime import datetime

# ADK imports
from google.adk.agents import Agent as ADKAgent
# Note: A2A protocol not available in current ADK version, using placeholder
# from google.adk.a2a import A2AProtocol, A2AMessage

class DebateService:
    def __init__(self, memory_service: MemoryService = None):
        self.settings = get_settings()
        self.memory_service = memory_service or MemoryService()
        # Initialize agent service with memory service for MCP tools
        self.agent_service = AgentService(self.memory_service)
        # Initialize multi-LLM service for agent responses
        self.llm_service = MultiLLMService()
        # ADK orchestrator and agent registry
        self.orchestrator: Optional[ADKAgent] = None  # Using generic agent as orchestrator for now
        self.agent_registry: Dict[str, ADKAgent] = {}
        # self.a2a_protocol = A2AProtocol()  # Not available in current ADK version

    async def create_session(self, scenario: str, agents: List[Agent]) -> str:
        """
        Create and initialize a new debate session with ADK orchestrator and agents.
        """
        # 1. Instantiate ADK agents from provided agent definitions using AgentService
        adk_agents = []
        for agent in agents:
            try:
                adk_agent = await self.agent_service.create_adk_agent(agent)
                self.agent_registry[agent.id] = adk_agent
                adk_agents.append(adk_agent)
            except Exception as e:
                logger.warning(f"Failed to create ADK agent for {agent.name}: {e}")
                # Continue with other agents
        # 2. Create ADK orchestrator for this session (placeholder for now)
        # self.orchestrator = Orchestrator(agents=adk_agents, protocol=self.a2a_protocol)
        # Using placeholder until proper ADK orchestrator is available
        self.orchestrator = None
        # 3. Create and store DebateSession as before
        session = DebateSession(
            scenario=scenario,
            agents=agents,
            status="created",
            current_round=0,
            consensus_reached=False,
            messages=[],
        )
        await self.memory_service.store_session(session)
        logger.info(f"Debate session created: {session.id} with ADK orchestrator")
        return session.id

    # Removed _create_adk_agent - now handled by AgentService

    async def start_debate(self, session_id: str, session: DebateSession):
        """
        Start the turn-based debate loop using ADK orchestrator and A2A protocol.
        """
        logger.info(f"Starting ADK debate for session {session_id}")
        max_rounds = session.max_rounds
        for round_num in range(session.current_round + 1, max_rounds + 1):
            session.current_round = round_num
            logger.info(f"Round {round_num} begins (ADK)")
            round_messages = []
            for agent in session.agents:
                adk_agent = self.agent_registry.get(agent.id)
                if not adk_agent:
                    logger.error(f"ADK agent not found for {agent.name}")
                    continue
                
                # 1. Build context for agent (previous messages, agent memory, etc.)
                context = await self._build_agent_context(session, agent)
                
                # 2. Generate agent response using their assigned LLM provider
                try:
                    agent_prompt = self._build_agent_prompt(agent, context, round_num)
                    system_prompt = self._build_agent_system_prompt(agent)
                    
                    # Use the agent's assigned LLM provider
                    llm_response = await self.llm_service.generate_agent_response(
                        agent=agent,
                        prompt=agent_prompt,
                        system_prompt=system_prompt,
                        provider=agent.llm_provider
                    )
                    
                    # 3. Create A2A message for agent's turn
                    a2a_message = self._build_a2a_message(agent, context, round_num)
                    
                    # 4. Create DebateMessage with LLM response
                    message = DebateMessage(
                        session_id=session.id,
                        agent_id=agent.id,
                        agent_name=agent.name,
                        message_type="argument",
                        content=llm_response.content,
                        round_number=round_num,
                        metadata={
                            "llm_provider": llm_response.provider,
                            "llm_model": llm_response.model,
                            "tokens_used": llm_response.tokens_used,
                            "finish_reason": llm_response.finish_reason
                        }
                    )
                    
                    logger.info(f"Agent {agent.name} ({llm_response.provider}) responded in round {round_num}")
                    
                except Exception as e:
                    logger.error(f"Error generating response for {agent.name}: {e}")
                    # Fallback message
                    message = DebateMessage(
                        session_id=session.id,
                        agent_id=agent.id,
                        agent_name=agent.name,
                        message_type="argument",
                        content=f"[Error] Agent {agent.name} encountered an error in round {round_num}.",
                        round_number=round_num,
                        metadata={"error": str(e)}
                    )
                
                session.messages.append(message)
                round_messages.append(message)
                await self.memory_service.store_debate_message(message)
            # 5. Evaluate consensus after each round
            consensus = await self.evaluate_consensus(session_id)
            if consensus.get("consensus_reached", False):
                session.consensus_reached = True
                session.consensus_result = ConsensusResult(**consensus)
                session.status = "consensus_reached"
                logger.info(f"Consensus reached in round {round_num}")
                break
            # 6. Update session state
            await self.memory_service.store_session(session)
        # End debate if max rounds reached
        if not session.consensus_reached:
            session.status = "ended"
            await self.memory_service.store_session(session)
            logger.info(f"Debate ended without consensus: {session_id}")

    def _build_a2a_message(self, agent: Agent, context: Dict[str, Any], round_num: int) -> Dict[str, Any]:
        """
        Build an A2A protocol message for the agent's turn (placeholder).
        """
        # TODO: Map context and agent state to A2A message fields
        # Using dict placeholder until A2A protocol is available
        return {
            "sender": agent.name,
            "content": f"[A2A Stub] Agent {agent.name} turn in round {round_num}.",
            "round": round_num,
            "context": context
        }

    async def _build_agent_context(self, session: DebateSession, agent: Agent) -> Dict[str, Any]:
        """
        Build the context for an agent's turn (history, memory, etc.).
        """
        # For MVP, just provide last N messages and agent's own memory
        messages = session.messages[-5:] if len(session.messages) > 5 else session.messages
        agent_memory = await self.memory_service.get_agent_memory(session.id, agent.id)
        return {
            "recent_messages": messages,
            "agent_memory": agent_memory,
            "scenario": session.scenario,
            "round": session.current_round,
        }

    def _build_agent_prompt(self, agent: Agent, context: Dict[str, Any], round_num: int) -> str:
        """
        Build the prompt for an agent's turn in the debate
        """
        recent_messages = context.get("recent_messages", [])
        agent_memory = context.get("agent_memory", {})
        scenario = context.get("scenario", "")
        
        # Build recent conversation history
        conversation_history = ""
        if recent_messages:
            conversation_history = "\n".join([
                f"{msg.agent_name}: {msg.content}" 
                for msg in recent_messages[-5:]  # Last 5 messages
            ])
        
        # Build agent memory summary
        memory_summary = ""
        if agent_memory:
            memory_summary = f"""
Your current stance: {agent_memory.get('current_stance', 'Not set')}
Your past proposals: {', '.join(agent_memory.get('past_proposals', []))}
Your past reasoning: {', '.join(agent_memory.get('past_reasoning', []))}
"""
        
        prompt = f"""**DEBATE SCENARIO:** {scenario}

**ROUND {round_num}** - It's your turn to contribute to the debate.

**RECENT CONVERSATION:**
{conversation_history or "No previous messages"}

**YOUR MEMORY:**{memory_summary}

**YOUR TASK:**
As {agent.name} ({agent.role}), provide your response to the current debate. Consider:
1. Your role and expertise: {', '.join(agent.expertise)}
2. Your goals: {', '.join(agent.goals)}
3. Your constraints: {', '.join(agent.constraints)}
4. Your reasoning style: {agent.reasoning_style}
5. Your communication style: {agent.communication_style}

**INSTRUCTIONS:**
- Respond in character as {agent.name}
- Address the current debate topic directly
- Consider other agents' points and respond appropriately
- Maintain your personality: {agent.personality}
- Work toward your goals while respecting your constraints
- Be constructive and aim for eventual consensus

**YOUR RESPONSE:**"""
        
        return prompt
    
    def _build_agent_system_prompt(self, agent: Agent) -> str:
        """
        Build the system prompt for an agent
        """
        return f"""You are {agent.name}, a {agent.role} participating in a multi-agent debate.

**Your Character:**
- Personality: {agent.personality}
- Reasoning Style: {agent.reasoning_style}
- Communication Style: {agent.communication_style}

**Your Goals:**
{chr(10).join(f"- {goal}" for goal in agent.goals)}

**Your Constraints:**
{chr(10).join(f"- {constraint}" for constraint in agent.constraints)}

**Your Expertise:**
{chr(10).join(f"- {area}" for area in agent.expertise)}

**Your Initial Stance:** {agent.initial_stance}

**Instructions:**
- Stay in character throughout the debate
- Use your expertise to inform your arguments
- Respect your constraints while pursuing your goals
- Engage constructively with other agents
- Aim for solutions that consider multiple perspectives
- Be authentic to your personality and communication style

Respond as {agent.name} would, maintaining consistency with your character."""

    async def evaluate_consensus(self, session_id: str) -> Dict[str, Any]:
        """
        Evaluate consensus for the session (stub: always returns not reached).
        """
        # TODO: Implement real consensus logic (e.g., Borda count, voting)
        logger.info(f"Evaluating consensus for session {session_id}")
        return {
            "consensus_reached": False,
            "consensus_level": 0.0,
            "agreement_points": [],
            "disagreement_points": [],
            "final_decision": None,
            "voting_results": {},
        }

    # (Optional) Add methods for pause, resume, inject, remove_agent, broadcast_update, etc. 