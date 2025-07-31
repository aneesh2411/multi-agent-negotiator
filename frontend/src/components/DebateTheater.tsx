import React, { useState, useEffect, useRef } from 'react'
import { MessageSquare, Users, Clock, Activity, Play, Pause, RotateCcw } from 'lucide-react'

interface DebateMessage {
  id: string
  agent_name: string
  content: string
  timestamp: string
  round_number: number
  agent_id: string
}

interface DebateSession {
  session_id: string
  scenario: string
  status: string
  current_round: number
  consensus_reached: boolean
  agents: any[]
}

interface DebateTheaterProps {
  sessionId: string | null
}

const DebateTheater: React.FC<DebateTheaterProps> = ({ sessionId }) => {
  const [session, setSession] = useState<DebateSession | null>(null)
  const [messages, setMessages] = useState<DebateMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    console.log('DebateTheater: sessionId changed to:', sessionId)
    if (sessionId) {
      console.log('DebateTheater: Fetching session details for:', sessionId)
      fetchSessionDetails()
      initializeWebSocket()
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.close()
      }
    }
  }, [sessionId])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const initializeWebSocket = () => {
    if (!sessionId) return

    // Connect to backend WebSocket
    const wsUrl = `ws://localhost:8000/ws/${sessionId}`
    socketRef.current = new WebSocket(wsUrl)

    socketRef.current.onopen = () => {
      setIsConnected(true)
      console.log('Connected to WebSocket')
    }

    socketRef.current.onclose = () => {
      setIsConnected(false)
      console.log('Disconnected from WebSocket')
    }

    socketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'debate_message':
            setMessages(prev => [...prev, data.message])
            break
          case 'session_update':
            setSession(prev => prev ? { ...prev, ...data } : null)
            break
          case 'consensus_reached':
            setSession(prev => prev ? { ...prev, consensus_reached: true } : null)
            break
          case 'round_update':
            setSession(prev => prev ? { ...prev, current_round: data.round_number } : null)
            break
          case 'agent_typing':
            console.log(`${data.agent_name} is typing...`)
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

  const fetchSessionDetails = async () => {
    if (!sessionId) return
    
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:8000/api/v1/sessions/${sessionId}`)
      const data = await response.json()
      setSession(data)
      
      // Also fetch existing messages
      const messagesResponse = await fetch(`http://localhost:8000/api/v1/sessions/${sessionId}/messages`)
      const messagesData = await messagesResponse.json()
      setMessages(messagesData)
    } catch (error) {
      console.error('Failed to fetch session details:', error)
    } finally {
      setLoading(false)
    }
  }

  const startDebate = async () => {
    if (!sessionId || !socketRef.current) return
    
    try {
      await fetch(`http://localhost:8000/api/v1/sessions/${sessionId}/start-debate`, {
        method: 'POST'
      })
      
      // WebSocket will receive updates automatically from backend
      
      fetchSessionDetails()
    } catch (error) {
      console.error('Failed to start debate:', error)
    }
  }

  const pauseDebate = async () => {
    if (!sessionId || !socketRef.current) return
    
    try {
      await fetch(`http://localhost:8000/api/v1/sessions/${sessionId}/pause-debate`, {
        method: 'POST'
      })
      
      // WebSocket will receive updates automatically from backend
      fetchSessionDetails()
    } catch (error) {
      console.error('Failed to pause debate:', error)
    }
  }

  const resumeDebate = async () => {
    if (!sessionId || !socketRef.current) return
    
    try {
      await fetch(`http://localhost:8000/api/v1/sessions/${sessionId}/resume-debate`, {
        method: 'POST'
      })
      
      // WebSocket will receive updates automatically from backend
      fetchSessionDetails()
    } catch (error) {
      console.error('Failed to resume debate:', error)
    }
  }

  if (!sessionId) {
    return (
      <div className="text-center py-12">
        <MessageSquare className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-medium text-gray-900 mb-2">No Active Debate</h3>
        <p className="text-gray-600">Create agents in the Agent Studio to start a debate</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading debate session...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-2">
          Debate Theater
        </h2>
        <p className="text-gray-600">Watch AI agents engage in real-time intelligent debates</p>
      </div>

      {session && (
        <>
          {/* Session Overview */}
          <div className="card">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{session.scenario}</h3>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <Users className="h-4 w-4" />
                    <span>{session.agents.length} agents</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-4 w-4" />
                    <span>Round {session.current_round}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Activity className="h-4 w-4" />
                    <span className={`capitalize ${
                      session.status === 'debating' ? 'text-green-600' : 
                      session.status === 'paused' ? 'text-yellow-600' : 
                      'text-gray-600'
                    }`}>
                      {session.status}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className={`text-xs ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                      {isConnected ? 'Live' : 'Disconnected'}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                {session.status === 'created' && (
                  <button onClick={startDebate} className="btn-primary flex items-center space-x-2">
                    <Play className="h-4 w-4" />
                    <span>Start Debate</span>
                  </button>
                )}
                {session.status === 'debating' && (
                  <button onClick={pauseDebate} className="btn-secondary flex items-center space-x-2">
                    <Pause className="h-4 w-4" />
                    <span>Pause</span>
                  </button>
                )}
                {session.status === 'paused' && (
                  <button onClick={resumeDebate} className="btn-primary flex items-center space-x-2">
                    <Play className="h-4 w-4" />
                    <span>Resume</span>
                  </button>
                )}
              </div>
            </div>

            {/* Consensus Status */}
            {session.consensus_reached && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="font-medium text-green-800">Consensus Reached!</span>
                </div>
                <p className="text-green-700 mt-1">The agents have found common ground on this topic.</p>
              </div>
            )}
          </div>

          {/* Agents Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {session.agents.map((agent, index) => (
              <div key={agent.id} className="card hover:shadow-md transition-shadow">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-primary-700 font-medium">{index + 1}</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">{agent.name}</h4>
                    <p className="text-sm text-gray-600">{agent.role}</p>
                  </div>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Current Stance:</span>
                    <p className="text-gray-600 mt-1">{agent.initial_stance}</p>
                  </div>
                  
                  {agent.llm_provider && (
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-700">Powered by:</span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                        {agent.llm_provider}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Debate Messages */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <MessageSquare className="h-5 w-5 text-primary-600 mr-2" />
              Debate Messages
            </h3>
            
            {messages.length > 0 ? (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {messages.map((message) => (
                  <div key={message.id} className="border-l-2 border-primary-200 pl-4 py-2 animate-fade-in">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">{message.agent_name}</span>
                        <span className="text-xs text-gray-500">Round {message.round_number}</span>
                      </div>
                      <span className="text-xs text-gray-500">{new Date(message.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-gray-700">{message.content}</p>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            ) : (
              <div className="text-center py-8">
                <MessageSquare className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">No messages yet. Start the debate to see agent discussions.</p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default DebateTheater 