"use client";
import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getAuthToken } from "../../utils/cookies";

interface APIKey {
  id: number;
  name: string;
  provider: string;
  value: string;
}

interface MCPServer {
  id: number;
  name: string;
  description?: string;
  config: Record<string, any>;
  createdAt: string;
}

const AI_PROVIDERS = [
  { value: "deepseek", label: "DeepSeek R1 (via OpenRouter)", placeholder: "Enter your OpenRouter API key" },
  { value: "openai", label: "OpenAI GPT", placeholder: "Enter your OpenAI API key" },
  { value: "anthropic", label: "Anthropic Claude", placeholder: "Enter your Anthropic API key" },
];

const MCP_SERVER_TYPES = [
  { 
    value: "pipedream", 
    label: "Pipedream Workflow", 
    description: "Connect to a Pipedream MCP workflow",
    example: "https://mcp.pipedream.net/[workflow-id]/[endpoint]",
    placeholder: "https://mcp.pipedream.net/6919d1b2-8143-422f-a5ae-6bca936cdbe6/gmail"
  },
  { 
    value: "stdio", 
    label: "Standard I/O", 
    description: "Connect to an MCP server using standard input/output",
    example: "npx -y @modelcontextprotocol/server-filesystem /path/to/directory",
    placeholder: "npx -y @modelcontextprotocol/server-filesystem /path/to/directory"
  },
  { 
    value: "sse", 
    label: "Server-Sent Events", 
    description: "Connect to an MCP server using HTTP with Server-Sent Events",
    example: "http://localhost:3000/sse",
    placeholder: "http://localhost:3000/sse"
  },
  { 
    value: "websocket", 
    label: "WebSocket", 
    description: "Connect to an MCP server using WebSocket protocol",
    example: "ws://localhost:3000/ws",
    placeholder: "ws://localhost:3000/ws"
  },
  { 
    value: "custom", 
    label: "Custom URI", 
    description: "Connect using any custom MCP server URI",
    example: "mcp://custom-server.example.com:8080",
    placeholder: "mcp://custom-server.example.com:8080"
  }
];

