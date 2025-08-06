#!/usr/bin/env python3
"""
Test Pipedream Session

This script tests the Pipedream session handling in detail.
"""

import aiohttp
import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from prisma import Prisma
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def test_pipedream_session():
    """Test Pipedream session handling"""
    print("🔗 Testing Pipedream Session Handling")
    print("=" * 50)
    
    try:
        # Get MCP server from database
        prisma = Prisma()
        await prisma.connect()
        
        servers = await prisma.mcpserver.find_many()
        if not servers:
            print("❌ No MCP servers found in database")
            await prisma.disconnect()
            return
        
        server = servers[0]
        print(f"📧 Testing with server: {server.name}")
        
        # Parse config
        if isinstance(server.config, str):
            config = json.loads(server.config)
        else:
            config = server.config
        
        uri = config.get('uri', '')
        print(f"🔗 Base URI: {uri}")
        
        await prisma.disconnect()
        
        if not uri:
            print("❌ No URI found in server config")
            return
        
        # Step 1: Get the session endpoint
        print(f"\n🔍 Step 1: Getting session endpoint...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(uri) as response:
                    print(f"   Status: {response.status}")
                    print(f"   Headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        response_text = await response.text()
                        print(f"   Response: {response_text}")
                        
                        # Parse the session endpoint
                        lines = response_text.strip().split('\n')
                        session_endpoint = None
                        
                        for line in lines:
                            if line.startswith('data: '):
                                try:
                                    data_json = line[6:]  # Remove "data: " prefix
                                    if data_json.startswith('/v1/'):
                                        session_endpoint = data_json
                                        break
                                except:
                                    continue
                        
                        if session_endpoint:
                            print(f"   ✅ Session endpoint found: {session_endpoint}")
                            
                            # Step 2: Test the session endpoint
                            print(f"\n🔍 Step 2: Testing session endpoint...")
                            
                            # Construct the full session URL
                            base_uri = uri.rstrip('/')
                            if session_endpoint.startswith('/'):
                                session_url = base_uri + session_endpoint
                            else:
                                session_url = base_uri + '/' + session_endpoint
                            
                            print(f"   Session URL: {session_url}")
                            
                            # Test tools/list on session endpoint
                            tools_request = {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "tools/list",
                                "params": {}
                            }
                            
                            print(f"   Sending tools/list request...")
                            async with session.post(
                                session_url,
                                json=tools_request,
                                headers={
                                    "Content-Type": "application/json",
                                    "Accept": "application/json, text/event-stream"
                                },
                                timeout=aiohttp.ClientTimeout(total=30)
                            ) as tools_response:
                                
                                print(f"   Tools response status: {tools_response.status}")
                                print(f"   Tools response headers: {dict(tools_response.headers)}")
                                
                                if tools_response.status == 200:
                                    try:
                                        tools_data = await tools_response.json()
                                        print(f"   ✅ Tools response: {json.dumps(tools_data, indent=2)}")
                                    except:
                                        tools_text = await tools_response.text()
                                        print(f"   ✅ Tools response (text): {tools_text}")
                                        
                                        # Try to parse SSE response
                                        if 'event:' in tools_text:
                                            lines = tools_text.strip().split('\n')
                                            for line in lines:
                                                if line.startswith('data: '):
                                                    try:
                                                        data_json = line[6:]
                                                        tools_data = json.loads(data_json)
                                                        print(f"   ✅ Parsed SSE tools data: {json.dumps(tools_data, indent=2)}")
                                                        break
                                                    except:
                                                        continue
                                else:
                                    try:
                                        error_data = await tools_response.json()
                                        print(f"   ❌ Tools error: {json.dumps(error_data, indent=2)}")
                                    except:
                                        error_text = await tools_response.text()
                                        print(f"   ❌ Tools error (text): {error_text}")
                            
                            # Step 3: Test a simple tool call
                            print(f"\n🔍 Step 3: Testing simple tool call...")
                            
                            tool_call_request = {
                                "jsonrpc": "2.0",
                                "id": 2,
                                "method": "tools/call",
                                "params": {
                                    "name": "gmail-list-labels",
                                    "arguments": {
                                        "instruction": "List all Gmail labels"
                                    }
                                }
                            }
                            
                            print(f"   Sending tool call request...")
                            async with session.post(
                                session_url,
                                json=tool_call_request,
                                headers={
                                    "Content-Type": "application/json",
                                    "Accept": "application/json, text/event-stream"
                                },
                                timeout=aiohttp.ClientTimeout(total=45)
                            ) as tool_response:
                                
                                print(f"   Tool call response status: {tool_response.status}")
                                print(f"   Tool call response headers: {dict(tool_response.headers)}")
                                
                                if tool_response.status == 200:
                                    try:
                                        tool_data = await tool_response.json()
                                        print(f"   ✅ Tool call response: {json.dumps(tool_data, indent=2)}")
                                    except:
                                        tool_text = await tool_response.text()
                                        print(f"   ✅ Tool call response (text): {tool_text}")
                                        
                                        # Try to parse SSE response
                                        if 'event:' in tool_text:
                                            lines = tool_text.strip().split('\n')
                                            for line in lines:
                                                if line.startswith('data: '):
                                                    try:
                                                        data_json = line[6:]
                                                        tool_data = json.loads(data_json)
                                                        print(f"   ✅ Parsed SSE tool data: {json.dumps(tool_data, indent=2)}")
                                                        break
                                                    except:
                                                        continue
                                else:
                                    try:
                                        error_data = await tool_response.json()
                                        print(f"   ❌ Tool call error: {json.dumps(error_data, indent=2)}")
                                    except:
                                        error_text = await tool_response.text()
                                        print(f"   ❌ Tool call error (text): {error_text}")
                        else:
                            print(f"   ❌ No session endpoint found in response")
                            
        except asyncio.TimeoutError:
            print(f"   ❌ Request timed out")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        # Summary
        print(f"\n" + "=" * 50)
        print("📊 Pipedream Session Test Summary")
        print("=" * 50)
        
        print(f"💡 Based on the test results:")
        print(f"   1. If session endpoint is found: Pipedream is working")
        print(f"   2. If tools/list works: MCP server is responding")
        print(f"   3. If tool call works: Gmail integration is working")
        print(f"   4. If timeouts occur: Workflow might be slow or misconfigured")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipedream_session()) 