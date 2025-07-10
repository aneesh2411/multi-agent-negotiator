"""
Memory service for managing Redis and ChromaDB connections and operations
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
from models.debate import DebateSession, AgentMemory, DebateContext, DebateMessage

class MemoryService:
    """Service for managing memory operations with Redis and ChromaDB"""
    
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
            self.chroma_client = chromadb.Client(ChromaSettings(
                chroma_api_impl="rest",
                chroma_server_host=self.settings.chroma_host,
                chroma_server_http_port=self.settings.chroma_port
            ))
            
            # Create collections
            await self._create_collections()
            logger.info("ChromaDB connection established")
            
        except Exception as e:
            logger.error(f"Error initializing memory service: {e}")
            raise
    
    async def _create_collections(self):
        """Create ChromaDB collections for different data types"""
        try:
            # Debate sessions collection
            self.collections["debate_sessions"] = self.chroma_client.get_or_create_collection(
                name="debate_sessions",
                metadata={"description": "Debate session data"}
            )
            
            # Agent memories collection
            self.collections["agent_memories"] = self.chroma_client.get_or_create_collection(
                name="agent_memories",
                metadata={"description": "Agent memory and context data"}
            )
            
            # Debate messages collection
            self.collections["debate_messages"] = self.chroma_client.get_or_create_collection(
                name="debate_messages",
                metadata={"description": "Debate message history"}
            )
            
            logger.info("ChromaDB collections created successfully")
            
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
    
    # Redis Operations for Active Debate State
    
    async def store_session(self, session: DebateSession):
        """Store debate session in Redis"""
        try:
            key = f"session:{session.id}"
            data = session.dict()
            await self.redis_client.setex(
                key,
                self.settings.memory_ttl_seconds,
                json.dumps(data, default=str)
            )
            logger.info(f"Stored session {session.id} in Redis")
        except Exception as e:
            logger.error(f"Error storing session: {e}")
            raise
    
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
        """Store agent memory in Redis"""
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
    
    # ChromaDB Operations for Session History
    
    async def store_session_history(self, session: DebateSession):
        """Store session history in ChromaDB"""
        try:
            collection = self.collections["debate_sessions"]
            
            # Store session metadata
            collection.add(
                documents=[json.dumps(session.dict(), default=str)],
                metadatas=[{
                    "session_id": session.id,
                    "scenario": session.scenario,
                    "status": session.status,
                    "created_at": str(session.created_at),
                    "consensus_reached": str(session.consensus_reached)
                }],
                ids=[session.id]
            )
            logger.info(f"Stored session history {session.id} in ChromaDB")
        except Exception as e:
            logger.error(f"Error storing session history: {e}")
            raise
    
    async def store_agent_memory_history(self, memory: AgentMemory):
        """Store agent memory history in ChromaDB"""
        try:
            collection = self.collections["agent_memories"]
            
            # Store memory data
            collection.add(
                documents=[json.dumps(memory.dict(), default=str)],
                metadatas=[{
                    "agent_id": memory.agent_id,
                    "session_id": memory.session_id,
                    "last_updated": str(memory.last_updated)
                }],
                ids=[f"{memory.session_id}:{memory.agent_id}"]
            )
        except Exception as e:
            logger.error(f"Error storing agent memory history: {e}")
            raise
    
    async def store_debate_message_history(self, message: DebateMessage):
        """Store debate message history in ChromaDB"""
        try:
            collection = self.collections["debate_messages"]
            
            # Store message data
            collection.add(
                documents=[message.content],
                metadatas=[{
                    "message_id": message.id,
                    "session_id": message.session_id,
                    "agent_id": message.agent_id,
                    "agent_name": message.agent_name,
                    "message_type": message.message_type,
                    "round_number": str(message.round_number),
                    "timestamp": str(message.timestamp)
                }],
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
            return results
        except Exception as e:
            logger.error(f"Error searching session history: {e}")
            return []
    
    async def search_agent_memories(self, query: str, session_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search agent memories in ChromaDB"""
        try:
            collection = self.collections["agent_memories"]
            
            # Build query filter
            where_filter = {}
            if session_id:
                where_filter["session_id"] = session_id
            
            results = collection.query(
                query_texts=[query],
                where=where_filter if where_filter else None,
                n_results=limit
            )
            return results
        except Exception as e:
            logger.error(f"Error searching agent memories: {e}")
            return []
    
    # Utility Methods
    
    async def clear_session_data(self, session_id: str):
        """Clear all data for a session"""
        try:
            # Clear Redis data
            session_key = f"session:{session_id}"
            messages_key = f"debate_messages:{session_id}"
            memory_pattern = f"agent_memory:{session_id}:*"
            
            await self.redis_client.delete(session_key, messages_key)
            
            # Clear agent memories
            memory_keys = await self.redis_client.keys(memory_pattern)
            if memory_keys:
                await self.redis_client.delete(*memory_keys)
            
            logger.info(f"Cleared session data for {session_id}")
        except Exception as e:
            logger.error(f"Error clearing session data: {e}")
            raise
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        try:
            session = await self.get_session(session_id)
            messages = await self.get_session_messages(session_id)
            
            return {
                "session_id": session_id,
                "status": session.status if session else "unknown",
                "message_count": len(messages),
                "round_count": session.current_round if session else 0,
                "consensus_reached": session.consensus_reached if session else False,
                "created_at": session.created_at if session else None
            }
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {} 