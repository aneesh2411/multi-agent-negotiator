# 🧠 Dynamic Multi-Agent Negotiation Framework

A sophisticated system for creating autonomous, multi-agent debates around user-defined scenarios with real-time visualization and user intervention capabilities.

## 🎯 Project Overview

This system enables **autonomous, multi-agent debates** where agents communicate, debate, negotiate trade-offs, and reason iteratively to reach consensus. Users can view debates live, intervene at system level, and control agent participation.

### Key Features

- **Dynamic Role Assignment**: Auto-generates N agents with relevant goals and personalities
- **Multi-Agent Debate Engine**: Agents communicate using Google A2A protocol
- **Memory & Context Awareness**: Hierarchical memory system with Redis and ChromaDB
- **Consensus Building**: Advanced voting mechanisms (Borda Count, Delphi Method)
- **Real-Time UI**: Live debate visualization with agent interaction graphs
- **User Intervention System**: Control agent entry, pause/resume debates, manual consensus triggers

## 🏗 Architecture

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend API | Python + FastAPI | MCP Orchestration Server |
| LLM Backend | OpenAI GPT-4 / Claude / Mixtral | Agent reasoning & generation |
| Short-Term Memory | Redis | Active debate state & agent memory |
| Session Memory | ChromaDB | Current debate history & semantic search |
| Agent Orchestration | LangGraph + Google A2A | Multi-agent coordination |
| Frontend | React.js + TailwindCSS | Real-time debate visualization |
| Real-Time Communication | Socket.IO | Live debate streaming |
| Visualization | D3.js / React Flow | Agent interaction graphs |

### System Flow

1. **User Input** → Scenario definition
2. **Agent Preview** → User approval system
3. **Role Generation** → Dynamic agent creation
4. **Memory Management** → Redis/ChromaDB integration
5. **Debate Engine** → Google A2A protocol communication
6. **Consensus Evaluation** → Advanced voting mechanisms
7. **Real-Time UI** → Live visualization and intervention

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Redis
- ChromaDB
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/multi-agent-negotiator.git
cd multi-agent-negotiator

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### Environment Setup

Create `.env` files in both `backend/` and `frontend/` directories:

```bash
# Backend .env
OPENAI_API_KEY=your_openai_api_key
REDIS_URL=redis://localhost:6379
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

### Running the Application

```bash
# Start backend
cd backend
uvicorn main:app --reload

# Start frontend (in new terminal)
cd frontend
npm start
```

## 📊 Development Progress

See [PROGRESS_TRACKER.md](./PROGRESS_TRACKER.md) for detailed progress tracking and completed tasks.

## 🗓 Development Phases

### Phase 1 (MVP) - Weeks 1-4
- [ ] FastAPI backend with WebSocket support
- [ ] Google A2A protocol integration
- [ ] Basic agent generation (3-5 agents)
- [ ] Redis for active debate state
- [ ] Simple consensus mechanism
- [ ] React UI with agent preview
- [ ] Real-time debate viewer
- [ ] Basic agent interaction graphs

### Phase 2 (Advanced) - Weeks 5-8
- [ ] Dynamic agent generation
- [ ] Advanced consensus mechanisms
- [ ] Conflict resolution agents
- [ ] ChromaDB for semantic memory
- [ ] Sophisticated visualizations
- [ ] Debate analytics dashboard
- [ ] Advanced user intervention tools

### Phase 3 (Production) - Weeks 9-12
- [ ] Multiple concurrent sessions
- [ ] Performance optimization
- [ ] Production deployment
- [ ] Advanced memory management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions, please open an issue in the GitHub repository.

---

**Built with ❤️ for advancing multi-agent systems and AI negotiation frameworks** 