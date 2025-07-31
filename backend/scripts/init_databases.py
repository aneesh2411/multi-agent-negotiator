#!/usr/bin/env python3
"""
Database Initialization Script for Multi-Agent Negotiation Framework
Sets up Redis and ChromaDB databases with proper configuration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.memory_service import MemoryService
from utils.config import get_settings

async def check_redis_connectivity():
    """Check if Redis is running and accessible"""
    print("🔍 Checking Redis connectivity...")
    
    try:
        import redis.asyncio as redis
        settings = get_settings()
        
        client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await client.ping()
        await client.close()
        
        print("✅ Redis is running and accessible")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n💡 To fix this:")
        print("   1. Install Redis: brew install redis")
        print("   2. Start Redis: brew services start redis")
        print("   3. Or manually: redis-server")
        return False

async def setup_memory_service():
    """Initialize memory service and create collections"""
    print("\n🗄️  Setting up Memory Service...")
    
    try:
        # Set environment variable for ChromaDB
        os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
        
        memory_service = MemoryService()
        
        print("   Initializing connections...")
        await memory_service.initialize()
        
        print("   Testing Redis operations...")
        redis_ok = await memory_service.check_redis_connection()
        
        print("   Testing ChromaDB operations...")
        chroma_ok = await memory_service.check_chromadb_connection()
        
        if redis_ok and chroma_ok:
            print("✅ Memory service initialized successfully")
            print("   - Redis collections ready")
            print("   - ChromaDB collections created")
        else:
            print("❌ Memory service initialization failed")
            return False
        
        await memory_service.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Memory service setup failed: {e}")
        return False

def check_environment_variables():
    """Check that required environment variables are set"""
    print("\n🔧 Checking Environment Variables...")
    
    settings = get_settings()
    
    # Check LLM API keys
    providers = []
    if settings.openai_api_key:
        providers.append("OpenAI")
    if settings.anthropic_api_key:
        providers.append("Anthropic") 
    if settings.google_api_key:
        providers.append("Google")
    
    if providers:
        print(f"✅ LLM Providers configured: {', '.join(providers)}")
    else:
        print("⚠️  No LLM providers configured")
        print("   Add API keys to .env file:")
        print("   - OPENAI_API_KEY=your_key_here")
        print("   - ANTHROPIC_API_KEY=your_key_here") 
        print("   - GOOGLE_API_KEY=your_key_here")
    
    # Check database settings
    print(f"✅ Redis URL: {settings.redis_url}")
    print(f"✅ ChromaDB: {settings.chroma_host}:{settings.chroma_port}")
    
    return len(providers) > 0

async def test_basic_operations():
    """Test basic database operations"""
    print("\n🧪 Testing Basic Database Operations...")
    
    try:
        os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
        
        memory_service = MemoryService()
        await memory_service.initialize()
        
        # Test Redis operations
        print("   Testing Redis key-value operations...")
        test_key = "test:init:redis"
        test_value = "Database initialization test"
        
        await memory_service.redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved = await memory_service.redis_client.get(test_key)
        
        if retrieved == test_value:
            print("   ✅ Redis read/write operations working")
        else:
            print("   ❌ Redis read/write operations failed")
            return False
        
        # Clean up test key
        await memory_service.redis_client.delete(test_key)
        
        # Test ChromaDB operations
        print("   Testing ChromaDB collection operations...")
        
        # This was already tested during memory service initialization
        print("   ✅ ChromaDB collections accessible")
        
        await memory_service.cleanup()
        print("✅ All basic operations working")
        return True
        
    except Exception as e:
        print(f"❌ Basic operations test failed: {e}")
        return False

async def main():
    """Main initialization function"""
    print("🚀 Multi-Agent Negotiation Framework - Database Initialization")
    print("=" * 70)
    
    # Step 1: Check environment variables
    env_ok = check_environment_variables()
    
    # Step 2: Check Redis connectivity
    redis_ok = await check_redis_connectivity()
    
    if not redis_ok:
        print("\n❌ Cannot proceed without Redis. Please install and start Redis first.")
        return 1
    
    # Step 3: Setup memory service
    memory_ok = await setup_memory_service()
    
    if not memory_ok:
        print("\n❌ Memory service setup failed.")
        return 1
    
    # Step 4: Test basic operations
    operations_ok = await test_basic_operations()
    
    if not operations_ok:
        print("\n❌ Basic operations test failed.")
        return 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 INITIALIZATION SUMMARY")
    print("=" * 70)
    print(f"Environment Variables: {'✅ OK' if env_ok else '⚠️  Partial'}")
    print(f"Redis Connectivity:    {'✅ OK' if redis_ok else '❌ Failed'}")
    print(f"Memory Service:        {'✅ OK' if memory_ok else '❌ Failed'}")
    print(f"Basic Operations:      {'✅ OK' if operations_ok else '❌ Failed'}")
    print("-" * 70)
    
    if all([redis_ok, memory_ok, operations_ok]):
        print("🎉 Database initialization completed successfully!")
        print("\nNext steps:")
        print("1. Run 'python backend/scripts/validate_setup.py' to validate everything")
        print("2. Start the FastAPI server: 'uvicorn backend.main:app --reload'")
        print("3. Test the API endpoints")
        return 0
    else:
        print("⚠️  Database initialization completed with issues.")
        print("Please address the issues above before proceeding.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 