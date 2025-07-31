"""
MCP Tools for Multi-Agent Negotiation Framework
Provides Redis and ChromaDB tools for agents to access memory and search capabilities
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from loguru import logger
import json
from datetime import datetime

from services.memory_service import MemoryService
from models.debate import AgentMemory, DebateMessage, A2AMessage


class MCPToolResult(BaseModel):
    """Result from MCP tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPToolRegistry:
    """Registry for MCP tools available to agents"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Any]:
        """Register all available MCP tools"""
        return {
            "redis_memory": RedisTool(self.memory_service),
            "chromadb_search": ChromaDBTool(self.memory_service),
            "agent_memory": AgentMemoryTool(self.memory_service),
            "debate_history": DebateHistoryTool(self.memory_service)
        }
    
    def get_tool(self, tool_name: str):
        """Get a tool by name"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.tools.keys())
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all tools"""
        return {
            name: tool.description 
            for name, tool in self.tools.items()
        }


class BaseMCPTool:
    """Base class for MCP tools"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        self.description = "Base MCP tool"
    
    async def execute(self, **kwargs) -> MCPToolResult:
        """Execute the tool with given parameters"""
        raise NotImplementedError


class RedisTool(BaseMCPTool):
    """Redis MCP tool for memory operations"""
    
    def __init__(self, memory_service: MemoryService):
        super().__init__(memory_service)
        self.description = "Access Redis for memory operations (get/set agent memory, session data)"
    
    async def execute(self, operation: str, **kwargs) -> MCPToolResult:
        """
        Execute Redis operations
        
        Operations:
        - get_agent_memory: Get agent's memory
        - store_agent_memory: Store agent's memory
        - get_session: Get session data
        - get_recent_messages: Get recent debate messages
        """
        try:
            if operation == "get_agent_memory":
                session_id = kwargs.get("session_id")
                agent_id = kwargs.get("agent_id")
                
                if not session_id or not agent_id:
                    return MCPToolResult(
                        success=False,
                        error="Missing session_id or agent_id"
                    )
                
                memory = await self.memory_service.get_agent_memory(session_id, agent_id)
                return MCPToolResult(
                    success=True,
                    data=memory.dict() if memory else None,
                    metadata={"operation": "get_agent_memory"}
                )
            
            elif operation == "store_agent_memory":
                memory_data = kwargs.get("memory_data")
                if not memory_data:
                    return MCPToolResult(
                        success=False,
                        error="Missing memory_data"
                    )
                
                memory = AgentMemory(**memory_data)
                await self.memory_service.store_agent_memory(memory)
                return MCPToolResult(
                    success=True,
                    data={"stored": True},
                    metadata={"operation": "store_agent_memory"}
                )
            
            elif operation == "get_session":
                session_id = kwargs.get("session_id")
                if not session_id:
                    return MCPToolResult(
                        success=False,
                        error="Missing session_id"
                    )
                
                session = await self.memory_service.get_session(session_id)
                return MCPToolResult(
                    success=True,
                    data=session.dict() if session else None,
                    metadata={"operation": "get_session"}
                )
            
            elif operation == "get_recent_messages":
                session_id = kwargs.get("session_id")
                limit = kwargs.get("limit", 10)
                
                if not session_id:
                    return MCPToolResult(
                        success=False,
                        error="Missing session_id"
                    )
                
                messages = await self.memory_service.get_session_messages(session_id)
                recent_messages = messages[-limit:] if len(messages) > limit else messages
                
                return MCPToolResult(
                    success=True,
                    data=[msg.dict() for msg in recent_messages],
                    metadata={"operation": "get_recent_messages", "count": len(recent_messages)}
                )
            
            else:
                return MCPToolResult(
                    success=False,
                    error=f"Unknown Redis operation: {operation}"
                )
        
        except Exception as e:
            logger.error(f"Redis tool error: {e}")
            return MCPToolResult(
                success=False,
                error=str(e)
            )


class ChromaDBTool(BaseMCPTool):
    """ChromaDB MCP tool for semantic search operations"""
    
    def __init__(self, memory_service: MemoryService):
        super().__init__(memory_service)
        self.description = "Perform semantic searches on debate history, agent memories, and A2A messages"
    
    async def execute(self, operation: str, **kwargs) -> MCPToolResult:
        """
        Execute ChromaDB operations
        
        Operations:
        - search_session_history: Search session history
        - search_agent_memories: Search agent memories
        - search_a2a_messages: Search A2A messages
        - search_debate_messages: Search debate messages
        """
        try:
            query = kwargs.get("query")
            if not query:
                return MCPToolResult(
                    success=False,
                    error="Missing query parameter"
                )
            
            limit = kwargs.get("limit", 10)
            session_id = kwargs.get("session_id")
            
            if operation == "search_session_history":
                results = await self.memory_service.search_session_history(query, limit)
                return MCPToolResult(
                    success=True,
                    data=results,
                    metadata={"operation": "search_session_history", "query": query}
                )
            
            elif operation == "search_agent_memories":
                results = await self.memory_service.search_agent_memories(query, session_id, limit)
                return MCPToolResult(
                    success=True,
                    data=results,
                    metadata={"operation": "search_agent_memories", "query": query}
                )
            
            elif operation == "search_a2a_messages":
                results = await self.memory_service.search_a2a_messages(query, session_id, limit)
                return MCPToolResult(
                    success=True,
                    data=results,
                    metadata={"operation": "search_a2a_messages", "query": query}
                )
            
            else:
                return MCPToolResult(
                    success=False,
                    error=f"Unknown ChromaDB operation: {operation}"
                )
        
        except Exception as e:
            logger.error(f"ChromaDB tool error: {e}")
            return MCPToolResult(
                success=False,
                error=str(e)
            )


