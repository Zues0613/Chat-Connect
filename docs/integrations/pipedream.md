# 🔗 **Pipedream MCP Integration Guide**

This guide helps you connect your Pipedream workflows to ChatConnect as MCP servers, enabling AI-powered automation and tool integration.

## 🎯 **What is Pipedream MCP?**

Pipedream MCP (Model Context Protocol) allows you to expose your Pipedream workflows as tools that AI assistants can use. This means your AI can:

- ✅ **Send emails** via Gmail workflows
- ✅ **Post messages** to Slack
- ✅ **Create issues** in GitHub
- ✅ **Update databases** and spreadsheets
- ✅ **Trigger any API** or service
- ✅ **Automate complex workflows**

## 🚀 **Quick Start**

### **Step 1: Create a Pipedream MCP Workflow**

1. **Go to [Pipedream](https://pipedream.com)** and sign in
2. **Create a new workflow** or use an existing one
3. **Add MCP support** to your workflow:
   - Click on your workflow
   - Go to **Settings** → **MCP**
   - Enable **MCP Server**
   - Copy the **MCP Endpoint URL**

### **Step 2: Add to ChatConnect**

1. **Open ChatConnect Settings**
2. **Go to MCP Servers tab**
3. **Select "Pipedream Workflow"** as server type
4. **Paste your Pipedream MCP URL**
5. **Click "Add MCP Server"**

### **Step 3: Test Your Integration**

1. **Start a new chat** in ChatConnect
2. **Ask your AI** to use the connected tools
3. **Verify** that the tools work correctly

## 📋 **Pipedream MCP URL Format**

Your Pipedream MCP URL will look like this:

```
https://mcp.pipedream.net/[workflow-id]/[endpoint]
```

**Example:**
```
https://mcp.pipedream.net/6919d1b2-8143-422f-a5ae-6bca936cdbe6/gmail
```

## 🔧 **Creating Pipedream MCP Workflows**

### **Gmail Integration Example**

1. **Create a new Pipedream workflow**
2. **Add Gmail trigger** (new email, etc.)
3. **Add Gmail action** (send email, etc.)
4. **Enable MCP Server** in workflow settings
5. **Copy the MCP endpoint URL**

### **Slack Integration Example**

1. **Create a new Pipedream workflow**
2. **Add Slack trigger** (new message, etc.)
3. **Add Slack action** (send message, etc.)
4. **Enable MCP Server** in workflow settings
5. **Copy the MCP endpoint URL**

### **Custom API Integration**

1. **Create a new Pipedream workflow**
2. **Add HTTP trigger** or **Webhook**
3. **Add HTTP action** to call your API
4. **Enable MCP Server** in workflow settings
5. **Copy the MCP endpoint URL**

## 🛠️ **Common Pipedream MCP Workflows**

### **Email Automation**
```
Workflow: Send Email via Gmail
MCP URL: https://mcp.pipedream.net/[id]/gmail
Tools: gmail-send-email, gmail-create-draft
```

### **Slack Integration**
```
Workflow: Post to Slack
MCP URL: https://mcp.pipedream.net/[id]/slack
Tools: slack-send-message, slack-create-channel
```

### **GitHub Integration**
```
Workflow: GitHub Actions
MCP URL: https://mcp.pipedream.net/[id]/github
Tools: github-create-issue, github-create-pull-request
```

### **File Operations**
```
Workflow: Google Drive
MCP URL: https://mcp.pipedream.net/[id]/drive
Tools: drive-upload-file, drive-create-folder
```

## 🧪 **Testing Your Pipedream MCP Server**

### **Test Commands**

Once your Pipedream MCP server is connected, try these commands in ChatConnect:

#### **Gmail Workflow**
```
"Send an email to user@example.com with subject 'Test' and body 'Hello from AI'"
```

#### **Slack Workflow**
```
"Post a message to #general channel saying 'Hello from ChatConnect AI'"
```

#### **GitHub Workflow**
```
"Create a new issue in my repository with title 'Bug Report' and description 'Found a bug'"
```

### **Expected Behavior**

When working correctly, you should see:

1. **AI recognizes** the need for a tool
2. **Tool is called** with correct parameters
3. **Pipedream workflow executes** the action
4. **AI confirms** the action was completed
5. **No timeouts** or errors

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. "Invalid Pipedream URL" Error**

**Problem**: URL doesn't start with `https://mcp.pipedream.net/`

**Solution**: 
- Make sure you copied the MCP endpoint URL, not the workflow URL
- Check that MCP Server is enabled in your Pipedream workflow settings

#### **2. "Connection timeout" Error**

**Problem**: Pipedream workflow is taking too long to respond

**Solution**:
- Check your Pipedream workflow for infinite loops
- Simplify complex workflows
- Add timeouts to workflow steps
- Use the enhanced timeout handling (300s) in ChatConnect

#### **3. "No tools found" Error**

**Problem**: Pipedream workflow doesn't expose any tools

**Solution**:
- Make sure MCP Server is enabled in workflow settings
- Add actions to your workflow that can be exposed as tools
- Check workflow logs for errors

#### **4. "Authentication required" Error**

**Problem**: Pipedream workflow requires OAuth authentication

**Solution**:
- Complete OAuth setup in your Pipedream workflow
- Make sure all required permissions are granted
- Test the workflow manually in Pipedream first

### **Debug Steps**

1. **Test in Pipedream**: Run your workflow manually in Pipedream dashboard
2. **Check MCP Settings**: Verify MCP Server is enabled in workflow settings
3. **Check Workflow Logs**: Look for errors in Pipedream workflow execution
4. **Test Connection**: Use the "Test Connection" feature in ChatConnect settings
5. **Check URL Format**: Ensure the MCP URL is correct

## 📊 **Best Practices**

### **Workflow Design**

1. **Keep workflows simple** - Avoid complex logic that might timeout
2. **Add error handling** - Use try-catch blocks in your workflow
3. **Set appropriate timeouts** - Don't let steps run indefinitely
4. **Test thoroughly** - Test workflows manually before connecting to ChatConnect

### **Security**

1. **Use environment variables** - Store sensitive data in Pipedream environment variables
2. **Limit permissions** - Only grant necessary permissions to your workflows
3. **Monitor usage** - Check Pipedream usage and billing regularly
4. **Review logs** - Monitor workflow execution logs for security issues

### **Performance**

1. **Optimize API calls** - Minimize external API calls in workflows
2. **Use caching** - Cache frequently accessed data
3. **Batch operations** - Group related operations together
4. **Monitor response times** - Keep workflows under 30 seconds when possible

## 🔮 **Advanced Features**

### **Workflow Chaining**

You can chain multiple Pipedream workflows together:

1. **Create multiple workflows** for different purposes
2. **Connect them all** to ChatConnect
3. **Let AI orchestrate** complex multi-step processes

### **Custom Tools**

Create custom tools in Pipedream:

1. **Add HTTP actions** to call your custom APIs
2. **Expose them as MCP tools** in workflow settings
3. **Use them in ChatConnect** conversations

### **Webhook Integration**

Use webhooks to trigger workflows:

1. **Create webhook triggers** in Pipedream
2. **Expose webhook URLs** as MCP tools
3. **Let AI trigger** workflows on demand

## 📖 **Examples**

### **Complete Email Automation**

**Pipedream Workflow**:
1. Trigger: Manual (MCP tool call)
2. Action: Gmail - Send Email
3. Action: Slack - Post notification
4. Action: Database - Log email sent

**ChatConnect Usage**:
```
"Send a welcome email to newuser@company.com and notify the team in Slack"
```

### **Issue Management**

**Pipedream Workflow**:
1. Trigger: Manual (MCP tool call)
2. Action: GitHub - Create Issue
3. Action: Slack - Post to #bugs channel
4. Action: Email - Notify team lead

**ChatConnect Usage**:
```
"Create a bug report for the login issue and notify the development team"
```

## 🎉 **Success Criteria**

Your Pipedream MCP integration is working correctly when:

✅ **Workflows execute** without timeouts
✅ **Tools are discovered** automatically by ChatConnect
✅ **AI can use tools** to perform actions
✅ **Error handling** works gracefully
✅ **Performance** is acceptable (under 30 seconds)
✅ **Security** is maintained (proper authentication)

## 📞 **Support**

If you encounter issues:

1. **Check this guide** for troubleshooting steps
2. **Review Pipedream documentation** for workflow-specific help
3. **Test workflows manually** in Pipedream dashboard
4. **Check ChatConnect logs** for detailed error messages
5. **Contact support** if issues persist

## 🔗 **Useful Links**

- [Pipedream Documentation](https://pipedream.com/docs)
- [Pipedream MCP Guide](https://pipedream.com/docs/mcp)
- [ChatConnect Documentation](https://github.com/your-repo/docs)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

---

This guide should help you successfully integrate Pipedream workflows with ChatConnect for powerful AI-powered automation! 