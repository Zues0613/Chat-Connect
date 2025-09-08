"use client";

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getAuthToken, clearAuthToken } from '../../utils/cookies';

interface Chat {
  id: number;
  title: string;
  createdAt: string;
  updatedAt: string;
  hash: string;
}

export default function ChatIndexPage() {
  const router = useRouter();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(false);

  const [showSearchModal, setShowSearchModal] = useState(false);
  const [modalSearch, setModalSearch] = useState("");

  const [showMCPServerModal, setShowMCPServerModal] = useState(false);
  const [mcpServers, setMcpServers] = useState<any[]>([]);
  const [mcpTools, setMcpTools] = useState<any[]>([]);
  const [isLoadingMCPServers, setIsLoadingMCPServers] = useState(false);
  const [isLoadingMCPTools, setIsLoadingMCPTools] = useState(false);
  const [isRefreshingMCP, setIsRefreshingMCP] = useState(false);

  const [newServerUrl, setNewServerUrl] = useState("");
  const [newServerName, setNewServerName] = useState("");
  const [isAddingServer, setIsAddingServer] = useState(false);

  const [user, setUser] = useState<{ name: string; email: string }>({ name: '', email: '' });
  const [isLoadingUser, setIsLoadingUser] = useState(false);

  const [enabledServers, setEnabledServers] = useState<Set<number>>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('enabledServers');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          return new Set(parsed);
        } catch {}
      }
    }
    return new Set();
  });

  const API_BASE = "/api";

  const apiCall = async (endpoint: string, options: RequestInit = {}, timeoutMs: number = 15000) => {
    const token = getAuthToken();
    if (!token) throw new Error("No auth token");

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        let detail: string | undefined;
        try {
          const parsed = JSON.parse(errorText);
          detail = parsed?.detail || parsed?.error;
        } catch {}
        throw new Error(`HTTP ${response.status}: ${detail || errorText}`);
      }

      return await response.json();
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - server took too long to respond. Please check if the backend server is running on http://127.0.0.1:8000');
      }
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        throw new Error('Cannot connect to server. Please ensure the backend server is running on http://127.0.0.1:8000');
      }
      throw error;
    }
  };

  const fetchChats = async () => {
    try {
      setIsLoadingChats(true);
      const response = await apiCall('/chat/chats');
      setChats(response);
    } catch (e) {
      console.error('Failed to fetch chats:', e);
    } finally {
      setIsLoadingChats(false);
    }
  };

  const fetchMCPServers = async () => {
    try {
      setIsLoadingMCPServers(true);
      const data = await apiCall("/auth/mcp-servers");
      const servers = Array.isArray(data) ? data : [];
      setMcpServers(servers);
      if (enabledServers.size === 0 && servers.length > 0) {
        const serverIds = servers.map(server => server.id);
        setEnabledServers(new Set(serverIds));
        localStorage.setItem('enabledServers', JSON.stringify(serverIds));
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') console.error('Failed to fetch MCP servers:', error);
      setMcpServers([]);
    } finally {
      setIsLoadingMCPServers(false);
    }
  };

  const fetchMCPTools = async () => {
    try {
      setIsLoadingMCPTools(true);
      const data = await apiCall("/chat/mcp/tools");
      setMcpTools(data.tools || []);
    } catch (error: any) {
      if (error.name !== 'AbortError') console.error('Failed to fetch MCP tools:', error);
      setMcpTools([]);
    } finally {
      setIsLoadingMCPTools(false);
    }
  };

  const fetchUserInfo = async () => {
    try {
      setIsLoadingUser(true);
      const data = await apiCall('/auth/me');
      setUser({ name: data.name || '', email: data.email || '' });
    } catch (error: any) {
      if (error.name !== 'AbortError') console.error('Error fetching user info:', error);
    } finally {
      setIsLoadingUser(false);
    }
  };

  const handleRefreshMCP = async () => {
    if (isRefreshingMCP) return;
    try {
      setIsRefreshingMCP(true);
      await Promise.all([fetchMCPServers(), fetchMCPTools()]);
    } finally {
      setIsRefreshingMCP(false);
    }
  };

  const addMCPServer = async () => {
    if (!newServerUrl.trim()) {
      alert('Please enter a server URL');
      return;
    }
    setIsAddingServer(true);
    try {
      await apiCall("/auth/mcp-servers", {
        method: "POST",
        body: JSON.stringify({ url: newServerUrl.trim(), name: newServerName.trim() || undefined }),
      });
      setNewServerUrl("");
      setNewServerName("");
      await fetchMCPServers();
      alert('MCP server added successfully!');
    } catch (error: any) {
      alert(`Failed to add MCP server: ${error.message}`);
    } finally {
      setIsAddingServer(false);
    }
  };

  const toggleServerStatus = (serverId: number) => {
    const next = new Set(enabledServers);
    if (next.has(serverId)) next.delete(serverId); else next.add(serverId);
    setEnabledServers(next);
    localStorage.setItem('enabledServers', JSON.stringify(Array.from(next)));
  };

  const deleteMCPServer = async (serverId: number) => {
    if (!confirm('Are you sure you want to delete this MCP server?')) return;
    try {
      await apiCall(`/auth/mcp-servers/${serverId}`, { method: "DELETE" });
      await fetchMCPServers();
      const next = new Set(enabledServers);
      next.delete(serverId);
      setEnabledServers(next);
      localStorage.setItem('enabledServers', JSON.stringify(Array.from(next)));
    } catch (error: any) {
      alert(`Failed to delete MCP server: ${error.message}`);
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    router.push('/login');
  };

  useEffect(() => {
    const init = async () => {
      try {
        setIsLoading(true);
        setError(null);
        await Promise.all([fetchChats()]);
        // Non-essential in background
        Promise.allSettled([fetchMCPServers(), fetchMCPTools(), fetchUserInfo()]);
      } catch (e: any) {
        setError(e.message || 'Failed to load');
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, []);

  const modalFilteredChats = chats.filter((c) => c.title.toLowerCase().includes(modalSearch.toLowerCase()));

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f7f7f8] dark:bg-[#18181a]">
        <div className="text-center">
          <div className="relative h-12 w-12 mx-auto mb-4">
            <div className="absolute inset-0 animate-ping rounded-full bg-blue-500 opacity-30"></div>
            <div className="absolute inset-0 animate-spin rounded-full border-2 border-blue-600 border-t-transparent"></div>
          </div>
          <p className="text-gray-600 dark:text-gray-400">Loading chats...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Error Loading</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <button onClick={() => router.push('/')} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">Go to Home</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-[#f7f7f8] dark:bg-gradient-to-r dark:from-[#000046] dark:to-[#1CB5E0] font-sans">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-40 flex flex-col w-64 h-screen backdrop-blur-xl bg-white/10 dark:bg-black/20 border-r border-white/20 dark:border-gray-800/50 px-3 py-4 shadow-2xl"
        style={{ background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)', boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)' }}
      >
        <div className="flex items-center justify-between mb-4">
          <img src="/favicon.ico" alt="Vee" className="h-7 w-7 rounded" />
          <button
            className="p-2 rounded-lg backdrop-blur-md bg-white/20 dark:bg-black/30 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center border border-white/20 dark:border-gray-700/50"
            onClick={() => router.push('/')}
            title="Home"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M13 5v6h6" /></svg>
          </button>
        </div>

        {/* New Chat */}
        <button 
          onClick={async () => {
            try {
              const created = await apiCall('/chat/chats', { method: 'POST', body: JSON.stringify({ title: 'New Chat' }) });
              router.push(`/chat/${created.hash}`);
            } catch (e: any) {
              alert(e.message || 'Failed to create chat');
            }
          }}
          className="flex items-center gap-2 backdrop-blur-md bg-white/30 dark:bg-white/20 text-black dark:text-white font-semibold rounded-lg px-4 py-2 mb-3 hover:bg-white/40 dark:hover:bg_white/30 transition-all border border-white/30 dark:border-white/20 shadow-lg"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
          New Chat
        </button>

        {/* Search */}
        <button 
          onClick={() => setShowSearchModal(true)}
          className="flex items-center gap-2 w-full text-white dark:text_gray-200 font-medium rounded-lg px-3 py-2 mb-2 backdrop-blur-md bg-black/30 dark:bg-black/40 hover:bg-black/40 dark:hover:bg-black/50 transition-all border border-white/20 dark:border-gray-700/50"
          style={{ cursor: 'pointer' }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" /></svg>
          🔍 Search Chats
        </button>

        {/* MCP Servers */}
        <button 
          onClick={() => setShowMCPServerModal(true)}
          className="flex items-center justify_between w-full text-white dark:text-gray-200 font-medium rounded-lg px-3 py-2 mb-2 backdrop_blur-md bg-blue-600/80 dark:bg-blue-700/80 hover:bg-blue-700/90 dark:hover:bg-blue-800/90 transition-all border border-blue-400/30 dark:border-blue-500/30 shadow-lg"
          style={{ cursor: 'pointer' }}
        >
          <div className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>
            🔌 Quick Add MCP
          </div>
          {mcpServers.length > 0 && (
            <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">{mcpServers.length}</span>
          )}
        </button>

        {/* Chats list */}
        <div className="flex-1 overflow-y-auto mt-2 mb-2 scrollbar-hide">
          <div className="px-2 py-1">
            <span className="font-bold text-white dark:text-gray-200 text-base">Chats</span>
          </div>
          {isLoadingChats ? (
            <div className="space-y-2">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="flex items-center space-x-3 p-2 rounded-lg backdrop-blur-sm bg-white/10 dark:bg-black/20 border border-white/20 dark:border-gray-700/50">
                  <div className="w-4 h-4 bg-white/30 dark:bg-gray-600/50 rounded animate-pulse"></div>
                  <div className="flex-1">
                    <div className="w-3/4 h-3 bg_white/30 dark:bg-gray-600/50 rounded animate-pulse mb-1"></div>
                    <div className="w-1/2 h-2 bg-white/20 dark:bg-gray-700/50 rounded animate-pulse"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            chats.map((c) => (
              <div key={c.id} className="flex items-center gap-2 px-2 py-2 rounded-lg transition-all group backdrop-blur-sm mb-2 hover:bg-white/15 dark:hover:bg-black/30 hover:border hover:border-white/20 dark:hover:border-gray-700/50">
                <button className="flex items-center gap-2 flex-1 text-left" onClick={() => router.push(`/chat/${c.hash}`)}>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a1 1 0 011-1h6a1 1 0 011 1v4" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h8" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 7h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2z" /></svg>
                  <span className="truncate max-w-[140px] text-white dark:text-gray-200 text-sm font-medium" title={c.title}>{c.title}</span>
                </button>
              </div>
            ))
          )}
        </div>

        {/* User info */}
        <div className="mt-auto pt-4 border-t border-white/20 dark:border-gray-800/50">
          <div className="px-2 py-3">
            {isLoadingUser ? (
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-white/30 dark:bg-gray-600/50 rounded-full animate-pulse"></div>
                <div className="flex flex-col flex-1">
                  <div className="w-24 h-3 bg-white/30 dark:bg-gray-600/50 rounded animate-pulse mb-1"></div>
                  <div className="w-32 h-2 bg-white/20 dark:bg-gray-700/50 rounded animate-pulse"></div>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white dark:text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="12" cy="8" r="4" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 20v-2a6 6 0 0112 0v2" /></svg>
                <div className="flex flex-col flex-1">
                  <span className="text-white dark:text-gray-200 text-sm font-semibold">{user.name || 'Vee User'}</span>
                  <span className="text-xs text-gray-400">{user.email || 'Pro Plan'}</span>
                </div>
                <button className="p-1 rounded hover:bg-gray-800 text-gray-400 hover:text-white transition-all" onClick={handleLogout} title="Logout">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Search Modal */}
      {showSearchModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 dark:bg-black/60 backdrop-blur-xl" onClick={(e) => { if (e.target === e.currentTarget) { setShowSearchModal(false); setModalSearch(''); }}}>
          <div className="backdrop-blur-xl bg-white/20 dark:bg-black/40 rounded-lg shadow-xl w_full max-w-md mx-4 max-h-[80vh] flex flex-col border border-white/30 dark:border-gray-700/50">
            <div className="flex items-center justify-between p-4 border-b border-white/20 dark:border-gray-700/50">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Search Chats</h2>
              <button onClick={() => setShowSearchModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <input type="text" value={modalSearch} onChange={(e) => setModalSearch(e.target.value)} placeholder="Search chats..." className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" autoFocus />
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {isLoadingChats ? (
                <div className="space-y-2">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="p-3 rounded-lg">
                      <div className="w-3/4 h-4 bg-gray-300 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
                      <div className="w-1/2 h-3 bg-gray-300 dark:bg-gray-600 rounded animate-pulse"></div>
                    </div>
                  ))}
                </div>
              ) : modalFilteredChats.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-center py-4">{modalSearch ? 'No chats found' : 'No chats available'}</p>
              ) : (
                <div className="space-y-2">
                  {modalFilteredChats.map((c) => (
                    <button key={c.id} onClick={() => { setShowSearchModal(false); setModalSearch(''); router.push(`/chat/${c.hash}`); }} className="w-full text-left p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{c.title}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">{new Date(c.updatedAt).toLocaleDateString()}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MCP Server Modal */}
      {showMCPServerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 dark:bg-black/60 backdrop-blur-xl" onClick={(e) => { if (e.target === e.currentTarget) setShowMCPServerModal(false); }}>
          <div className="backdrop-blur-xl bg-white/20 dark:bg-black/40 rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[90vh] flex flex-col border border-white/30 dark:border-gray-700/50">
            <div className="flex items-center justify-between p-4 border-b border-white/20 dark:border-gray-700/50">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">MCP Server Management</h2>
              <div className="flex items-center gap-2">
                <button onClick={handleRefreshMCP} type="button" disabled={isRefreshingMCP} className={`transition-colors p-1 rounded-lg ${isRefreshingMCP ? 'text-gray-600 cursor-not-allowed' : 'text-gray-400 hover:text-gray-200 dark:hover:text-gray-300 hover:bg-gray-700 dark:hover:bg-gray-800'}`} title={isRefreshingMCP ? "Refreshing servers and tools..." : "Refresh servers and tools"}>
                  <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 ${isRefreshingMCP ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                </button>
                <button onClick={() => setShowMCPServerModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <div className="mb-6 p-4 bg-blue-900/20 dark:bg-blue-900/10 rounded-lg border border-blue-700 dark:border-blue-800">
                <h3 className="text-md font-semibold text-blue-200 dark:text-blue-300 mb-3">🚀 Quick Add MCP Server</h3>
                <p className="text-sm text-blue-300 dark:text-blue-400 mb-4">Paste your MCP server URL from Pipedream, GitHub, or any other platform to quickly connect it.</p>
                <div className="space-y-3">
                  <input type="text" value={newServerUrl} onChange={(e) => setNewServerUrl(e.target.value)} placeholder="Paste MCP server URL here" className="w-full px-3 py-2 rounded-lg border border-blue-600 dark:border-blue-700 bg-blue-900/20 dark:bg-blue-900/10 text-white dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-blue-400 dark:placeholder-blue-500" />
                  <input type="text" value={newServerName} onChange={(e) => setNewServerName(e.target.value)} placeholder="Give it a name (optional)" className="w-full px-3 py-2 rounded-lg border border-blue-600 dark:border-blue-700 bg-blue-900/20 dark:bg-blue-900/10 text-white dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-blue-400 dark:placeholder-blue-500" />
                  <button onClick={addMCPServer} disabled={isAddingServer || !newServerUrl.trim()} className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${isAddingServer || !newServerUrl.trim() ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}>{isAddingServer ? 'Adding...' : 'Add MCP Server'}</button>
                </div>
              </div>

              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Connected Servers {isLoadingMCPServers && <span className="text-blue-400">(Refreshing...)</span>}</h3>
                {isLoadingMCPServers ? (
                  <div className="space-y-3">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            <div className="w-4 h-4 bg-gray-300 dark:bg-gray-600 rounded animate-pulse"></div>
                            <div className="w-16 h-4 bg-gray-300 dark:bg-gray-600 rounded animate-pulse"></div>
                          </div>
                          <div>
                            <div className="w-32 h-4 bg-gray-300 dark:bg-gray-600 rounded animate-pulse mb-1"></div>
                            <div className="w-48 h-3 bg-gray-300 dark:bg-gray-600 rounded animate-pulse"></div>
                          </div>
                        </div>
                        <div className="w-6 h-6 bg-gray-300 dark:bg-gray-600 rounded animate-pulse"></div>
                      </div>
                    ))}
                  </div>
                ) : mcpServers.length === 0 ? (
                  <div className="text-center py-8 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>
                    <p className="text-gray-500 dark:text-gray-400">No MCP servers connected yet</p>
                    <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">Add your first server above to get started</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {mcpServers.map((server) => (
                      <div key={server.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            <input type="checkbox" checked={enabledServers.has(server.id)} onChange={() => toggleServerStatus(server.id)} className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600" />
                            <span className={`text-sm font_medium ${enabledServers.has(server.id) ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}`}>{enabledServers.has(server.id) ? 'Enabled' : 'Disabled'}</span>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 dark:text-gray-100">{server.name}</h4>
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">{server.config?.url || 'No URL'}</p>
                          </div>
                        </div>
                        <button onClick={() => deleteMCPServer(server.id)} className="text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors p-1" title="Delete server">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Available Tools ({mcpTools.filter((t: any) => enabledServers.has(t.server_id)).length}) {isLoadingMCPTools && <span className="text-blue-400">(Refreshing...)</span>}</h3>
                {isLoadingMCPTools ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                        <div className="w-32 h-4 bg-gray-300 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
                        <div className="w-48 h-3 bg-gray-300 dark:bg-gray-600 rounded animate-pulse"></div>
                      </div>
                    ))}
                  </div>
                ) : mcpTools.length === 0 ? (
                  <div className="text-center py-8 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                    <p className="text-gray-500 dark:text-gray-400">No tools available</p>
                    <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">Enable MCP servers to see available tools</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {mcpTools.filter((t: any) => enabledServers.has(t.server_id)).map((tool: any) => (
                      <div key={tool.name} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                        <h4 className="font-medium text-gray-900 dark:text-gray-100 text-sm">{tool.name}</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{tool.description || 'No description'}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main area prompting selection */}
      <main className="flex-1 ml-64 min-h-screen flex items-center justify-center p-4">
        <div className="max-w-2xl w-full text-center">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-8 shadow-sm">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Select or start a chat</h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">Choose a conversation from the sidebar or start a new chat to begin.</p>
            <div className="flex items-center justify-center gap-3">
              <button onClick={() => setShowSearchModal(true)} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200">Search chats</button>
              <button onClick={async () => {
                try {
                  const created = await apiCall('/chat/chats', { method: 'POST', body: JSON.stringify({ title: 'New Chat' }) });
                  router.push(`/chat/${created.hash}`);
                } catch (e: any) {
                  alert(e.message || 'Failed to create chat');
                }
              }} className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white">New chat</button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}


