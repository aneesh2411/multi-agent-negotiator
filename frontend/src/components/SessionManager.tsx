import React, { useState, useEffect } from 'react'
import { Folder, Calendar, Users, Clock, Play, Trash2, MoreVertical } from 'lucide-react'

interface Session {
  session_id: string
  scenario: string
  status: string
  current_round: number
  consensus_reached: boolean
  agents: any[]
  created_at: string
}

interface SessionManagerProps {
  onSelectSession: (sessionId: string) => void
}

const SessionManager: React.FC<SessionManagerProps> = ({ onSelectSession }) => {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSessions()
  }, [])

  const fetchSessions = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/v1/sessions')
      if (response.ok) {
        const data = await response.json()
        setSessions(data)
      } else {
        console.error('Failed to fetch sessions:', response.statusText)
        // Fallback to empty array if API fails
        setSessions([])
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
      // Fallback to empty array if API fails
      setSessions([])
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700'
      case 'debating':
        return 'bg-blue-100 text-blue-700'
      case 'paused':
        return 'bg-yellow-100 text-yellow-700'
      case 'created':
        return 'bg-gray-100 text-gray-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading sessions...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-2">
          Session Manager
        </h2>
        <p className="text-gray-600">Manage and review your debate sessions</p>
      </div>

      {/* Sessions List */}
      <div className="space-y-4">
        {sessions.length > 0 ? (
          sessions.map((session) => (
            <div key={session.session_id} className="card hover:shadow-lg transition-all duration-300 hover:scale-[1.02] backdrop-blur-sm">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                      <Folder className="h-5 w-5 text-primary-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 text-lg">{session.scenario}</h3>
                      <div className="flex items-center space-x-4 mt-1">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(session.status)}`}>
                          {session.status}
                        </span>
                        {session.consensus_reached && (
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                            Consensus Reached
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                    <div className="flex items-center space-x-2">
                      <Users className="h-4 w-4" />
                      <span>{session.agents.length} agents</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4" />
                      <span>Round {session.current_round}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-4 w-4" />
                      <span>{formatDate(session.created_at)}</span>
                    </div>
                  </div>

                  {/* Agents Preview */}
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Participating Agents:</p>
                    <div className="flex flex-wrap gap-2">
                      {session.agents.map((agent, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                        >
                          {agent.name}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => onSelectSession(session.session_id)}
                    className="btn-primary flex items-center space-x-1 text-sm py-2 px-3"
                  >
                    <Play className="h-3 w-3" />
                    <span>View</span>
                  </button>
                  
                  <button className="btn-secondary p-2">
                    <MoreVertical className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <Folder className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-gray-900 mb-2">No Sessions Yet</h3>
            <p className="text-gray-600 mb-4">Create your first debate session in the Agent Studio</p>
          </div>
        )}
      </div>

      {/* Session Statistics */}
      {sessions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <div className="text-2xl font-bold text-primary-600 mb-1">
              {sessions.length}
            </div>
            <div className="text-sm text-gray-600">Total Sessions</div>
          </div>
          
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {sessions.filter(s => s.consensus_reached).length}
            </div>
            <div className="text-sm text-gray-600">Consensus Reached</div>
          </div>
          
          <div className="card text-center">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {sessions.filter(s => s.status === 'debating').length}
            </div>
            <div className="text-sm text-gray-600">Active Debates</div>
          </div>
          
          <div className="card text-center">
            <div className="text-2xl font-bold text-gray-600 mb-1">
              {Math.round(sessions.reduce((acc, s) => acc + s.current_round, 0) / sessions.length || 0)}
            </div>
            <div className="text-sm text-gray-600">Avg. Rounds</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SessionManager 