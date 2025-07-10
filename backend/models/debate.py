"""
Data models for the Multi-Agent Negotiation Framework
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid

class AgentRole(str, Enum):
    """Agent roles in the debate"""
    FINANCE = "finance"
    OPERATIONS = "operations"
    MARKETING = "marketing"
    LEGAL = "legal"
    TECHNOLOGY = "technology"
    HUMAN_RESOURCES = "human_resources"
    CUSTOMER_SERVICE = "customer_service"
    STRATEGY = "strategy"

class AgentPersonality(str, Enum):
    """Agent personality types"""
    COOPERATIVE = "cooperative"
    COMPETITIVE = "competitive"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    CONSERVATIVE = "conservative"
    PROGRESSIVE = "progressive"

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

class Agent(BaseModel):
    """Agent model representing a debate participant"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: AgentRole
    personality: AgentPersonality
    goals: List[str]
    constraints: List[str]
    expertise: List[str]
    initial_stance: str
    reasoning_style: str
    communication_style: str
    
    class Config:
        use_enum_values = True

class DebateMessage(BaseModel):
    """Model for debate messages between agents"""
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

class DebateSession(BaseModel):
    """Model for a debate session"""
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
    
    class Config:
        use_enum_values = True

class DebateRound(BaseModel):
    """Model for a single debate round"""
    round_number: int
    session_id: str
    messages: List[DebateMessage]
    start_time: datetime
    end_time: Optional[datetime] = None
    consensus_evaluated: bool = False
    consensus_result: Optional[ConsensusResult] = None

class AgentMemory(BaseModel):
    """Model for agent's memory and context"""
    agent_id: str
    session_id: str
    past_proposals: List[str] = []
    past_reasoning: List[str] = []
    current_stance: str
    goals_achieved: List[str] = []
    constraints_violated: List[str] = []
    interaction_history: List[Dict[str, Any]] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class DebateContext(BaseModel):
    """Model for debate context and shared information"""
    session_id: str
    scenario: str
    debate_history: List[DebateMessage] = []
    current_round: int
    agent_memories: Dict[str, AgentMemory] = {}
    shared_context: Dict[str, Any] = {}
    constraints: List[str] = []
    objectives: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Request/Response models for API endpoints

class StartSessionRequest(BaseModel):
    """Request model for starting a debate session"""
    scenario: str = Field(..., description="The scenario to debate")
    agent_count: int = Field(default=5, ge=3, le=10, description="Number of agents to generate")
    max_rounds: int = Field(default=10, ge=1, le=50, description="Maximum debate rounds")
    custom_agents: Optional[List[Agent]] = Field(default=None, description="Custom agent definitions")

class StartSessionResponse(BaseModel):
    """Response model for starting a debate session"""
    session_id: str
    agents: List[Agent]
    status: str
    message: str

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

class DebateMessageResponse(BaseModel):
    """Response model for debate messages"""
    message: DebateMessage
    session_id: str
    round_number: int

class ConsensusResponse(BaseModel):
    """Response model for consensus evaluation"""
    consensus_reached: bool
    consensus_level: float
    agreement_points: List[str]
    disagreement_points: List[str]
    final_decision: Optional[str]
    voting_results: Dict[str, Any] 