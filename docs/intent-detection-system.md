# Intent Detection & Confirmation System

## 🎯 Overview

ChatConnect now features a **smart intent detection and confirmation system** that works like Cursor.ai's terminal command confirmation. This system automatically detects when users want to perform actions and asks for permission before executing them.

## 🚀 How It Works

### 1. **Intent Detection**
- Analyzes user messages to detect action-oriented requests
- Matches detected intents with available MCP servers
- Calculates confidence scores for accurate detection

### 2. **Smart Response System**
- **MCP Servers Available**: Asks for confirmation before execution
- **No MCP Servers**: Provides helpful setup guide
- **Regular Chat**: Continues with normal AI conversation

### 3. **Confirmation Flow**
- Creates unique confirmation IDs
- 5-minute expiration for security
- Simple confirm/cancel commands

## 📋 Supported Intent Types

### **Email Operations**
- **Patterns**: "send email", "compose mail", "gmail", "check inbox"
- **MCP Servers**: `gmail`, `outlook`
- **Actions**: Send, read, search emails

### **File Operations**
- **Patterns**: "create file", "read document", "search files"
- **MCP Servers**: `filesystem`, `google_drive`, `dropbox`
- **Actions**: Create, read, search, organize files

### **Calendar Operations**
- **Patterns**: "schedule meeting", "check calendar", "reminder"
- **MCP Servers**: `google_calendar`, `outlook_calendar`
- **Actions**: Create events, check schedule

### **Web Search**
- **Patterns**: "search web", "find information", "weather"
- **MCP Servers**: `web_search`, `weather`
- **Actions**: Search web, get weather info

### **Code Execution**
- **Patterns**: "run code", "execute script", "terminal"
- **MCP Servers**: `terminal`, `code_executor`
- **Actions**: Execute code, run commands

### **Database Operations**
- **Patterns**: "query database", "insert record", "search data"
- **MCP Servers**: `database`, `sql`
- **Actions**: Query, insert, update data

## 🔄 User Flow Examples

### **Scenario 1: User Has MCP Servers**

```
User: "Send an email to john@example.com about the meeting"

AI: 🔐 Action Confirmation Required

Action: Email Operations
Message: "Send an email to john@example.com about the meeting"
MCP Servers: gmail

Confirmation ID: `abc123-def456-ghi789`

To proceed, please respond with:
- `confirm abc123-def456-ghi789` - to execute the action
- `cancel abc123-def456-ghi789` - to cancel the action

⏰ This confirmation expires in 5 minutes.

User: "confirm abc123-def456-ghi789"

AI: 🚀 Executing Action

Action: Email Operations
MCP Servers: gmail

Processing your request... This may take a few moments.
[Email is sent via Gmail MCP server]
```

### **Scenario 2: User Has No MCP Servers**

```
User: "Send an email to john@example.com about the meeting"

AI: 🔧 Email Operations Setup Required

To use email features, you need to configure Gmail or Outlook MCP servers in your settings.

To get started:
1. Go to Settings → MCP Servers
2. Add the required server(s): gmail, outlook
3. Configure your credentials
4. Try your request again

Available servers for this action:
gmail, outlook

Would you like me to help you with something else, or would you prefer to set up the MCP servers first?
```

### **Scenario 3: Regular Chat**

```
User: "Help me write a Python function"

AI: [Normal AI response without any MCP interaction]
```

## 🛠️ Technical Implementation

### **Core Components**

1. **IntentDetector** (`app/services/intent_detector.py`)
   - Pattern matching with regex
   - Confidence scoring
   - MCP server matching

2. **ConfirmationHandler** (`app/services/confirmation_handler.py`)
   - Confirmation management
   - Timeout handling
   - User permission tracking

3. **Integration** (`app/chat/routes.py`)
   - Message preprocessing
   - Intent detection
   - Confirmation flow

### **Configuration**

```env
# Enable/disable MCP servers completely
ENABLE_MCP_SERVERS="true"

# Intent detection confidence threshold
INTENT_CONFIDENCE_THRESHOLD=0.3

# Confirmation timeout (minutes)
CONFIRMATION_TIMEOUT=5
```

## 🧪 Testing

Run the test script to see the system in action:

```bash
cd backend
python test_intent_detection.py
```

This will demonstrate:
- Intent detection for various message types
- Confirmation system workflow
- Setup guide generation
- Error handling

## 🔧 Customization

### **Adding New Intent Types**

1. **Update Intent Patterns** in `intent_detector.py`:
```python
"new_intent": {
    "patterns": [
        r"\b(your|pattern|here)\b",
        r"\b(another|pattern)\b"
    ],
    "mcp_servers": ["server1", "server2"],
    "description": "Description of the intent",
    "setup_guide": "Setup instructions for users",
    "confirmation_message": "Confirmation prompt"
}
```

2. **Add MCP Server Support** in your MCP service configuration

### **Modifying Confidence Scoring**

Adjust the `_calculate_confidence` method in `IntentDetector`:
```python
def _calculate_confidence(self, message: str, pattern: str) -> float:
    # Custom confidence calculation logic
    confidence = 0.5
    
    # Add your custom scoring rules
    if "specific_word" in message:
        confidence += 0.3
    
    return min(confidence, 1.0)
```

## 🎯 Benefits

### **For Users**
- **Security**: Explicit permission for actions
- **Transparency**: Clear understanding of what will happen
- **Control**: Easy to cancel unwanted actions
- **Guidance**: Helpful setup instructions

### **For Developers**
- **Extensible**: Easy to add new intent types
- **Maintainable**: Clean separation of concerns
- **Testable**: Comprehensive test coverage
- **Configurable**: Environment-based settings

### **For System**
- **Reliable**: Graceful fallback to regular chat
- **Secure**: Timeout-based confirmations
- **Scalable**: Stateless confirmation handling
- **User-Friendly**: Clear, actionable messages

## 🚀 Future Enhancements

### **Planned Features**
- **Visual Confirmation UI**: Buttons instead of text commands
- **Batch Actions**: Confirm multiple actions at once
- **Smart Suggestions**: Suggest related actions
- **Learning**: Improve detection based on user feedback

### **Advanced Patterns**
- **Context Awareness**: Consider conversation history
- **Multi-Step Actions**: Complex action sequences
- **Conditional Logic**: Smart action routing
- **Integration APIs**: Connect with external services

## 📞 Support

For questions or issues with the intent detection system:

1. **Check Logs**: Look for intent detection messages in server logs
2. **Test Patterns**: Use the test script to verify detection
3. **Review Configuration**: Ensure MCP servers are properly configured
4. **Update Patterns**: Add custom patterns for your use case

---

**This system makes ChatConnect both powerful and safe, giving users the best of both worlds: advanced AI capabilities with complete control over their actions.** 