#!/usr/bin/env python3
"""
Test Pipedream URL

This script tests if the Pipedream MCP server URL is accessible and working.
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

async def test_pipedream_url():
    """Test Pipedream URL accessibility"""
    print("🔗 Testing Pipedream URL Accessibility")
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
        print(f"📧 Testing server: {server.name}")
        
        # Parse config
        if isinstance(server.config, str):
            config = json.loads(server.config)
        else:
            config = server.config
        
        uri = config.get('uri', '')
        print(f"🔗 URI: {uri}")
        
        await prisma.disconnect()
        
        if not uri:
            print("❌ No URI found in server config")
            return
        
        # Test 1: Simple GET request to check if URL is accessible
        print(f"\n🔍 Test 1: Checking URL accessibility...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(uri, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    print(f"   Status: {response.status}")
                    print(f"   Headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        print(f"   ✅ URL is accessible")
                    else:
                        print(f"   ⚠️ URL returned status {response.status}")
                        
        except asyncio.TimeoutError:
            print(f"   ❌ GET request timed out")
        except Exception as e:
            print(f"   ❌ GET request failed: {e}")
        
        # Test 2: POST request with minimal JSON-RPC
        print(f"\n🔍 Test 2: Testing JSON-RPC POST request...")
        try:
            async with aiohttp.ClientSession() as session:
                test_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                }
                
                print(f"   Sending payload: {json.dumps(test_payload, indent=2)}")
                
                async with session.post(
                    uri,
                    json=test_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    },
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    print(f"   Status: {response.status}")
                    print(f"   Headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        try:
                            response_data = await response.json()
                            print(f"   ✅ Response: {json.dumps(response_data, indent=2)}")
                        except:
                            response_text = await response.text()
                            print(f"   ✅ Response (text): {response_text}")
                    else:
                        try:
                            error_data = await response.json()
                            print(f"   ❌ Error response: {json.dumps(error_data, indent=2)}")
                        except:
                            error_text = await response.text()
                            print(f"   ❌ Error response (text): {error_text}")
                        
        except asyncio.TimeoutError:
            print(f"   ❌ POST request timed out")
        except Exception as e:
            print(f"   ❌ POST request failed: {e}")
        
        # Test 3: Test with a simple tool call
        print(f"\n🔍 Test 3: Testing simple tool call...")
        try:
            async with aiohttp.ClientSession() as session:
                test_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "mcp_Gmail_gmail-list-labels",
                        "arguments": {
                            "instruction": "List all Gmail labels"
                        }
                    }
                }
                
                print(f"   Sending tool call: {json.dumps(test_payload, indent=2)}")
                
                async with session.post(
                    uri,
                    json=test_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    },
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            response_data = await response.json()
                            print(f"   ✅ Tool call response: {json.dumps(response_data, indent=2)}")
                        except:
                            response_text = await response.text()
                            print(f"   ✅ Tool call response (text): {response_text}")
                    else:
                        try:
                            error_data = await response.json()
                            print(f"   ❌ Tool call error: {json.dumps(error_data, indent=2)}")
                        except:
                            error_text = await response.text()
                            print(f"   ❌ Tool call error (text): {error_text}")
                        
        except asyncio.TimeoutError:
            print(f"   ❌ Tool call timed out")
        except Exception as e:
            print(f"   ❌ Tool call failed: {e}")
        
        # Summary
        print(f"\n" + "=" * 50)
        print("📊 Pipedream URL Test Summary")
        print("=" * 50)
        
        print(f"💡 Based on the test results:")
        print(f"   1. If GET request works: URL is accessible")
        print(f"   2. If tools/list works: MCP server is responding")
        print(f"   3. If tool call works: Gmail integration is working")
        print(f"   4. If timeouts occur: Workflow might be slow or misconfigured")
        
        print(f"\n🔧 Troubleshooting tips:")
        print(f"   • Check Pipedream workflow logs")
        print(f"   • Verify Gmail API credentials in Pipedream")
        print(f"   • Test the workflow manually in Pipedream")
        print(f"   • Check if the workflow has proper error handling")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipedream_url()) 