class AgentMemoryTool(BaseMCPTool):
    """Specialized tool for agent memory management"""
    
    def __init__(self, memory_service: MemoryService):
        super().__init__(memory_service)
        self.description = "Manage agent memory (update stance, add reasoning, track interactions)"
    
    async def execute(self, operation: str, **kwargs) -> MCPToolResult:
        """
        Execute agent memory operations
        
        Operations:
        - update_stance: Update agent's current stance
        - add_reasoning: Add reasoning to agent's memory
        - add_proposal: Add proposal to agent's memory
        - track_interaction: Track interaction with another agent
        """
        try:
            session_id = kwargs.get("session_id")
            agent_id = kwargs.get("agent_id")
            
            if not session_id or not agent_id:
                return MCPToolResult(
                    success=False,
                    error="Missing session_id or agent_id"
                )
            
            # Get current memory
            memory = await self.memory_service.get_agent_memory(session_id, agent_id)
            if not memory:
                # Create new memory if doesn't exist
                memory = AgentMemory(
                    agent_id=agent_id,
                    session_id=session_id,
                    current_stance="",
                    last_updated=datetime.utcnow()
                )
            
            if operation == "update_stance":
                new_stance = kwargs.get("stance")
                if not new_stance:
                    return MCPToolResult(
                        success=False,
                        error="Missing stance parameter"
                    )
                
                memory.current_stance = new_stance
                memory.last_updated = datetime.utcnow()
                
            elif operation == "add_reasoning":
                reasoning = kwargs.get("reasoning")
                if not reasoning:
                    return MCPToolResult(
                        success=False,
                        error="Missing reasoning parameter"
                    )
                
                memory.past_reasoning.append(reasoning)
                memory.last_updated = datetime.utcnow()
                
            elif operation == "add_proposal":
                proposal = kwargs.get("proposal")
                if not proposal:
                    return MCPToolResult(
                        success=False,
                        error="Missing proposal parameter"
                    )
                
                memory.past_proposals.append(proposal)
                memory.last_updated = datetime.utcnow()
                
            elif operation == "track_interaction":
                interaction = kwargs.get("interaction")
                if not interaction:
                    return MCPToolResult(
                        success=False,
                        error="Missing interaction parameter"
                    )
                
                memory.interaction_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "interaction": interaction
                })
                memory.last_updated = datetime.utcnow()
                
            else:
                return MCPToolResult(
                    success=False,
                    error=f"Unknown memory operation: {operation}"
                )
            
            # Store updated memory
            await self.memory_service.store_agent_memory(memory)
            
            return MCPToolResult(
                success=True,
                data=memory.dict(),
                metadata={"operation": operation}
            )
        
        except Exception as e:
            logger.error(f"Agent memory tool error: {e}")
            return MCPToolResult(
                success=False,
                error=str(e)
            )


class DebateHistoryTool(BaseMCPTool):
    """Tool for accessing debate history and context"""
    
    def __init__(self, memory_service: MemoryService):
        super().__init__(memory_service)
        self.description = "Access debate history, A2A messages, and context for decision making"
    
    async def execute(self, operation: str, **kwargs) -> MCPToolResult:
        """
        Execute debate history operations
        
        Operations:
        - get_debate_context: Get full debate context
        - get_agent_interactions: Get interactions with specific agent
        - get_round_summary: Get summary of specific round
        """
        try:
            session_id = kwargs.get("session_id")
            if not session_id:
                return MCPToolResult(
                    success=False,
                    error="Missing session_id"
                )
            
            if operation == "get_debate_context":
                # Get session data
                session = await self.memory_service.get_session(session_id)
                messages = await self.memory_service.get_session_messages(session_id)
                a2a_messages = await self.memory_service.get_a2a_messages(session_id)
                
                context = {
                    "session": session.dict() if session else None,
                    "messages": [msg.dict() for msg in messages],
                    "a2a_messages": [msg.dict() for msg in a2a_messages],
                    "message_count": len(messages),
                    "rounds": session.current_round if session else 0
                }
                
                return MCPToolResult(
                    success=True,
                    data=context,
                    metadata={"operation": "get_debate_context"}
                )
            
            elif operation == "get_agent_interactions":
                target_agent_id = kwargs.get("target_agent_id")
                if not target_agent_id:
                    return MCPToolResult(
                        success=False,
                        error="Missing target_agent_id"
                    )
                
                messages = await self.memory_service.get_session_messages(session_id)
                agent_messages = [
                    msg for msg in messages 
                    if msg.agent_id == target_agent_id
                ]
                
                return MCPToolResult(
                    success=True,
                    data=[msg.dict() for msg in agent_messages],
                    metadata={"operation": "get_agent_interactions", "target_agent": target_agent_id}
                )
            
            elif operation == "get_round_summary":
                round_number = kwargs.get("round_number")
                if round_number is None:
                    return MCPToolResult(
                        success=False,
                        error="Missing round_number"
                    )
                
                messages = await self.memory_service.get_session_messages(session_id)
                round_messages = [
                    msg for msg in messages 
                    if msg.round_number == round_number
                ]
                
                return MCPToolResult(
                    success=True,
                    data=[msg.dict() for msg in round_messages],
                    metadata={"operation": "get_round_summary", "round": round_number}
                )
            
            else:
                return MCPToolResult(
                    success=False,
                    error=f"Unknown debate history operation: {operation}"
                )
        
        except Exception as e:
            logger.error(f"Debate history tool error: {e}")
            return MCPToolResult(
                success=False,
                error=str(e)
            ) 