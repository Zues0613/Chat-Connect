# 🧪 **ChatConnect MCP Testing Guide**

This guide helps you test your MCP host functionality using simple, reliable MCP servers instead of complex external services like Gmail or Pipedream.

## 🎯 **Why Use Simple MCP Servers?**

**Problem**: Complex MCP servers like Gmail can cause timeouts and authentication issues during testing.

**Solution**: Use lightweight, local MCP servers that:
- ✅ **No external dependencies** - Everything runs locally
- ✅ **Fast response times** - No network delays
- ✅ **No authentication required** - Simple to set up
- ✅ **Predictable behavior** - Easy to debug
- ✅ **Multiple tools** - Test different scenarios

## 🚀 **Quick Start**

### **Step 1: Add Test MCP Servers**

```bash
# Navigate to backend directory
cd backend

# Add test MCP servers to your database
python add_test_mcp_servers.py add your-email@example.com

# Or use the first user in database
python add_test_mcp_servers.py add
```

### **Step 2: Start the Simple MCP Servers**

```bash
# Start the test MCP servers on port 8001
python -m app.services.simple_mcp_servers
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### **Step 3: Test in ChatConnect**

1. **Start your ChatConnect backend** (if not already running)
2. **Open ChatConnect in your browser**
3. **Start a new chat**
4. **Try these test prompts**:

## 📝 **Test Prompts**

### **Calculator Tests**

```
"Can you add 15 and 27 for me?"
```

**Expected Response**: The AI should use the `calculator_add` tool and return 42.

```
"What is 8 multiplied by 6?"
```

**Expected Response**: The AI should use the `calculator_multiply` tool and return 48.

```
"Divide 100 by 4"
```

**Expected Response**: The AI should use the `calculator_divide` tool and return 25.

### **Weather Tests**

```
"What's the weather like in New York?"
```

**Expected Response**: The AI should use the `weather_get_current` tool and return simulated weather data.

```
"Can you give me a 3-day forecast for London?"
```

**Expected Response**: The AI should use the `weather_get_forecast` tool and return a 3-day forecast.

### **File Operations Tests**

```
"Create a file called 'test.txt' with the content 'Hello World'"
```

**Expected Response**: The AI should use the `file_write` tool and create the file.

```
"Read the content of test.txt"
```

**Expected Response**: The AI should use the `file_read` tool and return "Hello World".

```
"List all files in the temp directory"
```

**Expected Response**: The AI should use the `file_list` tool and show available files.

### **Complex Tests**

```
"Calculate 15 + 27, then tell me the weather in Tokyo, and finally create a file called 'results.txt' with both results"
```

**Expected Response**: The AI should use multiple tools in sequence.

## 🔍 **Available Test Tools**

### **Calculator Server** (`http://localhost:8001/calculator`)

| Tool | Description | Parameters |
|------|-------------|------------|
| `calculator_add` | Add two numbers | `a` (number), `b` (number) |
| `calculator_multiply` | Multiply two numbers | `a` (number), `b` (number) |
| `calculator_divide` | Divide first by second | `a` (number), `b` (number) |

### **Weather Server** (`http://localhost:8001/weather`)

| Tool | Description | Parameters |
|------|-------------|------------|
| `weather_get_current` | Get current weather | `location` (string) |
| `weather_get_forecast` | Get weather forecast | `location` (string), `days` (integer, optional) |

### **File Operations Server** (`http://localhost:8001/files`)

| Tool | Description | Parameters |
|------|-------------|------------|
| `file_write` | Write text to file | `filename` (string), `content` (string) |
| `file_read` | Read file content | `filename` (string) |
| `file_list` | List all files | None |

### **Combined Server** (`http://localhost:8001/mcp`)

All tools from the above servers combined in one endpoint.

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **1. "No MCP servers found"**

**Solution**: Make sure you've added the test servers:
```bash
python add_test_mcp_servers.py list
```

#### **2. "Connection refused"**

**Solution**: Start the simple MCP servers:
```bash
python -m app.services.simple_mcp_servers
```

#### **3. "Tool not found"**

**Solution**: Check if the servers are properly connected:
```bash
curl http://localhost:8001/mcp -X POST -H "Content-Type: application/json" -d '{"method":"tools/list"}'
```

#### **4. "Timeout errors"**

**Solution**: The simple servers should respond quickly. If you get timeouts:
- Check if the servers are running on port 8001
- Verify your ChatConnect backend can reach localhost:8001
- Check firewall settings

### **Debug Commands**

```bash
# List all MCP servers for a user
python add_test_mcp_servers.py list your-email@example.com

# Test MCP server directly
curl http://localhost:8001/mcp -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "calculator_add",
    "arguments": {"a": 5, "b": 3}
  }
}'

# Check server health
curl http://localhost:8001/
```

## 📊 **Expected Results**

### **Successful Tool Execution**

When tools work correctly, you should see:

1. **AI recognizes the need for a tool**
2. **Tool is called with correct parameters**
3. **Tool returns results**
4. **AI incorporates results into response**

Example successful interaction:
```
User: "What is 15 + 27?"

AI: Let me calculate that for you.

[Tool: calculator_add called with a=15, b=27]

The result of 15 + 27 is 42.
```

### **Tool Discovery**

The AI should be able to discover and use these tools automatically. You can verify this by checking the logs for:

```
[DEBUG] Available MCP tools for DeepSeek: 12 tools
[DEBUG] Tool names: ['calculator_add', 'calculator_multiply', 'weather_get_current', ...]
```

## 🔧 **Advanced Testing**

### **Testing Multiple Tools**

Try complex requests that require multiple tools:

```
"Calculate 10 * 5, then tell me the weather in Paris, and save both results to a file called 'complex_test.txt'"
```

### **Testing Error Handling**

Try invalid inputs:

```
"Divide 10 by 0"
```

Expected: Should handle division by zero error gracefully.

### **Testing Tool Chaining**

```
"Add 5 and 3, multiply the result by 2, then tell me the weather in Tokyo"
```

Expected: Should chain multiple tool calls together.

## 🎯 **Next Steps After Testing**

Once you've confirmed the simple MCP servers work:

1. **Test with real MCP servers** (Gmail, etc.)
2. **Compare performance** between simple and complex servers
3. **Identify bottlenecks** in your MCP host implementation
4. **Optimize timeout settings** based on real-world usage

## 📋 **Management Commands**

```bash
# Add test servers
python add_test_mcp_servers.py add your-email@example.com

# List all servers
python add_test_mcp_servers.py list your-email@example.com

# Delete test servers
python add_test_mcp_servers.py delete your-email@example.com

# Show help
python add_test_mcp_servers.py help
```

## 🎉 **Success Criteria**

Your MCP host is working correctly if:

✅ **Tools are discovered** automatically
✅ **Tools are called** with correct parameters
✅ **Results are returned** and incorporated into AI responses
✅ **Multiple tools** can be used in sequence
✅ **Error handling** works gracefully
✅ **No timeouts** occur with simple servers

## 🔮 **Beyond Testing**

Once you've verified functionality with simple servers:

1. **Add real MCP servers** (Gmail, Slack, etc.)
2. **Implement proper error handling** for external services
3. **Add monitoring and logging** for production use
4. **Optimize performance** based on real usage patterns
5. **Add user management** for MCP server configurations

This testing approach ensures your MCP host foundation is solid before adding complexity with external services. 