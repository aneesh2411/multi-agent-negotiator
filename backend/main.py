"""
Main FastAPI application for the Multi-Agent Negotiation Framework with ADK integration
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from loguru import logger
import asyncio
from typing import List, Dict, Any
import json

# Import our modules
from models.debate import DebateSession, Agent, DebateMessage
from services.agent_service import AgentService
from services.debate_service import DebateService
from services.memory_service import MemoryService
from utils.config import get_settings

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Negotiation Framework (ADK-powered)",
    description="A sophisticated system for creating autonomous, multi-agent debates using Google ADK",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for WebSocket connections and ADK orchestrators
active_connections: List[WebSocket] = []
debate_sessions: Dict[str, DebateSession] = {}
debate_services: Dict[str, DebateService] = {}  # Track ADK orchestrators per session

# Initialize services
settings = get_settings()
agent_service = AgentService()
memory_service = MemoryService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Multi-Agent Negotiation Framework with ADK")
    await memory_service.initialize()
    # TODO: Initialize any global ADK resources if needed

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Multi-Agent Negotiation Framework")
    # Cleanup all active ADK orchestrators
    for session_id, debate_service in debate_services.items():
        if debate_service.orchestrator:
            logger.info(f"Shutting down ADK orchestrator for session {session_id}")
            # TODO: Add proper ADK orchestrator cleanup
    await memory_service.cleanup()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent Negotiation Framework API (ADK-powered)",
        "version": "1.0.0",
        "status": "running",
        "adk_enabled": True
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "redis": await memory_service.check_redis_connection(),
            "chromadb": await memory_service.check_chromadb_connection(),
            "adk": True  # TODO: Add actual ADK health check
        }
    }

@app.post("/api/v1/sessions/start")
async def start_debate_session(scenario: str, agent_count: int = 5):
    """Start a new debate session with ADK orchestrator"""
    try:
        # Generate agents for the scenario
        agents = await agent_service.generate_agents(scenario, agent_count)
        
        # Create debate service with ADK orchestrator
        debate_service = DebateService()
        session_id = await debate_service.create_session(scenario, agents)
        
        # Store session and debate service
        debate_sessions[session_id] = DebateSession(
            id=session_id,
            scenario=scenario,
            agents=agents,
            status="created"
        )
        debate_services[session_id] = debate_service
        
        logger.info(f"Created ADK debate session: {session_id}")
        
        return {
            "session_id": session_id,
            "agents": [agent.dict() for agent in agents],
            "status": "created",
            "adk_orchestrator": "initialized"
        }
    
    except Exception as e:
        logger.error(f"Error starting ADK debate session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sessions/{session_id}")
async def get_session_status(session_id: str):
    """Get the status of a debate session"""
    if session_id not in debate_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = debate_sessions[session_id]
    debate_service = debate_services.get(session_id)
    
    return {
        "session_id": session_id,
        "scenario": session.scenario,
        "agents": [agent.dict() for agent in session.agents],
        "status": session.status,
        "current_round": session.current_round,
        "consensus_reached": session.consensus_reached,
        "adk_orchestrator": "active" if debate_service and debate_service.orchestrator else "inactive"
    }

@app.post("/api/v1/sessions/{session_id}/start-debate")
async def start_debate(session_id: str):
    """Start the actual ADK debate for a session"""
    if session_id not in debate_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_id not in debate_services:
        raise HTTPException(status_code=404, detail="ADK debate service not found")
    
    try:
        session = debate_sessions[session_id]
        debate_service = debate_services[session_id]
        session.status = "debating"
        
        # Start the ADK debate engine
        await debate_service.start_debate(session_id, session)
        
        return {
            "message": "ADK debate started", 
            "session_id": session_id,
            "orchestrator_status": "active"
        }
    
    except Exception as e:
        logger.error(f"Error starting ADK debate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/sessions/{session_id}/pause")
async def pause_debate(session_id: str):
    """Pause the debate"""
    if session_id not in debate_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = debate_sessions[session_id]
    session.status = "paused"
    
    # TODO: Add ADK orchestrator pause functionality
    
    return {"message": "Debate paused", "session_id": session_id}

@app.post("/api/v1/sessions/{session_id}/resume")
async def resume_debate(session_id: str):
    """Resume the debate"""
    if session_id not in debate_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = debate_sessions[session_id]
    session.status = "debating"
    
    # TODO: Add ADK orchestrator resume functionality
    
    return {"message": "Debate resumed", "session_id": session_id}

@app.post("/api/v1/sessions/{session_id}/consensus")
async def trigger_consensus(session_id: str):
    """Manually trigger consensus evaluation"""
    if session_id not in debate_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_id not in debate_services:
        raise HTTPException(status_code=404, detail="ADK debate service not found")
    
    try:
        debate_service = debate_services[session_id]
        result = await debate_service.evaluate_consensus(session_id)
        return {
            "message": "Consensus evaluation triggered",
            "consensus_reached": result.get("consensus_reached", False),
            "consensus_details": result
        }
    
    except Exception as e:
        logger.error(f"Error evaluating consensus: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time debate updates with ADK events"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send real-time updates to connected clients
            if session_id in debate_sessions:
                session = debate_sessions[session_id]
                debate_service = debate_services.get(session_id)
                
                await websocket.send_text(json.dumps({
                    "type": "session_update",
                    "session_id": session_id,
                    "status": session.status,
                    "current_round": session.current_round,
                    "consensus_reached": session.consensus_reached,
                    "adk_orchestrator": "active" if debate_service and debate_service.orchestrator else "inactive"
                    # TODO: Add ADK-specific events (agent actions, A2A messages, etc.)
                }))
            
            # Wait before next update
            await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_message(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    if active_connections:
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove broken connections
                active_connections.remove(connection)

# TODO: Add endpoints for ADK-specific functionality:
# - Agent introspection
# - A2A message history
# - Orchestrator status and controls
# - Real-time agent state monitoring

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 