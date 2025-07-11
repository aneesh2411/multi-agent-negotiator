"""
Data models for the Multi-Agent Negotiation Framework with ADK and A2A protocol support
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import uuid

class DebateStatus(str, Enum):
    """Debate session status"""
    CREATED = "created"
    DEBATING = "debating"
    PAUSED = "paused"
    CONSENSUS_REACHED = "consensus_reached"
    ENDED = "ended"

class MessageType(str, Enum):
    """Types of debate messages"""
    ARGUMENT = "argument"
    RESPONSE = "response"
    CONSENSUS_PROPOSAL = "consensus_proposal"
    SYSTEM_MESSAGE = "system_message"
    A2A_MESSAGE = "a2a_message"  # ADK A2A protocol message

class A2AMessageType(str, Enum):
    """A2A protocol message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class Agent(BaseModel):
    """Agent model representing a debate participant with ADK compatibility"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: str  # Open-ended, LLM-driven
    personality: str  # Open-ended, LLM-driven
    goals: List[str]
    constraints: List[str]
    expertise: List[str]
    initial_stance: str
    reasoning_style: str
    communication_style: str
    
    # ADK-specific fields
    adk_agent_id: Optional[str] = None  # ADK agent instance ID
    adk_config: Dict[str, Any] = Field(default_factory=dict)  # ADK agent configuration
    tools: List[str] = Field(default_factory=list)  # Available tools for this agent
    
    class Config:
        use_enum_values = True

class A2AMessage(BaseModel):
    """A2A protocol message structure"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: A2AMessageType
    sender: str  # Agent name or ID
    receiver: Optional[str] = None  # Target agent (None for broadcast)
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None  # For request-response correlation
    
    class Config:
        use_enum_values = True

class DebateMessage(BaseModel):
    """Model for debate messages between agents with A2A protocol support"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    agent_id: str
    agent_name: str
    message_type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    round_number: int
    response_to: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    # A2A protocol fields
    a2a_message: Optional[A2AMessage] = None  # Original A2A message if applicable
    a2a_correlation_id: Optional[str] = None  # Link to A2A message chain
    
    class Config:
        use_enum_values = True

class ConsensusResult(BaseModel):
    """Model for consensus evaluation results"""
    consensus_reached: bool
    consensus_level: float  # 0.0 to 1.0
    agreement_points: List[str]
    disagreement_points: List[str]
    final_decision: Optional[str] = None
    voting_results: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # ADK-specific consensus fields
    consensus_method: str = "simple_majority"  # voting, borda_count, etc.
    agent_votes: Dict[str, Any] = Field(default_factory=dict)  # Individual agent votes

class DebateSession(BaseModel):
    """Model for a debate session with ADK orchestrator support"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: str
    agents: List[Agent]
    status: DebateStatus = DebateStatus.CREATED
    current_round: int = 0
    max_rounds: int = 10
    consensus_reached: bool = False
    consensus_result: Optional[ConsensusResult] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[DebateMessage] = []
    metadata: Dict[str, Any] = {}
    
    # ADK-specific fields
    orchestrator_id: Optional[str] = None  # ADK orchestrator instance ID
    adk_session_config: Dict[str, Any] = Field(default_factory=dict)  # ADK session configuration
    a2a_message_history: List[A2AMessage] = Field(default_factory=list)  # Full A2A message log
    
    class Config:
        use_enum_values = True

class DebateRound(BaseModel):
    """Model for a single debate round with A2A message tracking"""
    round_number: int
    session_id: str
    messages: List[DebateMessage]
    start_time: datetime
    end_time: Optional[datetime] = None
    consensus_evaluated: bool = False
    consensus_result: Optional[ConsensusResult] = None
    
    # A2A protocol tracking
    a2a_messages: List[A2AMessage] = Field(default_factory=list)  # A2A messages in this round
    agent_interactions: Dict[str, List[str]] = Field(default_factory=dict)  # Agent-to-agent interactions

class AgentMemory(BaseModel):
    """Model for agent's memory and context with ADK integration"""
    agent_id: str
    session_id: str
    past_proposals: List[str] = []
    past_reasoning: List[str] = []
    current_stance: str
    goals_achieved: List[str] = []
    constraints_violated: List[str] = []
    interaction_history: List[Dict[str, Any]] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # ADK-specific memory fields
    adk_context: Dict[str, Any] = Field(default_factory=dict)  # ADK agent context
    tool_usage_history: List[Dict[str, Any]] = Field(default_factory=list)  # Tool calls made
    a2a_interaction_log: List[A2AMessage] = Field(default_factory=list)  # A2A messages sent/received

class DebateContext(BaseModel):
    """Model for debate context and shared information with ADK orchestrator state"""
    session_id: str
    scenario: str
    debate_history: List[DebateMessage] = []
    current_round: int
    agent_memories: Dict[str, AgentMemory] = {}
    shared_context: Dict[str, Any] = {}
    constraints: List[str] = []
    objectives: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # ADK orchestrator state
    orchestrator_state: Dict[str, Any] = Field(default_factory=dict)
    a2a_protocol_state: Dict[str, Any] = Field(default_factory=dict)
    active_agent_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

# Request/Response models for API endpoints

class StartSessionRequest(BaseModel):
    """Request model for starting a debate session"""
    scenario: str = Field(..., description="The scenario to debate")
    agent_count: int = Field(default=5, ge=3, le=10, description="Number of agents to generate")
    max_rounds: int = Field(default=10, ge=1, le=50, description="Maximum debate rounds")
    custom_agents: Optional[List[Agent]] = Field(default=None, description="Custom agent definitions")
    
    # ADK-specific configuration
    adk_config: Dict[str, Any] = Field(default_factory=dict, description="ADK orchestrator configuration")
    consensus_method: str = Field(default="simple_majority", description="Consensus evaluation method")

class StartSessionResponse(BaseModel):
    """Response model for starting a debate session"""
    session_id: str
    agents: List[Agent]
    status: str
    message: str
    
    # ADK-specific response fields
    adk_orchestrator: str = "initialized"
    agent_registry: List[str] = Field(default_factory=list)  # ADK agent IDs

class SessionStatusResponse(BaseModel):
    """Response model for session status"""
    session_id: str
    scenario: str
    agents: List[Agent]
    status: DebateStatus
    current_round: int
    consensus_reached: bool
    messages_count: int
    created_at: datetime
    
    # ADK-specific status fields
    adk_orchestrator: str
    active_agents: List[str] = Field(default_factory=list)
    a2a_message_count: int = 0

class DebateMessageResponse(BaseModel):
    """Response model for debate messages"""
    message: DebateMessage
    session_id: str
    round_number: int
    
    # A2A protocol information
    a2a_correlation: Optional[str] = None
    agent_interactions: List[str] = Field(default_factory=list)

class ConsensusResponse(BaseModel):
    """Response model for consensus evaluation"""
    consensus_reached: bool
    consensus_level: float
    agreement_points: List[str]
    disagreement_points: List[str]
    final_decision: Optional[str]
    voting_results: Dict[str, Any]
    
    # ADK consensus details
    consensus_method: str
    agent_votes: Dict[str, Any]
    orchestrator_recommendation: Optional[str] = None 