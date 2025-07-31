#!/usr/bin/env python3
"""
Comprehensive connection test for Multi-Agent Negotiator Platform
Tests all API endpoints, database connections, and services
"""

import asyncio
import json
import aiohttp
import sys
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

class ConnectionTester:
    def __init__(self):
        self.results = []
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_test(self, test_name: str, success: bool, details: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({"name": test_name, "success": success, "details": details})
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")

    async def test_backend_health(self):
        """Test if backend server is running"""
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Backend Health Check", True, f"Status: {data.get('status', 'unknown')}")
                else:
                    self.log_test("Backend Health Check", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Connection failed: {e}")

    async def test_frontend_availability(self):
        """Test if frontend server is running"""
        try:
            async with self.session.get(FRONTEND_URL) as response:
                if response.status == 200:
                    self.log_test("Frontend Availability", True, "Frontend server responding")
                else:
                    self.log_test("Frontend Availability", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Frontend Availability", False, f"Connection failed: {e}")

    async def test_create_session(self):
        """Test creating a new debate session"""
        try:
            data = {
                "scenario": "Should AI be regulated?",
                "agent_count": 3
            }
            async with self.session.post(f"{BASE_URL}/api/v1/sessions/start", json=data) as response:
                if response.status == 200:
                    session_data = await response.json()
                    session_id = session_data.get("session_id")
                    if session_id:
                        self.log_test("Create Session", True, f"Session ID: {session_id}")
                        return session_id
                    else:
                        self.log_test("Create Session", False, "No session ID returned")
                else:
                    self.log_test("Create Session", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Create Session", False, f"Request failed: {e}")
        return None

    async def test_get_sessions(self):
        """Test getting all sessions"""
        try:
            async with self.session.get(f"{BASE_URL}/api/v1/sessions") as response:
                if response.status == 200:
                    sessions = await response.json()
                    self.log_test("Get Sessions", True, f"Found {len(sessions)} sessions")
                else:
                    self.log_test("Get Sessions", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Get Sessions", False, f"Request failed: {e}")

    async def test_session_details(self, session_id: str):
        """Test getting session details"""
        if not session_id:
            self.log_test("Session Details", False, "No session ID provided")
            return
        
        try:
            async with self.session.get(f"{BASE_URL}/api/v1/sessions/{session_id}") as response:
                if response.status == 200:
                    session_data = await response.json()
                    self.log_test("Session Details", True, f"Status: {session_data.get('status', 'unknown')}")
                else:
                    self.log_test("Session Details", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Session Details", False, f"Request failed: {e}")

    async def test_session_messages(self, session_id: str):
        """Test getting session messages"""
        if not session_id:
            self.log_test("Session Messages", False, "No session ID provided")
            return
        
        try:
            async with self.session.get(f"{BASE_URL}/api/v1/sessions/{session_id}/messages") as response:
                if response.status == 200:
                    messages = await response.json()
                    self.log_test("Session Messages", True, f"Found {len(messages)} messages")
                else:
                    self.log_test("Session Messages", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Session Messages", False, f"Request failed: {e}")

    async def test_start_debate(self, session_id: str):
        """Test starting a debate"""
        if not session_id:
            self.log_test("Start Debate", False, "No session ID provided")
            return
        
        try:
            async with self.session.post(f"{BASE_URL}/api/v1/sessions/{session_id}/start-debate") as response:
                if response.status == 200:
                    result = await response.json()
                    self.log_test("Start Debate", True, f"Message: {result.get('message', 'Success')}")
                else:
                    self.log_test("Start Debate", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Start Debate", False, f"Request failed: {e}")

    async def run_all_tests(self):
        """Run all connection tests"""
        print("🧪 Running Comprehensive Connection Tests...")
        print("=" * 50)
        
        # Basic connectivity tests
        await self.test_backend_health()
        await self.test_frontend_availability()
        
        # API functionality tests
        session_id = await self.test_create_session()
        await self.test_get_sessions()
        await self.test_session_details(session_id)
        await self.test_session_messages(session_id)
        await self.test_start_debate(session_id)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        
        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['name']}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! Your platform is ready to use.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return passed == total

async def main():
    """Main test runner"""
    try:
        async with ConnectionTester() as tester:
            success = await tester.run_all_tests()
            sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 