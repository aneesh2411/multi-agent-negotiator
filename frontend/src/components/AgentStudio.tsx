import React, { useState, useEffect, useRef } from 'react'
import { Sparkles, Play, RefreshCw, Users, Brain, MessageSquare } from 'lucide-react'

interface Agent {
  id: string
  name: string
  role: string
  personality: string
  goals: string[]
  constraints: string[]
  expertise: string[]
  initial_stance: string
  reasoning_style: string
  communication_style: string
  llm_provider?: string
}

interface AgentStudioProps {
  onStartDebate: (sessionId: string) => void
}

const AgentStudio: React.FC<AgentStudioProps> = ({ onStartDebate }) => {
  const [scenario, setScenario] = useState('')
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(false)
  const [agentCount, setAgentCount] = useState(5)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    initializeWebSocket()
    
    return () => {
      if (socketRef.current) {
        socketRef.current.close()
      }
    }
  }, [])

  const initializeWebSocket = () => {
    // For AgentStudio, we'll connect to a general WebSocket for now
    // In a real implementation, this could be session-specific
    const wsUrl = `ws://localhost:8000/ws/agent-studio`
    socketRef.current = new WebSocket(wsUrl)

    socketRef.current.onopen = () => {
      setIsConnected(true)
      console.log('AgentStudio connected to WebSocket')
    }

    socketRef.current.onclose = () => {
      setIsConnected(false)
      console.log('AgentStudio disconnected from WebSocket')
    }

    socketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'agent_generation_progress':
            setGenerationProgress(data.progress)
            break
          case 'agents_generated':
            setAgents(data.agents)
            setCurrentSessionId(data.session_id)
            setGenerationProgress(0)
            setLoading(false)
            break
          case 'agent_generation_error':
            console.error('Agent generation error:', data.error)
            setLoading(false)
            setGenerationProgress(0)
            break
          default:
            console.log('Unknown message type:', data.type)
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    socketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }
  }

  const generateAgents = async () => {
    if (!scenario.trim()) return
    
    setLoading(true)
    setGenerationProgress(0)
    setAgents([])
    
    try {
      const params = new URLSearchParams({
        scenario: scenario,
        agent_count: agentCount.toString()
      })
      
      const response = await fetch(`http://localhost:8000/api/v1/sessions/start?${params}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      const data = await response.json()
      
      if (data.session_id) {
        setCurrentSessionId(data.session_id)
        
        // If agents are immediately available, use them
        if (data.agents && data.agents.length > 0) {
          setAgents(data.agents)
          setLoading(false)
          setGenerationProgress(100)
        }
        // Otherwise, WebSocket will receive updates automatically from backend
      } else {
        setAgents(data.agents || [])
        setLoading(false)
      }
    } catch (error) {
      console.error('Failed to generate agents:', error)
      setLoading(false)
    }
  }

  const startDebate = async () => {
    console.log('Start Debate button clicked!')
    
    if (agents.length === 0 || !currentSessionId) {
      console.error('Cannot start debate: missing agents or session ID', { agents: agents.length, currentSessionId })
      alert(`Cannot start debate: agents=${agents.length}, sessionId=${currentSessionId}`)
      return
    }
    
    console.log('Starting debate for session:', currentSessionId)
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/sessions/${currentSessionId}/start-debate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      const data = await response.json()
      console.log('Start debate response:', data)
      
      if (data.session_id || currentSessionId) {
        console.log('Calling onStartDebate with sessionId:', currentSessionId)
        onStartDebate(currentSessionId)
      }
    } catch (error) {
      console.error('Failed to start debate:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-2">
          Agent Studio
        </h2>
        <p className="text-gray-600">Create AI agents and preview their personalities before starting a debate</p>
      </div>

      {/* Scenario Input */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Sparkles className="h-5 w-5 text-primary-600 mr-2" />
          Debate Scenario
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="label">What should the agents debate about?</label>
            <textarea
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              placeholder="e.g., Should our company implement a 4-day work week?"
              className="input h-24 resize-none"
              disabled={loading}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="label">Number of agents (3-10)</label>
              <select
                value={agentCount}
                onChange={(e) => setAgentCount(Number(e.target.value))}
                className="input w-24"
                disabled={loading}
              >
                {[3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                  <option key={num} value={num}>{num}</option>
                ))}
              </select>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={generateAgents}
                disabled={!scenario.trim() || loading}
                className="btn-primary flex items-center space-x-2"
              >
                {loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Brain className="h-4 w-4" />
                )}
                <span>{loading ? 'Generating...' : 'Generate Agents'}</span>
              </button>
              
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className={`text-xs ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Progress Bar */}
        {loading && generationProgress > 0 && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Generating agents...</span>
              <span>{Math.round(generationProgress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${generationProgress}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>

      {/* Generated Agents */}
      {agents.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Users className="h-5 w-5 text-primary-600 mr-2" />
              Generated Agents ({agents.length})
            </h3>
            
            <button
              onClick={startDebate}
              className="btn-primary flex items-center space-x-2"
            >
              <Play className="h-4 w-4" />
              <span>Start Debate</span>
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agents.map((agent, index) => (
              <div key={agent.id} className="card hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <span className="text-primary-700 font-medium text-sm">{index + 1}</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">{agent.name}</h4>
                      <p className="text-sm text-gray-600">{agent.role}</p>
                    </div>
                  </div>
                  {agent.llm_provider && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                      {agent.llm_provider}
                    </span>
                  )}
                </div>
                
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Personality:</span>
                    <p className="text-gray-600 mt-1">{agent.personality}</p>
                  </div>
                  
                  <div>
                    <span className="font-medium text-gray-700">Goals:</span>
                    <ul className="text-gray-600 mt-1 space-y-1">
                      {agent.goals.slice(0, 2).map((goal, i) => (
                        <li key={i} className="flex items-start">
                          <span className="w-1 h-1 bg-gray-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                          {goal}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <span className="font-medium text-gray-700">Communication Style:</span>
                    <p className="text-gray-600 mt-1">{agent.communication_style}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {agents.length === 0 && !loading && (
        <div className="card text-center py-12">
          <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No agents generated yet</h3>
          <p className="text-gray-600 mb-4">Enter a debate scenario above and click "Generate Agents" to get started</p>
        </div>
      )}
    </div>
  )
}

export default AgentStudio 