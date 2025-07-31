"""
Memory service for managing Redis and ChromaDB connections and operations with ADK support
"""

import redis.asyncio as redis
import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime, timedelta

from utils.config import get_settings
from models.debate import DebateSession, AgentMemory, DebateContext, DebateMessage, A2AMessage

class MemoryService:
    """Service for managing memory operations with Redis and ChromaDB, with ADK integration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.chroma_client: Optional[chromadb.Client] = None
        self.collections: Dict[str, Any] = {}
        
    async def initialize(self):
        """Initialize Redis and ChromaDB connections"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test Redis connection
            await self.redis_client.ping()
            logger.info("Redis connection established")
            
            # Initialize ChromaDB connection
            if self.settings.is_development():
                # Use embedded ChromaDB for development
                import os
                os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
                self.chroma_client = chromadb.Client()
                logger.info("Using embedded ChromaDB for development")
            else:
                # Use client-server mode for production
                self.chroma_client = chromadb.Client(ChromaSettings(
                    chroma_api_impl="rest",
                    chroma_server_host=self.settings.chroma_host,
                    chroma_server_http_port=self.settings.chroma_port
                ))
                logger.info(f"Using ChromaDB server at {self.settings.chroma_host}:{self.settings.chroma_port}")
            
            # Create collections
            await self._create_collections()
            logger.info("ChromaDB connection established")
            
        except Exception as e:
            logger.error(f"Error initializing memory service: {e}")
            raise
    
    async def _create_collections(self):
        """Create ChromaDB collections for different data types including ADK-specific collections"""
        try:
            # Existing collections
            self.collections["debate_sessions"] = self.chroma_client.get_or_create_collection(
                name="debate_sessions",
                metadata={"description": "Debate session data"}
            )
            
            self.collections["agent_memories"] = self.chroma_client.get_or_create_collection(
                name="agent_memories",
                metadata={"description": "Agent memory and context data"}
            )
            
            self.collections["debate_messages"] = self.chroma_client.get_or_create_collection(
                name="debate_messages",
                metadata={"description": "Debate message history"}
            )
            
            # ADK-specific collections
            self.collections["a2a_messages"] = self.chroma_client.get_or_create_collection(
                name="a2a_messages",
                metadata={"description": "A2A protocol message history"}
            )
            
            self.collections["adk_agent_contexts"] = self.chroma_client.get_or_create_collection(
                name="adk_agent_contexts",
                metadata={"description": "ADK agent context and state"}
            )
            
            self.collections["adk_orchestrator_states"] = self.chroma_client.get_or_create_collection(
                name="adk_orchestrator_states",
                metadata={"description": "ADK orchestrator state snapshots"}
            )
            
            logger.info("ChromaDB collections created successfully (including ADK collections)")
            
        except Exception as e:
            logger.error(f"Error creating ChromaDB collections: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup connections"""
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Memory service cleanup completed")
    
    async def check_redis_connection(self) -> bool:
        """Check Redis connection status"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except Exception as e:
            logger.error(f"Redis connection check failed: {e}")
            return False
    
    async def check_chromadb_connection(self) -> bool:
        """Check ChromaDB connection status"""
        try:
            if self.chroma_client:
                # Try to get collection info
                self.chroma_client.list_collections()
                return True
            return False
        except Exception as e:
            logger.error(f"ChromaDB connection check failed: {e}")
            return False
    
    # Redis Operations for Active Debate State (Enhanced for ADK)
    
    async def store_session(self, session: DebateSession):
        """Store debate session in Redis with ADK orchestrator state"""
        try:
            key = f"session:{session.id}"
            data = session.dict()
            await self.redis_client.setex(
                key,
                self.settings.memory_ttl_seconds,
                json.dumps(data, default=str)
            )
            
            # Store ADK orchestrator state separately if present
            if session.orchestrator_id:
                await self.store_adk_orchestrator_state(session.id, session.orchestrator_id, session.adk_session_config)
            
            logger.info(f"Stored session {session.id} in Redis (with ADK state)")
        except Exception as e:
            logger.error(f"Error storing session: {e}")
            raise
    
    async def store_adk_orchestrator_state(self, session_id: str, orchestrator_id: str, state: Dict[str, Any]):
        """Store ADK orchestrator state in Redis"""
        try:
            key = f"adk_orchestrator:{session_id}:{orchestrator_id}"
            await self.redis_client.setex(
                key,
                self.settings.memory_ttl_seconds,
                json.dumps(state, default=str)
            )
            logger.debug(f"Stored ADK orchestrator state for session {session_id}")
        except Exception as e:
            logger.error(f"Error storing ADK orchestrator state: {e}")
            raise
    
    async def get_adk_orchestrator_state(self, session_id: str, orchestrator_id: str) -> Optional[Dict[str, Any]]:
        """Get ADK orchestrator state from Redis"""
        try:
            key = f"adk_orchestrator:{session_id}:{orchestrator_id}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting ADK orchestrator state: {e}")
            return None
    
    async def store_adk_agent_context(self, session_id: str, agent_id: str, context: Dict[str, Any]):
        """Store ADK agent context in Redis"""
        try:
            key = f"adk_agent_context:{session_id}:{agent_id}"
            await self.redis_client.setex(
                key,
                self.settings.memory_ttl_seconds,
                json.dumps(context, default=str)
            )
        except Exception as e:
            logger.error(f"Error storing ADK agent context: {e}")
            raise
    
    async def get_adk_agent_context(self, session_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get ADK agent context from Redis"""
        try:
            key = f"adk_agent_context:{session_id}:{agent_id}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting ADK agent context: {e}")
            return None

    async def get_session(self, session_id: str) -> Optional[DebateSession]:
        """Get debate session from Redis"""
        try:
            key = f"session:{session_id}"
            data = await self.redis_client.get(key)
            if data:
                session_data = json.loads(data)
                return DebateSession(**session_data)
            return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def store_agent_memory(self, memory: AgentMemory):
        """Store agent memory in Redis with ADK context"""
        try:
            key = f"agent_memory:{memory.session_id}:{memory.agent_id}"
            data = memory.dict()
            await self.redis_client.setex(
                key,
                self.settings.memory_ttl_seconds,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.error(f"Error storing agent memory: {e}")
            raise
    
    async def get_agent_memory(self, session_id: str, agent_id: str) -> Optional[AgentMemory]:
        """Get agent memory from Redis"""
        try:
            key = f"agent_memory:{session_id}:{agent_id}"
            data = await self.redis_client.get(key)
            if data:
                memory_data = json.loads(data)
                return AgentMemory(**memory_data)
            return None
        except Exception as e:
            logger.error(f"Error getting agent memory: {e}")
            return None
    
    async def store_debate_message(self, message: DebateMessage):
        """Store debate message in Redis for active session"""
        try:
            key = f"debate_messages:{message.session_id}"
            # Store in Redis list for active session
            await self.redis_client.lpush(
                key,
                json.dumps(message.dict(), default=str)
            )
            # Set TTL for the list
            await self.redis_client.expire(key, self.settings.memory_ttl_seconds)
        except Exception as e:
            logger.error(f"Error storing debate message: {e}")
            raise
    
    async def store_a2a_message(self, message: A2AMessage, session_id: str):
        """Store A2A protocol message in Redis for active session"""
        try:
            key = f"a2a_messages:{session_id}"
            await self.redis_client.lpush(
                key,
                json.dumps(message.dict(), default=str)
            )
            await self.redis_client.expire(key, self.settings.memory_ttl_seconds)
            logger.debug(f"Stored A2A message from {message.sender} in session {session_id}")
        except Exception as e:
            logger.error(f"Error storing A2A message: {e}")
            raise
    
    async def get_a2a_messages(self, session_id: str, limit: int = 50) -> List[A2AMessage]:
        """Get A2A messages for a session from Redis"""
        try:
            key = f"a2a_messages:{session_id}"
            messages_data = await self.redis_client.lrange(key, 0, limit - 1)
            messages = []
            for msg_data in messages_data:
                msg_dict = json.loads(msg_data)
                messages.append(A2AMessage(**msg_dict))
            return messages
        except Exception as e:
            logger.error(f"Error getting A2A messages: {e}")
            return []

    async def get_session_messages(self, session_id: str) -> List[DebateMessage]:
        """Get all messages for a session from Redis"""
        try:
            key = f"debate_messages:{session_id}"
            messages_data = await self.redis_client.lrange(key, 0, -1)
            messages = []
            for msg_data in messages_data:
                msg_dict = json.loads(msg_data)
                messages.append(DebateMessage(**msg_dict))
            return messages
        except Exception as e:
            logger.error(f"Error getting session messages: {e}")
            return []
    
    # ChromaDB Operations for Session History (Enhanced for ADK)
    
    async def store_session_history(self, session: DebateSession):
        """Store session history in ChromaDB with ADK metadata"""
        try:
            collection = self.collections["debate_sessions"]
            
            # Prepare metadata including ADK information
            metadata = {
                "session_id": session.id,
                "scenario": session.scenario[:100],  # Truncate for metadata
                "status": session.status,
                "agent_count": len(session.agents),
                "round_count": session.current_round,
                "consensus_reached": session.consensus_reached,
                "created_at": session.created_at.isoformat(),
                "has_adk_orchestrator": bool(session.orchestrator_id),
                "a2a_message_count": len(session.a2a_message_history)
            }
            
            # Store session data
            collection.add(
                documents=[json.dumps(session.dict(), default=str)],
                metadatas=[metadata],
                ids=[session.id]
            )
            
            logger.debug(f"Stored session history for {session.id} in ChromaDB")
            
        except Exception as e:
            logger.error(f"Error storing session history: {e}")
            raise
    
    async def store_a2a_message_history(self, message: A2AMessage, session_id: str):
        """Store A2A message in ChromaDB for long-term history"""
        try:
            collection = self.collections["a2a_messages"]
            
            metadata = {
                "session_id": session_id,
                "message_type": message.message_type,
                "sender": message.sender,
                "receiver": message.receiver or "broadcast",
                "timestamp": message.timestamp.isoformat(),
                "has_correlation_id": bool(message.correlation_id)
            }
            
            collection.add(
                documents=[message.content],
                metadatas=[metadata],
                ids=[message.id]
            )
            
        except Exception as e:
            logger.error(f"Error storing A2A message history: {e}")
            raise

    async def store_agent_memory_history(self, memory: AgentMemory):
        """Store agent memory in ChromaDB with ADK context"""
        try:
            collection = self.collections["agent_memories"]
            
            metadata = {
                "agent_id": memory.agent_id,
                "session_id": memory.session_id,
                "stance": memory.current_stance[:100],  # Truncate for metadata
                "goals_count": len(memory.goals_achieved),
                "constraints_violated": len(memory.constraints_violated),
                "last_updated": memory.last_updated.isoformat(),
                "has_adk_context": bool(memory.adk_context),
                "tool_usage_count": len(memory.tool_usage_history)
            }
            
            # Combine all memory content for document
            memory_content = f"""
            Current Stance: {memory.current_stance}
            Past Proposals: {'; '.join(memory.past_proposals)}
            Past Reasoning: {'; '.join(memory.past_reasoning)}
            Goals Achieved: {'; '.join(memory.goals_achieved)}
            ADK Context: {json.dumps(memory.adk_context)}
            """
            
            collection.add(
                documents=[memory_content],
                metadatas=[metadata],
                ids=[f"{memory.session_id}_{memory.agent_id}"]
            )
            
        except Exception as e:
            logger.error(f"Error storing agent memory history: {e}")
            raise

    async def store_debate_message_history(self, message: DebateMessage):
        """Store debate message in ChromaDB with A2A correlation"""
        try:
            collection = self.collections["debate_messages"]
            
            metadata = {
                "session_id": message.session_id,
                "agent_id": message.agent_id,
                "agent_name": message.agent_name,
                "message_type": message.message_type,
                "round_number": message.round_number,
                "timestamp": message.timestamp.isoformat(),
                "has_a2a_correlation": bool(message.a2a_correlation_id)
            }
            
            collection.add(
                documents=[message.content],
                metadatas=[metadata],
                ids=[message.id]
            )
            
        except Exception as e:
            logger.error(f"Error storing debate message history: {e}")
            raise

    async def search_session_history(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search session history in ChromaDB"""
        try:
            collection = self.collections["debate_sessions"]
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            return [
                {
                    "session_id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                }
                for i in range(len(results["ids"][0]))
            ]
            
        except Exception as e:
            logger.error(f"Error searching session history: {e}")
            return []

    async def search_agent_memories(self, query: str, session_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search agent memories in ChromaDB"""
        try:
            collection = self.collections["agent_memories"]
            
            where_filter = {}
            if session_id:
                where_filter["session_id"] = session_id
            
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter if where_filter else None
            )
            
            return [
                {
                    "memory_id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                }
                for i in range(len(results["ids"][0]))
            ]
            
        except Exception as e:
            logger.error(f"Error searching agent memories: {e}")
            return []
    
    async def search_a2a_messages(self, query: str, session_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search A2A messages in ChromaDB"""
        try:
            collection = self.collections["a2a_messages"]
            
            where_filter = {}
            if session_id:
                where_filter["session_id"] = session_id
            
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter if where_filter else None
            )
            
            return [
                {
                    "message_id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                }
                for i in range(len(results["ids"][0]))
            ]
            
        except Exception as e:
            logger.error(f"Error searching A2A messages: {e}")
            return []

    async def clear_session_data(self, session_id: str):
        """Clear all session data from Redis and ChromaDB"""
        try:
            # Clear Redis data
            keys_to_delete = [
                f"session:{session_id}",
                f"debate_messages:{session_id}",
                f"a2a_messages:{session_id}",
                f"adk_orchestrator:{session_id}:*",
                f"adk_agent_context:{session_id}:*",
                f"agent_memory:{session_id}:*"
            ]
            
            for key_pattern in keys_to_delete:
                if "*" in key_pattern:
                    # Handle wildcard patterns
                    keys = await self.redis_client.keys(key_pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                else:
                    await self.redis_client.delete(key_pattern)
            
            logger.info(f"Cleared session data for {session_id}")
            
        except Exception as e:
            logger.error(f"Error clearing session data: {e}")
            raise

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session statistics including ADK metrics"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return {}
            
            messages = await self.get_session_messages(session_id)
            a2a_messages = await self.get_a2a_messages(session_id)
            
            stats = {
                "session_id": session_id,
                "status": session.status,
                "current_round": session.current_round,
                "total_messages": len(messages),
                "total_a2a_messages": len(a2a_messages),
                "agents_count": len(session.agents),
                "consensus_reached": session.consensus_reached,
                "has_adk_orchestrator": bool(session.orchestrator_id),
                "session_duration": (datetime.utcnow() - session.created_at).total_seconds(),
                "adk_session_config": session.adk_session_config
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {} 