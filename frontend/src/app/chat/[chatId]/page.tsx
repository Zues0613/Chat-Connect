"use client";

import { useEffect, useRef, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { LoaderOne } from '../../../components/ui/loader';
import { getAuthToken, clearAuthToken } from '../../../utils/cookies';
import MarkdownRenderer from '../../../components/MarkdownRenderer';

// Performance optimizations:
// - Cache loaded data to prevent unnecessary API calls
// - Only fetch chats, MCP data, and user info once per session
// - Use force parameter for manual refreshes
// - Reduce redundant fetchChats() calls in delete operations
// - Progressive loading: Show UI immediately, load data in background

// Hide scrollbar visuals while keeping scroll behavior (match base UI)
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    .scrollbar-hide::-webkit-scrollbar { display: none; }
    .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
  `;
  document.head.appendChild(style);
}

interface Chat {
  id: number;
  title: string;
  createdAt: string;
  updatedAt: string;
  hash: string;
}

interface Message {
  id: number;
  content: string;
  role: string;
  createdAt: string;
}

export default function ChatIndexPage() {
  const router = useRouter();
  const params = useParams();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showHideBtn, setShowHideBtn] = useState(false);
  
  const [isLoading, setIsLoading] = useState(false); // Show UI immediately, load data progressively
  const [error, setError] = useState<string | null>(null);

  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(false);
  const [chatsLoaded, setChatsLoaded] = useState(false); // Track if chats have been loaded once
  const [initialLoadComplete, setInitialLoadComplete] = useState(false); // Track initial page load

  const [showSearchModal, setShowSearchModal] = useState(false);
  const [modalSearch, setModalSearch] = useState("");

  const [showMCPServerModal, setShowMCPServerModal] = useState(false);
  const [mcpServers, setMcpServers] = useState<any[]>([]);
  const [mcpTools, setMcpTools] = useState<any[]>([]);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<{ id: number; title: string } | null>(null);
  const [isLoadingMCPServers, setIsLoadingMCPServers] = useState(false);
  const [isLoadingMCPTools, setIsLoadingMCPTools] = useState(false);
  const [mcpDataLoaded, setMcpDataLoaded] = useState(false); // Track if MCP data has been loaded once
  const [isRefreshingMCP, setIsRefreshingMCP] = useState(false);
  const [isFixingRoles, setIsFixingRoles] = useState(false);

  const [newServerUrl, setNewServerUrl] = useState("");
  const [newServerName, setNewServerName] = useState("");
  const [isAddingServer, setIsAddingServer] = useState(false);

  const [user, setUser] = useState<{ name: string; email: string }>({ name: '', email: '' });
  const [isLoadingUser, setIsLoadingUser] = useState(false);
  const [userDataLoaded, setUserDataLoaded] = useState(false); // Track if user data has been loaded once

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

  // Dynamic chat data
  const [chat, setChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [isAITyping, setIsAITyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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

  // Safe call for non-essential background fetches
  const apiCallSafe = async (endpoint: string, options: RequestInit = {}, timeoutMs: number = 8000) => {
    try {
      return await apiCall(endpoint, options, timeoutMs);
    } catch (_e) {
      return null;
    }
  };

  const fetchChats = async (force = false) => {
    // Only fetch if not already loaded or if forced
    if (!force && chatsLoaded && chats.length > 0) {
      console.log('Chats already loaded, skipping fetch');
      return;
    }

    try {
      setIsLoadingChats(true);
      const response = await apiCall('/chat/chats');
      console.log('Fetched chats:', response);
      setChats(response);
      setChatsLoaded(true); // Mark as loaded
    } catch (e) {
      console.error('Failed to fetch chats:', e);
    } finally {
      setIsLoadingChats(false);
    }
  };

  const fetchChatByHash = async (hash: string) => {
    const data = await apiCall(`/chat/chats/hash/${hash}`);
    setChat(data);
  };

  const fetchMessagesByHash = async (hash: string) => {
    try {
      setIsLoadingMessages(true);
      const res = await apiCall(`/chat/chats/hash/${hash}/messages`);
      setMessages(Array.isArray(res) ? res : []);
    } catch (e) {
      console.error('Failed to fetch messages:', e);
      setMessages([]);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const fetchMCPServers = async (force = false) => {
    // Only fetch if not already loaded or if forced
    if (!force && mcpDataLoaded && mcpServers.length >= 0) {
      console.log('MCP servers already loaded, skipping fetch');
      return;
    }

    try {
      setIsLoadingMCPServers(true);
      const data = await apiCallSafe("/auth/mcp-servers");
      const servers = Array.isArray(data) ? data : [];
      setMcpServers(servers);
      setMcpDataLoaded(true); // Mark as loaded
      
      if (enabledServers.size === 0 && servers.length > 0) {
        const serverIds = servers.map(server => server.id);
        setEnabledServers(new Set(serverIds));
        localStorage.setItem('enabledServers', JSON.stringify(serverIds));
      }
    } catch (_e) {
      setMcpServers([]);
    } finally {
      setIsLoadingMCPServers(false);
    }
  };

  const fetchMCPTools = async (force = false) => {
    // Only fetch if not already loaded or if forced
    if (!force && mcpDataLoaded && mcpTools.length >= 0) {
      console.log('MCP tools already loaded, skipping fetch');
      return;
    }

    try {
      setIsLoadingMCPTools(true);
      const data = await apiCallSafe("/chat/mcp/tools");
      setMcpTools((data && data.tools) || []);
      setMcpDataLoaded(true); // Mark as loaded
    } catch (_e) {
      setMcpTools([]);
    } finally {
      setIsLoadingMCPTools(false);
    }
  };

  const fetchUserInfo = async (force = false) => {
    // Only fetch if not already loaded or if forced
    if (!force && userDataLoaded && (user.name || user.email)) {
      console.log('User data already loaded, skipping fetch');
      return;
    }

    try {
      setIsLoadingUser(true);
      const data = await apiCallSafe('/auth/me');
      if (data) {
      setUser({ name: data.name || '', email: data.email || '' });
        setUserDataLoaded(true); // Mark as loaded
      }
    } catch (_e) {
    } finally {
      setIsLoadingUser(false);
    }
  };

  const handleRefreshMCP = async () => {
    if (isRefreshingMCP) return;
    try {
      setIsRefreshingMCP(true);
      // Force refresh MCP data
      await Promise.all([
        fetchMCPServers(true),
        fetchMCPTools(true)
      ]);
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

  // Delete chat functionality (matches base UI behavior)
  const deleteChat = async (chatId: number) => {
    if (!confirm('Delete this chat? This cannot be undone.')) return;
    try {
      await apiCall(`/chat/chats/${chatId}`, { method: 'DELETE' });
      await fetchChats();
      // If current chat was deleted, navigate home
      if (chat && chat.id === chatId) {
        router.push('/');
      }
    } catch (e: any) {
      alert(e.message || 'Failed to delete chat');
    }
  };

  const handleDeleteChat = async (chatId: number, chatTitle: string) => {
    // Validate chat ID
    if (!chatId || isNaN(chatId) || chatId <= 0) {
      console.error('Invalid chat ID:', chatId);
      alert('Invalid chat ID. Cannot delete this chat.');
      return;
    }

    console.log('Opening delete modal for chat:', { id: chatId, title: chatTitle });
    setChatToDelete({ id: chatId, title: chatTitle });
    setShowDeleteModal(true);
  };
  
  const confirmDeleteChat = async () => {
    if (!chatToDelete) {
      console.error('No chat to delete');
      return;
    }

    // Additional validation
    if (!chatToDelete.id || isNaN(chatToDelete.id) || chatToDelete.id <= 0) {
      console.error('Invalid chat ID in chatToDelete:', chatToDelete);
      alert('Invalid chat data. Please refresh and try again.');
      return;
    }

    console.log('Attempting to delete chat:', chatToDelete);

    try {
      // First, verify the chat still exists in our local state
      const chatExists = chats.find(c => c.id === chatToDelete.id);
      if (!chatExists) {
        console.log('Chat not found in local state, may have already been deleted');
        // Force refresh the chat list to get current state
        await fetchChats(true);
        return;
      }

      console.log('Making delete API call for chat ID:', chatToDelete.id);
      const response = await apiCall(`/chat/chats/${chatToDelete.id}`, {
        method: 'DELETE'
      });

      console.log('Delete response:', response);

      // Remove the chat from the list locally
      setChats(chats.filter(chat => chat.id !== chatToDelete.id));

      // If this was the currently selected chat, navigate to home
      if (chat && chat.id === chatToDelete.id) {
        router.push('/');
      }

      console.log('Chat deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete chat:', error);
      console.error('Error details:', {
        message: error.message,
        status: error.status,
        stack: error.stack
      });

      // Check if it's a 404 error (chat not found)
      if (error.message.includes('404') || error.message.includes('Chat not found')) {
        console.log('Chat not found - refreshing chat list');
        alert('Chat not found. It may have already been deleted.');
        // Refresh the chat list to reflect current state
        await fetchChats();
      } else {
        console.error('Unexpected error during chat deletion:', error.message);
        alert(`Failed to delete chat: ${error.message}`);
      }
    } finally {
      setShowDeleteModal(false);
      setChatToDelete(null);
      // Only refresh if there was an error to ensure consistency
      // Successful deletions already updated local state
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    router.push('/login');
  };

  // Load chats and dynamic chat - parallelize core and sidebar fetches
  useEffect(() => {
    const init = async () => {
      try {
        setError(null);
        const chatHash = params?.chatId as string | undefined;
        const decoded = chatHash ? decodeURIComponent(chatHash) : undefined;

        const corePromises: Promise<any>[] = [];
        const bgPromises: Promise<any>[] = [];

        // Core: chat + messages (if hash present)
        if (decoded) {
          corePromises.push(fetchChatByHash(decoded));
          corePromises.push(fetchMessagesByHash(decoded));
        }

        // Parallel: chats list
        bgPromises.push(fetchChats());
        // Parallel: sidebar data
        bgPromises.push(Promise.allSettled([
          fetchMCPServers(),
          fetchMCPTools(),
          fetchUserInfo(),
        ]));

        // Wait only for core (chat/messages) before marking ready
        await Promise.all(corePromises);
        setInitialLoadComplete(true);
        // Let background continue
        Promise.allSettled(bgPromises);
      } catch (e: any) {
        setError(e.message || 'Failed to load');
        setInitialLoadComplete(true);
      }
    };

    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, 120);
    textarea.style.height = `${newHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > 120 ? 'auto' : 'hidden';
  }, [chatInput]);

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAITyping]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || !chat) return;

    const userMessage = {
      id: Date.now(),
      content: message,
      role: 'user' as const,
      createdAt: new Date().toISOString(),
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setChatInput("");

    // Show AI thinking indicator
    setIsAITyping(true);

    try {
      // Use the non-streaming endpoint to get complete response
      const response = await fetch(`/api/chat/chats/${chat.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify({ content: message }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`API Error - Status: ${response.status}, Body: ${errorText}`);
        let detail: string | undefined;
        try {
          const errorJson = JSON.parse(errorText);
          detail = errorJson.detail;
        } catch {}
        const message = detail || errorText || 'Unknown error';
        throw new Error(`HTTP ${response.status}: ${message}`);
      }

      const responseData = await response.json();
      
      // Create assistant message with complete content
      const assistantMessage = {
        id: responseData.assistant_message.id,
        content: responseData.assistant_message.content,
        role: 'assistant' as const,
        createdAt: responseData.assistant_message.createdAt,
      };

      // Add assistant message to state
      setMessages(prev => [...prev, assistantMessage]);

      // Start typewriter effect
      startTypewriterEffect(assistantMessage.content, assistantMessage.id);

    } catch (error) {
      console.error('Error sending message:', error);
      
      // Show error message
      const errorMessage = {
        id: Date.now(),
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        role: 'assistant' as const,
        createdAt: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAITyping(false);
    }
  };

  const startTypewriterEffect = (fullContent: string, messageId: number) => {
    console.log('Starting typewriter effect for:', { fullContent: fullContent.substring(0, 100) + '...', messageId });
    
    // Start with empty content
    setMessages(prev => {
      console.log('Setting initial empty content for message:', messageId);
      return prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, content: '' }
          : msg
      );
    });

    let currentIndex = 0;
    const chunkSize = 3; // Characters to reveal at once
    
    const revealNextChunk = () => {
      if (currentIndex >= fullContent.length) {
        console.log('Typewriter effect complete');
        // Typewriter effect complete
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, content: fullContent }
            : msg
        ));
        return;
      }

      const nextChunk = fullContent.slice(currentIndex, currentIndex + chunkSize);
      currentIndex += chunkSize;

      // Update the message content progressively
      setMessages(prev => {
        const newContent = fullContent.slice(0, currentIndex);
        console.log('Updating message content:', { messageId, currentIndex, newContent: newContent.substring(0, 50) + '...' });
        return prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, content: newContent }
            : msg
      );
      });

      // Schedule next chunk
      setTimeout(revealNextChunk, 20); // 20ms delay between chunks
    };

    // Start the typewriter effect
    revealNextChunk();
  };

  const modalFilteredChats = chats.filter((c) => c.title.toLowerCase().includes(modalSearch.toLowerCase()));

  // Remove full-screen loading - show UI immediately and load data progressively

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
      {sidebarOpen && (
      <aside className="fixed left-0 top-0 z-40 flex flex-col w-64 h-screen backdrop-blur-xl bg-white/10 dark:bg-black/20 border-r border-white/20 dark:border-gray-800/50 px-3 py-4 shadow-2xl"
        style={{ background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)', boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)' }}
          onMouseMove={e => {
          const sidebar = e.currentTarget as HTMLElement;
          // @ts-ignore - offsetX available on MouseEvent
          const x = (e as any).nativeEvent ? (e as any).nativeEvent.offsetX : 0;
            setShowHideBtn(x > sidebar.offsetWidth - 32);
          }}
          onMouseLeave={() => setShowHideBtn(false)}
        >
          <div className="flex items-center justify-between mb-4">
            <img src="/favicon.ico" alt="Vee" className="h-7 w-7 rounded" />
            <div className="flex items-center gap-2">
            <button
              className="p-2 rounded-lg backdrop-blur-md bg-white/20 dark:bg-black/30 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center border border-white/20 dark:border-gray-700/50"
              onClick={() => setSidebarOpen(false)}
              title="Close sidebar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            </div>
          </div>

        {/* New Chat */}
          <button 
            onClick={() => router.push('/')}
          className="flex items-center gap-2 backdrop-blur-md bg-white/30 dark:bg-white/20 text-black dark:text-white font-semibold rounded-lg px-4 py-2 mb-3 hover:bg-white/40 dark:hover:bg_white/30 transition-all border border-white/30 dark:border-white/20 shadow-lg"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            New Chat
          </button>

        {/* Search */}
          <button 
            onClick={() => setShowSearchModal(true)}
            className="flex items-center gap-2 w-full text-white dark:text-gray-200 font-medium rounded-lg px-3 py-2 mb-2 backdrop-blur-md bg-black/30 dark:bg-black/40 hover:bg-black/40 dark:hover:bg-black/50 transition-all border border-white/20 dark:border-gray-700/50"
            style={{ cursor: 'pointer' }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" /></svg>
            🔍 Search Chats
          </button>
          
        {/* MCP Servers */}
          <button 
            onClick={() => { setShowMCPServerModal(true); handleRefreshMCP(); }}
            className="flex items-center justify-between w-full text-white dark:text-gray-200 font-medium rounded-lg px-3 py-2 mb-2 backdrop-blur-md bg-blue-600/80 dark:bg-blue-700/80 hover:bg-blue-700/90 dark:hover:bg-blue-800/90 transition-all border border-blue-400/30 dark:border-blue-500/30 shadow-lg"
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
              <div className="space-y-2 px-2 py-2">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="flex items-center gap-2 px-2 py-2 rounded-lg">
                    <div className="w-4 h-4 rounded bg-white/20 dark:bg-gray-700 animate-pulse" />
                    <div className="h-3 w-40 rounded bg-white/20 dark:bg-gray-700 animate-pulse" />
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
                <button
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-red-600/10 text-red-500 hover:text-red-600"
                  title="Delete chat"
                  onClick={(e) => { e.stopPropagation(); handleDeleteChat(c.id, c.title); }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
                </div>
              ))
            )}
          </div>

        {/* Settings (below chat list, above user info) */}
        <button 
          onClick={() => router.push('/settings')}
          className="flex items-center gap-2 px-3 py-2 rounded backdrop-blur-md hover:bg-black/40 dark:hover:bg-black/50 text-white font-medium mb-1 transition-all border border-white/20 dark:border-gray-700/50"
          title="Settings"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0a1.724 1.724 0 002.573 1.01c.797-.46 1.757.388 1.3 1.2a1.724 1.724 0 00.457 2.573c.921.3.921 1.603 0 1.902a1.724 1.724 0 00-1.01 2.573c.46.797-.388 1.757-1.2 1.3a1.724 1.724 0 00-2.573.457c-.3.921-1.603.921-1.902 0a1.724 1.724 0 00-2.573-1.01c-.797.46-1.757-.388-1.3-1.2a1.724 1.724 0 00-.457-2.573c-.921-.3-.921-1.603 0-1.902a1.724 1.724 0 001.01-2.573c-.46-.797.388-1.757 1.2-1.3a1.724 1.724 0 002.573-.457z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          Settings
        </button>

        {/* User info */}
          <div className="mt-auto pt-4 border-t border-white/20 dark:border-gray-800/50">
            <div className="px-2 py-3">
              {isLoadingUser ? (
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-white/20 dark:bg-gray-700 animate-pulse" />
                  <div className="flex flex-col flex-1 gap-1">
                    <div className="w-28 h-3 rounded bg-white/20 dark:bg-gray-700 animate-pulse" />
                    <div className="w-36 h-2 rounded bg-white/10 dark:bg-gray-800 animate-pulse" />
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
      )}

      {/* Mini rail when sidebar is closed */}
      {!sidebarOpen && (
        <div className="fixed left-0 top-0 z-30 h-screen w-16 backdrop-blur-xl bg-white/10 dark:bg-black/20 border-r border-white/20 dark:border-gray-800/50 flex flex-col items-center py-4 gap-6 shadow-2xl"
          style={{ background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)', boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)' }}>
          {/* Favicon */}
          <img src="/favicon.ico" alt="Vee" className="h-7 w-7 rounded mb-2" />
          {/* New Chat Icon */}
            <button
            onClick={() => router.push('/')}
            className="p-2 rounded-lg backdrop-blur-md bg-white/20 dark:bg-black/30 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center border border-white/20 dark:border-gray-700/50 shadow-lg"
            title="New Chat"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            </button>
          {/* Search Icon */}
          <button 
            onClick={() => setShowSearchModal(true)}
            className="p-2 rounded-lg backdrop-blur-md bg-white/20 dark:bg-black/30 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center border border-white/20 dark:border-gray-700/50 shadow-lg" 
            title="Search Chats"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" /></svg>
          </button>
          {/* MCP Servers Icon */}
          <button 
            onClick={() => { setShowMCPServerModal(true); handleRefreshMCP(); }}
            className="p-2 rounded-lg backdrop-blur-md bg-white/20 dark:bg-black/30 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center border border-white/20 dark:border-gray-700/50 shadow-lg" 
            title="MCP Servers"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>
          </button>
          {/* Spacer */}
          <div className="flex-1" />
          {/* Settings Icon */}
          <button 
            onClick={() => router.push('/settings')}
            className="p-2 rounded-lg backdrop-blur-md bg-white/20 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center mb-2 border border-white/20 dark:border-gray-700/50 shadow-lg" 
            title="Settings"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="12" cy="8" r="4" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 20v-2a6 6 0 0112 0v2" /></svg>
          </button>
          {/* Show sidebar */}
          <button 
            onClick={() => setSidebarOpen(true)}
            className="absolute right-0 top-1/2 px-3 py-2 rounded-l-lg backdrop-blur-md bg-black/30 dark:bg-black/40 text-white dark:text-gray-200 hover:bg-black/40 dark:hover:bg-black/50 transition-all flex items-center gap-1 border border-white/20 dark:border-gray-700/50" 
            style={{ transform: 'translateY(-50%)' }}
            title="Show sidebar"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
          </button>
        </div>
      )}

      {/* Search Modal */}
      {showSearchModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 dark:bg-black/30 backdrop-blur-2xl" onClick={(e) => { if (e.target === e.currentTarget) { setShowSearchModal(false); setModalSearch(''); }}}>
          <div className="backdrop-blur-xl bg-white/20 dark:bg-black/30 rounded-lg shadow-xl w-full max-w-md mx-4 max-h-[80vh] flex flex-col border border-white/30 dark:border-gray-700/50">
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 dark:bg-black/30 backdrop-blur-2xl" onClick={(e) => { if (e.target === e.currentTarget) setShowMCPServerModal(false); }}>
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
                {/* Popular Platforms */}
                <div className="mb-4 p-3 bg-blue-800/20 rounded-lg">
                  <h4 className="text-sm font-medium text-blue-200 mb-2">Popular MCP Server Sources:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-blue-300">
                    <div>• <strong>Pipedream:</strong> Workflow endpoints</div>
                    <div>• <strong>GitHub:</strong> Repository integrations</div>
                    <div>• <strong>Custom APIs:</strong> Your own MCP servers</div>
                    <div>• <strong>File System:</strong> Local file access</div>
                  </div>
                </div>
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
      <main className={`flex-1 min-h-screen relative ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
          {/* Removed top subtle loading bar */}
          <div className="w-full h-full flex flex-col">
            <div className="flex-1 overflow-y-auto px-4 py-8 pb-40">
              <div className="max-w-3xl mx-auto space-y-6">
              {isLoadingMessages ? (
                <div className="flex items-center justify-center py-6 min-h-[50vh]">
                  <LoaderOne size="md" />
                  <span className="ml-2 text-sm text-blue-400">Loading messages…</span>
                </div>
              ) : messages.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-gray-500 mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                    </div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">No Messages Yet</h2>
                  <p className="text-gray-600 dark:text-gray-400">This chat doesn't have any messages yet.</p>
                  </div>
                ) : (
                messages.map((message) => {
                  console.log('Rendering message:', { id: message.id, role: message.role, content: message.content.substring(0, 50) + '...' });
                  return (
                    <div key={message.id}>
                      {message.role === 'user' ? (
                        <div className="flex w-full justify-end">
                          <div className="relative group max-w-[70%] rounded-2xl px-5 py-4 bg-blue-500 text-white ml-12 shadow-lg">
                          <div className="whitespace-pre-wrap break-words text-lg leading-relaxed">{message.content}</div>
                          </div>
                        </div>
                      ) : (
                        <div className="w-full">
                          <div className="relative group">
                            <MarkdownRenderer 
                            content={message.content}
                              className="prose prose-gray dark:prose-invert max-w-none text-lg leading-relaxed markdown-content"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })
                )}
                <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Chatbox fixed at bottom */}
          <div className={`fixed bottom-0 ${sidebarOpen ? 'left-64' : 'left-16'} right-0 flex flex-col items-center justify-end z-30 transition-all duration-300`} style={{ pointerEvents: 'none' }}>
            <div className="relative w-full flex flex-col items-center mb-6 px-4 transition-all duration-300 max-w-4xl" style={{ pointerEvents: 'auto' }}>
              <div className="flex flex-col rounded-xl backdrop-blur-xl bg-white/10 dark:bg-black/20 border border-white/20 dark:border-gray-700/50 overflow-hidden w-full shadow-2xl" style={{ position: 'relative', minHeight: 80 }}>
                {/* Input area: auto-expand vertically, only top expands, up to 5 lines */}
                <div className="px-3 pt-3 pb-0 gap-2" style={{ flex: 1, paddingBottom: 56, minHeight: 44 }}>
                  <div className="flex-1 flex items-center relative">
                    <textarea
                      ref={textareaRef}
                      className="bg-transparent border-none outline-none px-2 py-2 text-base text-gray-1000 dark:text-gray-100 resize-none min-h-[44px] rounded-md w-full transition-all"
                      placeholder={isAITyping ? "AI is thinking..." : "Ask anything"}
                      value={chatInput}
                      onChange={(e) => {
                        setChatInput(e.target.value);
                        // Reset height when input is cleared
                        if (!e.target.value && textareaRef.current) {
                          textareaRef.current.style.height = 'auto';
                        }
                      }}
                      rows={1}
                      style={{
                        overflowX: 'auto',
                        minWidth: '120px',
                        maxWidth: '100%',
                        width: '100%',
                        minHeight: '44px',
                        maxHeight: '120px',
                        transition: 'height 0.2s ease-out',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        marginBottom: 0,
                        lineHeight: '1.5',
                        fontFamily: 'inherit',
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          if (chatInput.trim() && !isAITyping) {
                            handleSendMessage(chatInput);
                          }
                        }
                      }}
                      disabled={isAITyping}
                    />
                  </div>
                </div>
                {/* Tools bar fixed at bottom of chatbox */}
                <div className="flex items-center justify-between px-3 py-2 border-t border-white/20 dark:border-gray-700/50 w-full bg-white/5 backdrop-blur-sm" style={{ position: 'absolute', left: 0, right: 0, bottom: 0, borderRadius: '0 0 12px 12px' }}>
                  {/* + icon */}
                  {/* + icon on left */}
                  <button
                    type="button"
                    className="flex items-center justify-center p-2 rounded-full backdrop-blur-xl bg-white/40 dark:bg-black/50 border border-white/40 dark:border-gray-600/50 shadow-2xl hover:shadow-[0_0_25px_rgba(255,255,255,0.3)] hover:bg-white/50 dark:hover:bg-black/60 transition-all duration-300"
                    title="Tools"
                    tabIndex={0}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-700 dark:text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                  </button>
                  {/* Model selector dropdown in center */}
                  <div className="flex-1 flex justify-center relative">
                    {isAITyping && (
                      <span className="absolute -top-8 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs text-blue-200 bg-blue-500/20 border border-blue-400/30 shadow-sm animate-pulse">
                        AI is thinking…
                      </span>
                    )}
                    <span
                      className="flex items-center gap-1 cursor-pointer text-gray-700 dark:text-gray-200 font-semibold px-2 py-1 rounded backdrop-blur-2xl hover:bg-white/40 dark:hover:bg-black/50 transition-all border border-white/30 dark:border-gray-600/50 shadow-lg hover:shadow-xl"
                      onClick={() => {}} // showModelDropdown state removed
                      aria-haspopup="listbox"
                      aria-expanded={false} // showModelDropdown state removed
                      tabIndex={0}
                      role="button"
                    >
                      DeepSeek R1
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                    </span>
                    {/* showModelDropdown state removed */}
                  </div>
                  {/* Send / Stop on right */}
                  {isAITyping ? (
                    <button
                      type="button"
                      className="flex items-center justify-center rounded-full w-9 h-9 shadow-2xl hover:shadow-[0_0_25px_rgba(239,68,68,0.5)] border bg-red-500/90 border-red-400/50 hover:bg-red-600/90 hover:scale-105 text-white transition-all backdrop-blur-xl"
                      title="Stop"
                      tabIndex={0}
                      onClick={() => {}}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><rect x="6" y="6" width="8" height="8" rx="1" /></svg>
                    </button>
                  ) : (
                  <button
                    type="button"
                    className={`flex items-center justify-center rounded-full w-9 h-9 shadow-2xl hover:shadow-[0_0_25px_rgba(59,130,246,0.5)] border transition-all backdrop-blur-xl ${
                        chatInput.trim()
                        ? 'bg-blue-500/90 border-blue-400/50 hover:bg-blue-600/90 hover:scale-105' 
                        : 'bg-white/40 dark:bg-black/50 border-white/40 dark:border-gray-600/50 hover:bg-white/50 dark:hover:bg-black/60 hover:scale-105'
                    }`}
                    title="Send"
                    tabIndex={0}
                    onClick={() => {
                        if (chatInput.trim()) {
                        handleSendMessage(chatInput);
                      }
                    }}
                      disabled={!chatInput.trim()}
                  >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke={chatInput.trim() ? 'white' : 'currentColor'}>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </button>
                  )}
                </div>
              </div>
            </div>
          </div>
      </div>
        </main>

        {/* Delete Chat Confirmation Modal */}
        {showDeleteModal && chatToDelete && (
          <div 
            className="fixed inset-0 bg-black/40 dark:bg-black/60 flex items-center justify-center z-[99999] backdrop-blur-xl"
            onClick={() => setShowDeleteModal(false)}
    >
      <div 
              className="backdrop-blur-xl bg-white/20 dark:bg-black/40 rounded-xl shadow-2xl w-full max-w-md mx-4 flex flex-col border border-white/30 dark:border-gray-700/50"
        onClick={(e) => e.stopPropagation()}
      >
              {/* Modal Header */}
              <div className="flex items-center justify-between p-4 border-b border-white/20 dark:border-gray-700/50">
                <h2 className="text-lg font-semibold text-white dark:text-gray-100">Delete Chat</h2>
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="text-gray-400 hover:text-gray-200 dark:hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-800"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
          </button>
        </div>

              {/* Modal Content */}
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
        </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      Delete "{chatToDelete?.title}"?
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      This action cannot be undone and will permanently delete all messages in this chat.
                    </p>
        </div>
      </div>

                {/* Action Buttons */}
                <div className="flex gap-3 justify-end">
                  <button
                    onClick={() => setShowDeleteModal(false)}
                    className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmDeleteChat}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
                  >
                    Delete Chat
                  </button>
    </div>
              </div>
            </div>
          </div>
        )}
      </div>
  );
} 



