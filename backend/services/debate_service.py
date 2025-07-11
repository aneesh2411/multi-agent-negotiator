from typing import List, Dict, Any, Optional
from models.debate import DebateSession, Agent, DebateMessage, ConsensusResult
from services.memory_service import MemoryService
from utils.config import get_settings
import asyncio
from loguru import logger
from datetime import datetime

# ADK imports
from google.adk.agents import Agent as ADKAgent, Orchestrator
from google.adk.a2a import A2AProtocol, A2AMessage

class DebateService:
    def __init__(self):
        self.settings = get_settings()
        self.memory_service = MemoryService()  # Should be injected in real app
        # ADK orchestrator and agent registry
        self.orchestrator: Optional[Orchestrator] = None
        self.agent_registry: Dict[str, ADKAgent] = {}
        self.a2a_protocol = A2AProtocol()

    async def create_session(self, scenario: str, agents: List[Agent]) -> str:
        """
        Create and initialize a new debate session with ADK orchestrator and agents.
        """
        # 1. Instantiate ADK agents from provided agent definitions
        adk_agents = []
        for agent in agents:
            adk_agent = self._create_adk_agent(agent)
            self.agent_registry[agent.id] = adk_agent
            adk_agents.append(adk_agent)
        # 2. Create ADK orchestrator for this session
        self.orchestrator = Orchestrator(agents=adk_agents, protocol=self.a2a_protocol)
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

    def _create_adk_agent(self, agent: Agent) -> ADKAgent:
        """
        Convert our Agent model to an ADK agent instance.
        """
        # TODO: Map all relevant fields and behaviors
        return ADKAgent(
            name=agent.name,
            description=agent.role,
            # Add more fields as needed
        )

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
                # 2. Create A2A message for agent's turn
                a2a_message = self._build_a2a_message(agent, context, round_num)
                # 3. Send message via ADK orchestrator (stub)
                # TODO: Implement ADK agent turn and message handling
                # response = await self.orchestrator.send_message(adk_agent, a2a_message)
                # 4. Parse response and create DebateMessage
                # TODO: Parse A2A response to DebateMessage
                message = DebateMessage(
                    session_id=session.id,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    message_type="argument",
                    content=f"[ADK Stub] Agent {agent.name} responds in round {round_num}.",
                    round_number=round_num,
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

    def _build_a2a_message(self, agent: Agent, context: Dict[str, Any], round_num: int) -> A2AMessage:
        """
        Build an A2A protocol message for the agent's turn.
        """
        # TODO: Map context and agent state to A2A message fields
        return A2AMessage(
            sender=agent.name,
            content=f"[A2A Stub] Agent {agent.name} turn in round {round_num}.",
            # Add more fields as needed
        )

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