export default function SettingsPage() {
  const searchParams = useSearchParams();
  
  // API Keys state
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [apiKeyName, setApiKeyName] = useState("");
  const [apiKeyProvider, setApiKeyProvider] = useState("");
  const [apiKeyValue, setApiKeyValue] = useState("");
  const [apiKeyLoading, setApiKeyLoading] = useState(false);

  // MCP Servers state
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([]);
  const [mcpServerName, setMcpServerName] = useState("");
  const [mcpServerType, setMcpServerType] = useState("");
  const [mcpServerDescription, setMcpServerDescription] = useState("");
  const [mcpServerUrl, setMcpServerUrl] = useState("");
  const [mcpServerLoading, setMcpServerLoading] = useState(false);
  const [mcpServersLoading, setMcpServersLoading] = useState(true);

  // General state
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"api-keys" | "mcp-servers">("api-keys");
  const [oauthStatus, setOauthStatus] = useState<any[]>([]);
  const [oauthLoading, setOauthLoading] = useState(false);

  // Set tab from URL parameter and handle OAuth messages
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'mcp-servers') {
      setActiveTab('mcp-servers');
    }
    
    // Handle OAuth success/error messages
    const oauthSuccess = searchParams.get('oauth_success');
    const oauthError = searchParams.get('oauth_error');
    const serverName = searchParams.get('server_name');
    
    if (oauthSuccess) {
      setError("");
      // Show success message
      alert(`✅ OAuth authentication completed successfully for ${serverName || 'the server'}!`);
    } else if (oauthError) {
      setError(`OAuth authentication failed: ${oauthError}`);
    }
  }, [searchParams]);

  // Fetch data on mount
  useEffect(() => {
    fetchApiKeys();
    fetchMcpServers();
    fetchOAuthStatus();
  }, []);

  const fetchApiKeys = async () => {
    const token = getAuthToken();
    if (!token) return;
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/api-keys", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch API keys");
      const data = await res.json();
      setApiKeys(data);
    } catch (err) {
      setError("Could not load API keys.");
    }
  };

  const fetchMcpServers = async () => {
    const token = getAuthToken();
    if (!token) return;
    setMcpServersLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/mcp-servers", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch MCP servers");
      const data = await res.json();
      console.log("[DEBUG] Settings MCP servers response:", data);
      setMcpServers(Array.isArray(data) ? data : []); // Handle direct array response
    } catch (err) {
      console.error("[DEBUG] Settings MCP servers error:", err);
      setMcpServers([]); // Set empty array on error
      setError("Could not load MCP servers.");
    } finally {
      setMcpServersLoading(false);
    }
  };

  const fetchOAuthStatus = async () => {
    const token = getAuthToken();
    if (!token) return;
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/oauth/status", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        console.warn("[DEBUG] OAuth status fetch failed, continuing without OAuth data");
        setOauthStatus([]);
        return;
      }
      const data = await res.json();
      setOauthStatus(Array.isArray(data) ? data : []);
    } catch (err) {
      console.warn("[DEBUG] Settings OAuth status error (non-critical):", err);
      setOauthStatus([]);
    }
  };

  // API Key handlers
  const handleAddApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiKeyLoading(true);
    setError("");
    const token = getAuthToken();
    if (!token) return;
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/api-keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          name: apiKeyName, 
          provider: apiKeyProvider, 
          value: apiKeyValue 
        }),
      });
      if (!res.ok) throw new Error("Failed to add API key");
      const newKey = await res.json();
      setApiKeys((prev) => [...prev, newKey]);
      setApiKeyName("");
      setApiKeyProvider("");
      setApiKeyValue("");
    } catch (err) {
      setError("Could not add API key.");
    }
    setApiKeyLoading(false);
  };

  const handleDeleteApiKey = async (id: number) => {
    const token = getAuthToken();
    if (!token) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/auth/api-keys/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to delete API key");
      setApiKeys((prev) => prev.filter((key) => key.id !== id));
    } catch (err) {
      setError("Could not delete API key.");
    }
  };

  // MCP Server handlers
  const handleAddMcpServer = async (e: React.FormEvent) => {
    e.preventDefault();
    setMcpServerLoading(true);
    setError("");
    const token = getAuthToken();
    if (!token) return;
    
    try {
      // Validate Pipedream URL format
      if (mcpServerType === "pipedream") {
        if (!mcpServerUrl.startsWith("https://mcp.pipedream.net/")) {
          setError("Invalid Pipedream URL. Must start with https://mcp.pipedream.net/");
          setMcpServerLoading(false);
          return;
        }
      }
      
      const res = await fetch("http://127.0.0.1:8000/auth/mcp-servers", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: mcpServerName,
          description: mcpServerDescription,
          config: { 
            type: mcpServerType === "pipedream" ? "custom" : mcpServerType, 
            uri: mcpServerUrl,
            transport: mcpServerType === "pipedream" ? "http" : mcpServerType
          }
        }),
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to add MCP server");
      }
      
      const newServer = await res.json();
      console.log("[DEBUG] New server added:", newServer);
      
      // Refresh the entire list to ensure consistency
      await fetchMcpServers();
      
      setMcpServerName("");
      setMcpServerType("");
      setMcpServerDescription("");
      setMcpServerUrl("");
    } catch (err: any) {
      setError(err.message || "Could not add MCP server.");
    }
    setMcpServerLoading(false);
  };

  const handleDeleteMcpServer = async (id: number) => {
    const token = getAuthToken();
    if (!token) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/auth/mcp-servers/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to delete MCP server");
      setMcpServers((prev) => prev.filter((server) => server.id !== id));
    } catch (err) {
      setError("Could not delete MCP server.");
    }
  };

  const handleOAuthAuthorize = async (serverId: number, provider?: string) => {
    setOauthLoading(true);
    setError("");
    const token = getAuthToken();
    if (!token) return;
    
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/oauth/authorize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          server_id: serverId,
          provider: provider
        }),
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to initiate OAuth flow");
      }
      
      const data = await res.json();
      
      // Redirect to OAuth URL
      window.location.href = data.oauth_url;
    } catch (err: any) {
      setError(err.message || "Could not initiate OAuth flow.");
    }
    setOauthLoading(false);
  };

  const handleRevokeOAuth = async (serverId: number, provider: string) => {
    const token = getAuthToken();
    if (!token) return;
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/auth/oauth/tokens/${serverId}?provider=${provider}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (!res.ok) throw new Error("Failed to revoke OAuth tokens");
      
      // Refresh OAuth status
      fetchOAuthStatus();
    } catch (err) {
      setError("Could not revoke OAuth tokens.");
    }
  };

  return (
    <div className="min-h-screen bg-[#f7f7f8] dark:bg-gradient-to-r dark:from-[#000046] dark:to-[#1CB5E0] py-10">
      <div className="max-w-4xl mx-auto px-4">
        <div className="w-full max-w-4xl mx-auto overflow-hidden bg-white rounded-lg shadow-md backdrop-blur-2xl dark:bg-[#232328] border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4">
            <div className="flex justify-center mx-auto mb-6">
              <img className="w-auto h-8 sm:h-10" src="/favicon.ico" alt="ChatConnect" />
            </div>
            
            <h1 className="text-2xl font-bold mb-6 text-center text-gray-900 dark:text-gray-100">Settings</h1>
            
            {/* Tab Navigation */}
            <div className="flex mb-6 border-b border-gray-200 dark:border-gray-700">
              <button
                className={`px-6 py-3 font-medium transition-colors ${
                  activeTab === "api-keys"
                    ? "text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400"
                    : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                }`}
                onClick={() => setActiveTab("api-keys")}
              >
                API Keys
              </button>
              <button
                className={`px-6 py-3 font-medium transition-colors ${
                  activeTab === "mcp-servers"
                    ? "text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400"
                    : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                }`}
                onClick={() => setActiveTab("mcp-servers")}
              >
                MCP Servers
              </button>
            </div>

            {error && (
              <div className="px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg mb-6">
                <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <span className="text-sm">{error}</span>
                </div>
              </div>
            )}

            {/* API Keys Tab */}
            {activeTab === "api-keys" && (
              <div>
                <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">
                  AI Model API Keys
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Add API keys for different AI models to use them in your conversations.
                </p>
                
                {/* Default API Key Info */}
                <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg mb-6">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                        API Key Information
                      </h3>
                      <div className="mt-2 text-sm text-blue-700 dark:text-blue-300">
                        <p>
                          • <strong>DeepSeek R1:</strong> Get your API key from{" "}
                          <a href="https://openrouter.ai/" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-800 dark:hover:text-blue-100">
                            OpenRouter
                          </a>
                          {" "}(free tier available)
                        </p>
                        <p>
                          • <strong>OpenAI GPT:</strong> Get your API key from{" "}
                          <a href="https://platform.openai.com/" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-800 dark:hover:text-blue-100">
                            OpenAI Platform
                          </a>
                        </p>
                        <p>
                          • <strong>Anthropic Claude:</strong> Get your API key from{" "}
                          <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-800 dark:hover:text-blue-100">
                            Anthropic Console
                          </a>
                        </p>
                        <p className="mt-2 text-xs">
                          💡 If you don't add a personal API key, the system will use a default key for basic functionality.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <form className="flex flex-col gap-4 mb-6" onSubmit={handleAddApiKey}>
                  <input
                    type="text"
                    className="block w-full px-4 py-2 text-gray-700 placeholder-gray-500 bg-white border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 focus:border-blue-400 dark:focus:border-blue-300 focus:ring-opacity-40 focus:outline-none focus:ring focus:ring-blue-300"
                    placeholder="Key Name (e.g., 'My DeepSeek Key')"
                    value={apiKeyName}
                    onChange={e => setApiKeyName(e.target.value)}
                    required
                  />
                  <select
                    className="block w-full px-4 py-2 text-gray-700 placeholder-gray-500 bg-white border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 focus:border-blue-400 dark:focus:border-blue-300 focus:ring-opacity-40 focus:outline-none focus:ring focus:ring-blue-300"
                    value={apiKeyProvider}
                    onChange={e => setApiKeyProvider(e.target.value)}
                    required
                  >
                    <option value="">Select AI Provider</option>
                    {AI_PROVIDERS.map(provider => (
                      <option key={provider.value} value={provider.value}>
                        {provider.label}
                      </option>
                    ))}
                  </select>
                  <input
                    type="password"
                    className="block w-full px-4 py-2 text-gray-700 placeholder-gray-500 bg-white border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 focus:border-blue-400 dark:focus:border-blue-300 focus:ring-opacity-40 focus:outline-none focus:ring focus:ring-blue-300"
                    placeholder={AI_PROVIDERS.find(p => p.value === apiKeyProvider)?.placeholder || "Enter your API key"}
                    value={apiKeyValue}
                    onChange={e => setApiKeyValue(e.target.value)}
                    required
                  />
                  <button
                    type="submit"
                    className="px-6 py-2 text-sm font-medium tracking-wide text-white capitalize transition-colors duration-300 transform bg-blue-500 rounded-lg hover:bg-blue-400 focus:outline-none focus:ring focus:ring-blue-300 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed w-full"
                    disabled={apiKeyLoading}
                  >
                    {apiKeyLoading ? "Adding..." : "Add API Key"}
                  </button>
                </form>

                <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">Your API Keys</h3>
                <div className="space-y-2">
                  {apiKeys.map((key) => (
                    <div key={key.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                      <div>
                        <span className="font-medium text-gray-900 dark:text-gray-100">{key.name}</span>
                        <span className="ml-3 px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                          {AI_PROVIDERS.find(p => p.value === key.provider)?.label || key.provider}
                        </span>
                      </div>
                      <button
                        className="text-red-500 hover:text-red-700 text-sm font-semibold transition-colors"
                        onClick={() => handleDeleteApiKey(key.id)}
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                  {apiKeys.length === 0 && (
                    <div className="text-gray-500 py-8 text-center">
                      No API keys added yet. Add one above to get started!
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* MCP Servers Tab */}
            {activeTab === "mcp-servers" && (
              <div>
                <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">
                  MCP Server Management
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Connect MCP servers to enable task automation and tool integration in your conversations. 
                  <strong>For Pipedream workflows</strong>, simply paste your Pipedream MCP URL. 
                  For other MCP servers, provide the appropriate connection details.
                </p>

                <form className="flex flex-col gap-4 mb-6" onSubmit={handleAddMcpServer}>
                  <input
                    type="text"
                    className="block w-full px-4 py-2 text-gray-700 placeholder-gray-500 bg-white border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 focus:border-blue-400 dark:focus:border-blue-300 focus:ring-opacity-40 focus:outline-none focus:ring focus:ring-blue-300"
                    placeholder="Server Name (e.g., 'My Pipedream Workflows')"
                    value={mcpServerName}
                    onChange={e => setMcpServerName(e.target.value)}
                    required
                  />
                  
                  <select
                    className="block w-full px-4 py-2 text-gray-700 placeholder-gray-500 bg-white border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 focus:border-blue-400 dark:focus:border-blue-300 focus:ring-opacity-40 focus:outline-none focus:ring focus:ring-blue-300"
                    value={mcpServerType}
                    onChange={e => setMcpServerType(e.target.value)}
                    required
                  >
                    <option value="">Select Server Type</option>
                    {MCP_SERVER_TYPES.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>

                  {mcpServerType && MCP_SERVER_TYPES.find(t => t.value === mcpServerType) && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <p className="text-blue-800 dark:text-blue-200 text-sm mb-3">
                        {MCP_SERVER_TYPES.find(t => t.value === mcpServerType)?.description}
                      </p>
                      <p className="text-gray-500 text-xs italic">
                        Example: {MCP_SERVER_TYPES.find(t => t.value === mcpServerType)?.example}
                      </p>
                    </div>
                  )}

                  <textarea
                    className="block w-full px-4 py-2 text-gray-700 placeholder-gray-500 bg-white border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 focus:border-blue-400 dark:focus:border-blue-300 focus:ring-opacity-40 focus:outline-none focus:ring focus:ring-blue-300"
                    placeholder="Description (optional)"
                    rows={2}
                    value={mcpServerDescription}
                    onChange={e => setMcpServerDescription(e.target.value)}
                  />

                  {/* MCP Server URL input */}
                  <input
                    type="text"
                    className="block w-full px-4 py-2 text-gray-700 placeholder-gray-500 bg-white border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 focus:border-blue-400 dark:focus:border-blue-300 focus:ring-opacity-40 focus:outline-none focus:ring focus:ring-blue-300"
                    placeholder={MCP_SERVER_TYPES.find(t => t.value === mcpServerType)?.placeholder || "MCP Server URL"}
                    value={mcpServerUrl}
                    onChange={e => setMcpServerUrl(e.target.value)}
                    required
                  />
                  
                  {mcpServerType === "pipedream" && (
                    <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                      <h4 className="text-yellow-800 dark:text-yellow-200 font-semibold mb-2">💡 Pipedream Setup Guide</h4>
                      <ol className="text-yellow-700 dark:text-yellow-300 text-sm space-y-1">
                        <li>1. Go to your <a href="https://pipedream.com" target="_blank" rel="noopener noreferrer" className="underline">Pipedream dashboard</a></li>
                        <li>2. Create or open an MCP workflow</li>
                        <li>3. Copy the MCP endpoint URL (starts with https://mcp.pipedream.net/)</li>
                        <li>4. Paste it in the URL field above</li>
                        <li>5. The system will automatically test the connection</li>
                      </ol>
                    </div>
                  )}

                  <button
                    type="submit"
                    className="px-6 py-2 text-sm font-medium tracking-wide text-white capitalize transition-colors duration-300 transform bg-green-500 rounded-lg hover:bg-green-400 focus:outline-none focus:ring focus:ring-green-300 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed w-full"
                    disabled={mcpServerLoading}
                  >
                    {mcpServerLoading ? "Adding..." : "Add MCP Server"}
                  </button>
                </form>

                <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">Your MCP Servers</h3>
                <div className="space-y-3">
                  {mcpServersLoading ? (
                    <div className="text-gray-500 py-8 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                      Loading MCP servers...
                    </div>
                  ) : Array.isArray(mcpServers) ? mcpServers.map((server) => {
                    // Find OAuth status for this server
                    const serverOAuthStatus = oauthStatus.find(status => status.server_id === server.id);
                    const isPipedream = server.config.uri?.includes("pipedream.net");
                    const provider = isPipedream && server.config.uri?.includes("gmail") ? "gmail" : 
                                   isPipedream && server.config.uri?.includes("google") ? "google" : null;
                    
                    return (
                      <div key={server.id} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className="font-medium text-gray-900 dark:text-gray-100">{server.name}</span>
                              <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
                                {MCP_SERVER_TYPES.find(t => t.value === server.config.type)?.label || server.config.type}
                              </span>
                              {serverOAuthStatus && (
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  serverOAuthStatus.is_valid 
                                    ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                                    : "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200"
                                }`}>
                                  {serverOAuthStatus.is_valid ? "🔐 Authenticated" : "❌ Expired"}
                                </span>
                              )}
                            </div>
                            {server.description && (
                              <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">{server.description}</p>
                            )}
                            <p className="text-gray-500 text-xs mb-2">
                              Added {new Date(server.createdAt).toLocaleDateString()}
                            </p>
                            
                            {/* OAuth Controls */}
                            {provider && (
                              <div className="flex gap-2 mt-3">
                                {!serverOAuthStatus || !serverOAuthStatus.is_valid ? (
                                  <button
                                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded transition-colors"
                                    onClick={() => handleOAuthAuthorize(server.id, provider)}
                                    disabled={oauthLoading}
                                  >
                                    {oauthLoading ? "Authorizing..." : `🔐 Authenticate ${provider.toUpperCase()}`}
                                  </button>
                                ) : (
                                  <button
                                    className="bg-red-600 hover:bg-red-700 text-white text-xs px-3 py-1 rounded transition-colors"
                                    onClick={() => handleRevokeOAuth(server.id, provider)}
                                  >
                                    🔓 Revoke Access
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                          <button
                            className="text-red-500 hover:text-red-700 text-sm font-semibold transition-colors"
                            onClick={() => handleDeleteMcpServer(server.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    );
                  }) : (
                    <div className="text-gray-500 py-8 text-center">
                      Error loading MCP servers
                    </div>
                  )}
                  {Array.isArray(mcpServers) && mcpServers.length === 0 && (
                    <div className="text-gray-500 py-8 text-center">
                      No MCP servers configured yet. Add one above to enable task automation!
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 