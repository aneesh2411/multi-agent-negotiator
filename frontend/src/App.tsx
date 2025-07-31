import React, { useState } from 'react'
import { MessageSquare, Users, Settings, Play, Pause, RotateCcw, Brain } from 'lucide-react'
import AgentStudio from './components/AgentStudio.tsx'
import DebateTheater from './components/DebateTheater.tsx'
import SessionManager from './components/SessionManager.tsx'

type ActiveView = 'studio' | 'theater' | 'sessions'

function App() {
  const [activeView, setActiveView] = useState<ActiveView>('studio')
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)

  const navigation = [
    { id: 'studio', name: 'Agent Studio', icon: Users, description: 'Create & preview AI agents' },
    { id: 'theater', name: 'Debate Theater', icon: MessageSquare, description: 'Watch live debates' },
    { id: 'sessions', name: 'Sessions', icon: Settings, description: 'Manage debate sessions' }
  ]

  const renderActiveView = () => {
    switch (activeView) {
      case 'studio':
        return <AgentStudio onStartDebate={(sessionId: string) => {
          console.log('App: onStartDebate called with sessionId:', sessionId)
          setCurrentSessionId(sessionId)
          setActiveView('theater')
          console.log('App: Switched to theater view with sessionId:', sessionId)
        }} />
      case 'theater':
        return <DebateTheater sessionId={currentSessionId} />
      case 'sessions':
        return <SessionManager onSelectSession={(sessionId) => {
          setCurrentSessionId(sessionId)
          setActiveView('theater')
        }} />
      default:
        return <AgentStudio onStartDebate={() => {}} />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-primary-600 to-primary-700 p-2 rounded-xl shadow-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Multi-Agent Negotiator
                </h1>
                <p className="text-xs text-gray-500">AI-Powered Debate Platform</p>
              </div>
            </div>
            
            {/* Status Indicator */}
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">System Online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <nav className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = activeView === item.id
                
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveView(item.id as ActiveView)}
                    className={`w-full flex items-start space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-200 group ${
                      isActive 
                        ? 'bg-gradient-to-r from-primary-50 to-primary-100/50 border-primary-200/50 text-primary-700 shadow-lg' 
                        : 'hover:bg-white/80 hover:shadow-md border-transparent text-gray-600 hover:text-gray-900 backdrop-blur-sm'
                    } border`}
                  >
                    <Icon className={`h-5 w-5 mt-0.5 transition-all group-hover:scale-110 ${
                      isActive ? 'text-primary-600' : 'text-gray-400 group-hover:text-primary-500'
                    }`} />
                    <div>
                      <div className={`font-medium ${isActive ? 'text-primary-900' : 'text-gray-700'}`}>
                        {item.name}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {item.description}
                      </div>
                    </div>
                  </button>
                )
              })}
            </nav>
            
            {/* Current Session Info */}
            {currentSessionId && (
              <div className="mt-6 p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
                <h3 className="font-medium text-gray-900 mb-2">Active Session</h3>
                <p className="text-xs text-gray-500 font-mono bg-gray-50 px-2 py-1 rounded">
                  {currentSessionId.slice(0, 8)}...
                </p>
                <div className="flex items-center mt-3 space-x-2">
                  <button className="btn-primary text-xs py-1 px-2">
                    <Play className="h-3 w-3 mr-1" />
                    Resume
                  </button>
                  <button className="btn-secondary text-xs py-1 px-2">
                    <Pause className="h-3 w-3" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="animate-fade-in">
              {renderActiveView()}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
