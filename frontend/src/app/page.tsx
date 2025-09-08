"use client";
import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { getAuthToken, clearAuthToken, getCookie, setAuthToken } from "../utils/cookies";
import { useSession } from "../hooks/useSession";
import MarkdownRenderer from "../components/MarkdownRenderer";
// Hash-based URLs - no encryption needed

// Add custom CSS for animations
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    
    .slide-up {
      animation: slideUp 0.5s ease-out;
    }
    
    .fade-in {
      animation: fadeIn 0.3s ease-out;
    }
    
    /* Custom scrollbar styling for textarea */
    textarea::-webkit-scrollbar {
      width: 8px;
    }
    textarea::-webkit-scrollbar-track {
      background: transparent;
    }
    textarea::-webkit-scrollbar-thumb {
      background: #cbd5e0;
      border-radius: 4px;
    }
    textarea::-webkit-scrollbar-thumb:hover {
      background: #a0aec0;
    }
    .dark textarea::-webkit-scrollbar-thumb {
      background: #4a5568;
    }
    .dark textarea::-webkit-scrollbar-thumb:hover {
      background: #718096;
    }
    
    /* Glass morphism effects */
    .glass-morphism {
      backdrop-filter: blur(16px) saturate(180%);
      -webkit-backdrop-filter: blur(16px) saturate(180%);
      background-color: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.125);
    }
    
    .glass-morphism-dark {
      backdrop-filter: blur(16px) saturate(180%);
      -webkit-backdrop-filter: blur(16px) saturate(180%);
      background-color: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.125);
    }
    
    /* Enhanced glass morphism for interactive elements */
    .glass-morphism-interactive {
      backdrop-filter: blur(20px) saturate(200%);
      -webkit-backdrop-filter: blur(20px) saturate(200%);
      background-color: rgba(255, 255, 255, 0.15);
      border: 1px solid rgba(255, 255, 255, 0.2);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-morphism-interactive:hover {
      backdrop-filter: blur(24px) saturate(220%);
      -webkit-backdrop-filter: blur(24px) saturate(220%);
      background-color: rgba(255, 255, 255, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.3);
      transform: translateY(-2px);
    }
    
    /* Hide scrollbar but keep functionality */
    .scrollbar-hide {
      -ms-overflow-style: none;  /* Internet Explorer 10+ */
      scrollbar-width: none;  /* Firefox */
    }
    .scrollbar-hide::-webkit-scrollbar {
      display: none;  /* Safari and Chrome */
    }
    
    /* Custom markdown content styling */
    .markdown-content {
      font-size: 18px;
      line-height: 1.7;
    }
    
    .markdown-content h1 {
      font-size: 2.25rem;
      margin-top: 2em;
      margin-bottom: 0.75em;
      font-weight: 700;
    }
    
    .markdown-content h2 {
      font-size: 1.875rem;
      margin-top: 1.75em;
      margin-bottom: 0.75em;
      font-weight: 600;
    }
    
    .markdown-content h3 {
      font-size: 1.5rem;
      margin-top: 1.5em;
      margin-bottom: 0.5em;
      font-weight: 600;
    }
    
    .markdown-content h4 {
      font-size: 1.25rem;
      margin-top: 1.5em;
      margin-bottom: 0.5em;
      font-weight: 600;
    }
    
    .markdown-content p {
      margin-bottom: 1.2em;
      font-size: 18px;
    }
    
    .markdown-content ul,
    .markdown-content ol {
      margin-bottom: 1.2em;
      padding-left: 1.8em;
    }
    
    .markdown-content li {
      margin-bottom: 0.4em;
      font-size: 18px;
    }
    
    .markdown-content blockquote {
      margin: 1.8em 0;
      padding: 1.2em;
      border-left: 4px solid #3b82f6;
      background-color: rgba(59, 130, 246, 0.05);
      font-size: 18px;
    }
    
    .dark .markdown-content blockquote {
      background-color: rgba(59, 130, 246, 0.1);
    }
    
    /* Line clamp utility for tool descriptions */
    .line-clamp-2 {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
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

interface MCPServer {
  id: number;
  name: string;
  description?: string;
  config: any;
  createdAt: string;
}

const promptCards = [
  {
    title: "Send Email",
    description: "Compose and send emails using Gmail integration.",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
    ),
  },
  {
    title: "MCP Setup",
    description: "Learn how to configure MCP servers and tools.",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573.457c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
    ),
  },
  {
    title: "OAuth Guide",
    description: "Set up OAuth authentication for your MCP servers.",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
    ),
  },
];

// Custom hook for auto-resizing textarea
const useAutoResizeTextarea = (value: string, maxHeight: number = 120) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    // Calculate new height
    const scrollHeight = textarea.scrollHeight;
    const newHeight = Math.min(scrollHeight, maxHeight);
    
    // Set the new height
    textarea.style.height = `${newHeight}px`;
    
    // Add scrollbar if content exceeds max height
    if (scrollHeight > maxHeight) {
      textarea.style.overflowY = 'auto';
    } else {
      textarea.style.overflowY = 'hidden';
    }
  }, [value, maxHeight]);

  return textareaRef;
};

export default function Home() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showHideBtn, setShowHideBtn] = useState(false);
  const [user, setUser] = useState<{ name: string; email: string }>({ name: '', email: '' });
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingChats, setIsLoadingChats] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isPromptCardLoading, setIsPromptCardLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<{ id: number; title: string } | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(false);
  
  // Chat functionality
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState<Array<{id: number, content: string, role: string, createdAt: string}>>([]);
  const [isAITyping, setIsAITyping] = useState(false);
  const [currentRequestController, setCurrentRequestController] = useState<AbortController | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedBaseMessageId, setEditedBaseMessageId] = useState<number | null>(null);
  const [editVersions, setEditVersions] = useState<Record<number, Array<{ user: string; assistant: string }>>>({});
  const [editVersionIndex, setEditVersionIndex] = useState<Record<number, number>>({});
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // Auto-resize textarea hook
  const textareaRef = useAutoResizeTextarea(chatInput, 120);

  // Search modal state
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [modalSearch, setModalSearch] = useState("");

  // MCP Server state
  const [showMCPServerModal, setShowMCPServerModal] = useState(false);
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([]);
  const [mcpTools, setMcpTools] = useState<any[]>([]);
  const [expandedServers, setExpandedServers] = useState<Set<string>>(new Set());
  const [isRefreshingMCP, setIsRefreshingMCP] = useState(false);
  const [isLoadingMCPServers, setIsLoadingMCPServers] = useState(false);
  const [isLoadingMCPTools, setIsLoadingMCPTools] = useState(false);
  const [enabledServers, setEnabledServers] = useState<Set<number>>(() => {
    // Load enabled servers from localStorage on component mount
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('enabledServers');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          return new Set(parsed);
        } catch (e) {
          console.log("[DEBUG] Failed to parse enabled servers from localStorage");
        }
      }
    }
    return new Set();
  });
  const [newServerName, setNewServerName] = useState('');
  const [newServerDescription, setNewServerDescription] = useState('');
  const [newServerUrl, setNewServerUrl] = useState('');
  const [newServerType, setNewServerType] = useState('custom');

  const availableModels = ["DeepSeek R1", "GPT", "Claude"];
  const [selectedModel, setSelectedModel] = useState<string>("DeepSeek R1");

  // Use session management hook
  useSession();

  // Handle URL parameters for chat hash - only on main page
  useEffect(() => {
    if (isLoading || isLoadingMessages) return;
    
    const handleUrlParams = async () => {
      try {
        // Only handle chat URLs if we're on the main page (not on /chat/[id] pages)
        const pathname = window.location.pathname;
        if (pathname !== '/') {
          console.log('Not on main page, skipping URL parameter handling');
          return;
        }
        
        // Check for hash-based URL first (e.g., /chat/chat_abc123)
        const hashMatch = pathname.match(/^\/chat\/(.+)$/);
        
        if (hashMatch) {
          const chatHash = hashMatch[1];
          console.log('Found chat hash in URL path:', chatHash);
          
          // Find chat by hash in the chat list
          const chatByHash = chats.find(chat => chat.hash === chatHash);
          
          if (chatByHash) {
            console.log('Found chat by hash:', chatByHash.id);
            // Only update if not already selected
            if (selectedChatId !== chatByHash.id.toString()) {
              setSelectedChatId(chatByHash.id.toString());
              setCurrentChatId(chatByHash.id);
              await fetchMessages(chatByHash.id);
            }
            return;
          } else {
            console.log('Chat not found by hash, will load when chats are fetched');
            // Store the hash to load later when chats are available
            setSelectedChatId(chatHash);
          }
        } else {
          // Fallback to query parameter (for backward compatibility)
          const urlParams = new URLSearchParams(window.location.search);
          const chatHashFromUrl = urlParams.get('chatHash');
          
          if (chatHashFromUrl) {
            console.log('Found chat hash in query param:', chatHashFromUrl);
            
            // Find chat by hash in the chat list
            const chatByHash = chats.find(chat => chat.hash === chatHashFromUrl);
            
            if (chatByHash) {
              console.log('Found chat by hash:', chatByHash.id);
              // Only update if not already selected
              if (selectedChatId !== chatByHash.id.toString()) {
                setSelectedChatId(chatByHash.id.toString());
                setCurrentChatId(chatByHash.id);
                await fetchMessages(chatByHash.id);
              }
              // Update the URL to the clean format
              router.replace(`/chat/${chatHashFromUrl}`);
              return;
            } else {
              console.log('Chat not found by hash, will load when chats are fetched');
              // Store the hash to load later when chats are available
              setSelectedChatId(chatHashFromUrl);
            }
          }
        }
      } catch (error) {
        console.error('Error handling URL parameters:', error);
        // Don't redirect on error, just log it
      }
    };

    handleUrlParams();
  }, [isLoading, isLoadingMessages, chats, selectedChatId]);

  // Additional effect to handle URL when chats are loaded
  useEffect(() => {
    if (isLoading || isLoadingMessages || chats.length === 0) return;
    
    const pathname = window.location.pathname;
    console.log("[DEBUG] Checking URL restoration for pathname:", pathname);
    const hashMatch = pathname.match(/^\/chat\/(.+)$/);
    
    if (hashMatch) {
      const chatHash = hashMatch[1];
      console.log("[DEBUG] Found chat hash in URL:", chatHash);
      const chatByHash = chats.find(chat => chat.hash === chatHash);
      
      if (chatByHash) {
        console.log("[DEBUG] Found matching chat:", chatByHash.id, chatByHash.title);
        if (selectedChatId !== chatByHash.id.toString()) {
          console.log("[DEBUG] Loading chat from URL after chats loaded:", chatByHash.id);
          setSelectedChatId(chatByHash.id.toString());
          setCurrentChatId(chatByHash.id);
          fetchMessages(chatByHash.id);
        } else {
          console.log("[DEBUG] Chat already selected, skipping");
        }
        
        // Clear stored URL since we successfully restored the chat
        const storedUrl = localStorage.getItem('lastChatUrl');
        if (storedUrl === pathname) {
          console.log("[DEBUG] Clearing stored URL since chat was successfully restored");
          localStorage.removeItem('lastChatUrl');
        }
      } else {
        console.log("[DEBUG] Chat not found in chats list for hash:", chatHash);
        console.log("[DEBUG] Available chats:", chats.map(c => ({ id: c.id, hash: c.hash, title: c.title })));
        // If chat not found, but we have a valid hash, keep the URL and show a message
        console.log("[DEBUG] Keeping URL with hash:", chatHash, "for potential future restoration");
      }
    } else {
      console.log("[DEBUG] No chat hash found in URL");
    }
  }, [chats, isLoading, isLoadingMessages]);

  // Additional effect to prevent navigation away from chat URLs
  useEffect(() => {
    const pathname = window.location.pathname;
    const hashMatch = pathname.match(/^\/chat\/(.+)$/);
    
    if (hashMatch && !isLoading) {
      console.log("[DEBUG] Currently on chat URL:", pathname);
      // If we're on a chat URL and not loading, make sure we don't navigate away
      const chatHash = hashMatch[1];
      if (selectedChatId && chats.length > 0) {
        const chatByHash = chats.find(chat => chat.hash === chatHash);
        if (chatByHash && selectedChatId !== chatByHash.id.toString()) {
          console.log("[DEBUG] Restoring chat selection from URL:", chatByHash.id);
          setSelectedChatId(chatByHash.id.toString());
          setCurrentChatId(chatByHash.id);
          fetchMessages(chatByHash.id);
        }
      }
    }
  }, [isLoading, selectedChatId, chats]);



  // Filter chats for search modal
  const modalFilteredChats = chats.filter((chat) =>
    chat.title.toLowerCase().includes(modalSearch.toLowerCase())
  );

  // Handle chat selection from modal
  const handleChatSelect = (chatId: number) => {
    setSelectedChatId(chatId.toString());
    setShowSearchModal(false);
    setModalSearch("");
    // Navigate to hash-based chat URL
    const selectedChat = chats.find(chat => chat.id === chatId);
    if (selectedChat) {
      const hashUrl = `/chat/${selectedChat.hash}`;
      router.push(hashUrl);
    }
  };

  // Close modal when clicking outside
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      setShowSearchModal(false);
      setModalSearch("");
    }
  };

  // Close modal on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (showSearchModal) {
          setShowSearchModal(false);
          setModalSearch("");
        }
        if (showMCPServerModal) {
          setShowMCPServerModal(false);
        }
      }
    };

    if (showSearchModal || showMCPServerModal) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [showSearchModal, showMCPServerModal]);

  const handleSearchClick = () => {
    setShowSearchModal(true);
  };

  // API Functions
  const API_BASE = "/api";

  const apiCall = async (endpoint: string, options: RequestInit = {}, timeoutMs: number = 30000, retries: number = 1) => {
    const token = getAuthToken();
    if (!token) throw new Error("No auth token");
    
    console.log(`Making API call to: ${API_BASE}${endpoint}`);
    console.log("Request options:", options);
    
    // Create AbortController for timeout
    const externalSignal = options.signal as AbortSignal | undefined;
    const controller = externalSignal ? null : new AbortController();
    const timeoutId = setTimeout(() => {
      if (externalSignal) {
        // Cannot abort external signal; rely on caller to handle timeout if needed
      } else {
        controller?.abort();
      }
    }, timeoutMs);
    
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        signal: externalSignal ?? controller?.signal,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          ...options.headers,
        },
      });
      
      clearTimeout(timeoutId);
      
      console.log(`Response status: ${response.status}`);
      console.log(`Response headers:`, Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`API Error - Status: ${response.status}, Body: ${errorText}`);
        // Try to parse JSON error
        let detail: string | undefined = undefined;
        try {
          const parsed = JSON.parse(errorText);
          detail = parsed?.detail || parsed?.error || undefined;
        } catch {}
        const message = detail || errorText || 'Unknown error';
        throw new Error(`HTTP ${response.status}: ${message}`);
      }

      const responseData = await response.json();
      console.log("API Response data:", responseData);
      return responseData;
    } catch (error: any) {
      clearTimeout(timeoutId);
      
      // Retry logic for network errors
      if (retries > 0 && (error.message.includes('Failed to fetch') || error.message.includes('NetworkError') || error.name === 'AbortError')) {
        console.log(`Retrying API call to ${endpoint} (${retries} retries left)`);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
        return apiCall(endpoint, options, timeoutMs, retries - 1);
      }
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - server took too long to respond. Please check if the backend server is running on http://127.0.0.1:8000');
      }
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        throw new Error('Cannot connect to server. Please ensure the backend server is running on http://127.0.0.1:8000');
      }
      throw error;
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;
    
    const userMessage = {
      id: Date.now(),
      content: message,
      role: 'user' as const,
      createdAt: new Date().toISOString(),
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setChatInput('');

    // Show AI thinking indicator
    setIsAITyping(true);

    try {
      // Create a new chat first
      const chatResponse = await fetch('/api/chat/chats', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify({ title: message.slice(0, 50) }),
      });

      if (!chatResponse.ok) {
        throw new Error('Failed to create chat');
      }

      const chatData = await chatResponse.json();
      const chatId = chatData.id;

      // Use the non-streaming endpoint to get complete response
      const response = await fetch(`/api/chat/chats/${chatId}/messages`, {
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
      console.log('Response received:', responseData);
      
      // Create assistant message with complete content
      const assistantMessage = {
        id: responseData.assistant_message.id,
        content: responseData.assistant_message.content,
        role: 'assistant' as const,
        createdAt: responseData.assistant_message.createdAt,
      };
      console.log('Assistant message created:', assistantMessage);

      // Add assistant message to state
      setMessages(prev => {
        console.log('Previous messages:', prev);
        const newMessages = [...prev, assistantMessage];
        console.log('New messages array:', newMessages);
        return newMessages;
      });
      console.log('Message added to state, starting typewriter effect...');

      // Start typewriter effect
      startTypewriterEffect(assistantMessage.content, assistantMessage.id);

      // Refresh chats to show the new chat
      await fetchChats();

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
    // Start with empty content
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, content: '' }
        : msg
    ));

    let currentIndex = 0;
    const chunkSize = 3; // Characters to reveal at once
    
    const revealNextChunk = () => {
      if (currentIndex >= fullContent.length) {
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
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, content: fullContent.slice(0, currentIndex) }
          : msg
      ));

      // Schedule next chunk
      setTimeout(revealNextChunk, 20); // 20ms delay between chunks
    };

    // Start the typewriter effect
    revealNextChunk();
  };

  // Auto-scroll to bottom when new messages are added
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAITyping]);

  // Render helpers for edit version navigation (minimal placeholder UI)
  const renderEditHeader = () => {
    if (!isEditing || editedBaseMessageId == null) return null;
    const versions = editVersions[editedBaseMessageId] || [];
    const idx = editVersionIndex[editedBaseMessageId] ?? 0;
    const total = versions.length || 1;
    return (
      <div className="fixed top-16 left-1/2 -translate-x-1/2 z-40 px-3 py-1 rounded bg-gray-900/70 text-white text-sm flex items-center gap-2">
        <button className="px-2 py-1 rounded bg-gray-700 hover:bg-gray-600" onClick={() => setEditVersionIndex(prev => ({...prev, [editedBaseMessageId]: Math.max(0, (prev[editedBaseMessageId] ?? 0) - 1)}))}>{"<"}</button>
        <span>{`${Math.min(idx + 1, total)}/${total}`}</span>
        <button className="px-2 py-1 rounded bg-gray-700 hover:bg-gray-600" onClick={() => setEditVersionIndex(prev => ({...prev, [editedBaseMessageId]: Math.min((prev[editedBaseMessageId] ?? 0) + 1, Math.max(total - 1, 0))}))}>{">"}</button>
      </div>
    );
  };

  // Debug effect to monitor messages state
  React.useEffect(() => {
    console.log('Messages state changed:', messages.length, 'messages');
    console.log('Loading state:', isLoadingMessages);
  }, [messages, isLoadingMessages]);



  // Test hash-based URLs on component mount
  React.useEffect(() => {
    console.log('Testing hash-based URLs...');
    console.log('Hash-based system is ready');
  }, []);

  // Logout function
  const handleLogout = () => {
    clearAuthToken();
    router.replace("/login");
  };

  const fetchChats = async () => {
    try {
      setIsLoadingChats(true);
      const response = await apiCall('/chat/chats', {}, 45000); // 45 second timeout
      setChats(response);
    } catch (error: any) {
      console.error('Failed to fetch chats:', error);
      // Show user-friendly error message
      if (error.message.includes('timeout') || error.message.includes('Cannot connect to server')) {
        console.warn('Chat fetch timeout - this is non-critical and will retry automatically');
      }
    } finally {
      setIsLoadingChats(false);
    }
  };

  const fetchMCPServers = async () => {
    try {
      setIsLoadingMCPServers(true);
      const data = await apiCall("/auth/mcp-servers", {}, 45000); // 45 second timeout
      console.log("[DEBUG] MCP servers response:", data);
      console.log("[DEBUG] MCP servers type:", typeof data);
      console.log("[DEBUG] MCP servers is array:", Array.isArray(data));
      
      const servers = Array.isArray(data) ? data : [];
      setMcpServers(servers);
      
      // Enable all servers by default if none are enabled
      if (enabledServers.size === 0 && servers.length > 0) {
        const serverIds = servers.map(server => server.id);
        setEnabledServers(new Set(serverIds));
        localStorage.setItem('enabledServers', JSON.stringify(serverIds));
        console.log("[DEBUG] Enabled all servers by default:", serverIds);
      }
    } catch (error) {
      console.error("Failed to fetch MCP servers:", error);
      setMcpServers([]); // Set empty array on error
    } finally {
      setIsLoadingMCPServers(false);
    }
  };

  const fetchMCPTools = async () => {
    try {
      setIsLoadingMCPTools(true);
      const data = await apiCall("/chat/mcp/tools", {}, 45000); // 45 second timeout
      setMcpTools(data.tools || []);
    } catch (error) {
      console.error("Failed to fetch MCP tools:", error);
    } finally {
      setIsLoadingMCPTools(false);
    }
  };

  const addMCPServer = async () => {
    try {
      console.log("Starting MCP server addition...");
      console.log("Form data:", {
        name: newServerName,
        description: newServerDescription,
        url: newServerUrl,
        type: newServerType
      });

      const config = {
        type: newServerType,
        uri: newServerUrl,
        transport: newServerType === 'custom' ? 'http' : newServerType
      };

      console.log("Config object:", config);

      const requestBody = {
        name: newServerName,
        description: newServerDescription,
        config: config
      };

      console.log("Request body:", requestBody);

      const newServer = await apiCall("/auth/mcp-servers", {
        method: "POST",
        body: JSON.stringify(requestBody)
      });

      console.log("Server created successfully:", newServer);

      // Try to connect to the server
      try {
        await apiCall(`/chat/mcp/servers/${newServer.id}/connect`, {
          method: "POST"
        });
        console.log("Successfully connected to MCP server");
      } catch (connectError: any) {
        console.warn("Failed to connect to MCP server immediately:", connectError?.message || connectError);
        // Don't show error to user as server will be connected when needed
        // The server is saved and will be connected when actually used
      }

      // Reset form
      setNewServerName('');
      setNewServerDescription('');
      setNewServerUrl('');
      setNewServerType('custom');
      setShowMCPServerModal(false);

      // Refresh servers list
      await fetchMCPServers();
      
      // Show success message
      alert(`MCP Server "${newServer.name}" added successfully! The server will be connected when needed.`);
    } catch (error: any) {
      console.error("Failed to add MCP server - Full error:", error);
      console.error("Error details:", {
        message: error?.message,
        stack: error?.stack,
        response: error?.response
      });
      
      // Show more detailed error message
      let errorMessage = 'Failed to add MCP server. ';
      if (error?.message) {
        errorMessage += `Error: ${error.message}`;
      }
      alert(errorMessage);
    }
  };

  const toggleServerStatus = (serverId: number) => {
    setEnabledServers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(serverId)) {
        newSet.delete(serverId);
      } else {
        newSet.add(serverId);
      }
      
      // Persist to localStorage
      localStorage.setItem('enabledServers', JSON.stringify(Array.from(newSet)));
      console.log("[DEBUG] Updated enabled servers:", Array.from(newSet));
      
      return newSet;
    });
  };

  const deleteMCPServer = async (serverId: number) => {
    try {
      await apiCall(`/auth/mcp-servers/${serverId}`, {
        method: "DELETE"
      });
      await fetchMCPServers();
    } catch (error) {
      console.error("Failed to delete MCP server:", error);
      alert('Failed to delete MCP server. Please try again.');
    }
  };

  const handleSelectChat = async (chatId: number) => {
    try {
      console.log('=== START: handleSelectChat ===');
      
      // Prevent multiple rapid clicks
      if (selectedChatId === chatId.toString()) {
        console.log('Chat already selected, returning');
        return; // Already selected
      }
      
      console.log('Step 1: Setting state for chat:', chatId);
      setSelectedChatId(chatId.toString());
      setCurrentChatId(chatId);
      setMessages([]); // Clear current messages to load new ones
      
      console.log('Step 2: Getting chat hash');
      // Get chat hash from the chat list
      const selectedChat = chats.find(chat => chat.id === chatId);
      if (!selectedChat) {
        throw new Error('Chat not found in list');
      }
      
      // Update URL without triggering navigation
      const hashUrl = `/chat/${selectedChat.hash}`;
      console.log('Generated hash URL:', hashUrl);
      
      console.log('Step 3: Updating URL');
      // Use replace to update URL without triggering navigation
      window.history.replaceState(null, '', hashUrl);
      
      console.log('Step 4: Setting up timeout');
      // Add timeout to prevent infinite loading
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout')), 15000); // 15 second timeout
      });
      
      console.log('Step 5: Fetching messages');
      // Fetch messages with timeout
      await Promise.race([
        fetchMessages(chatId),
        timeoutPromise
      ]);
      
      console.log('=== END: handleSelectChat (success) ===');
      
    } catch (error: any) {
      console.error('=== ERROR in handleSelectChat ===');
      console.error('Error details:', error);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      
      // Show error message to user
      alert(`Error loading chat: ${error.message || 'Unknown error'}`);
      // Reset loading state
      setIsLoadingMessages(false);
    }
  };

  const fetchMessages = async (chatId: number) => {
    try {
      // Prevent fetching if already loading
      if (isLoadingMessages) {
        console.log('Already loading messages, skipping...');
        return;
      }
      
      setIsLoadingMessages(true); // Show loading while fetching messages
      console.log(`Fetching messages for chat ${chatId}...`);
      
      // Get chat hash from the chat list
      const selectedChat = chats.find(chat => chat.id === chatId);
      if (!selectedChat) {
        throw new Error('Chat not found in list');
      }
      
      const startTime = Date.now();
      const response = await apiCall(`/chat/chats/hash/${selectedChat.hash}/messages`);
      const duration = Date.now() - startTime;
      
      console.log(`Received ${response?.length || 0} messages for chat ${chatId} (hash: ${selectedChat.hash}) in ${duration}ms`);
      
      if (Array.isArray(response)) {
        console.log('Setting messages in state:', response.length, 'messages');
        setMessages(response);
        console.log('Messages state should be updated');
      } else {
        console.error('Invalid response format:', response);
        setMessages([]);
      }
    } catch (error: any) {
      console.error('Failed to fetch messages:', error);
      // Set empty messages array on error to prevent UI issues
      setMessages([]);
      // Show user-friendly error
      alert(`Failed to load chat messages: ${error.message || 'Unknown error'}`);
    } finally {
      console.log('Setting isLoadingMessages to false');
      setIsLoadingMessages(false);
      console.log('Loading state should be cleared');
    }
  };

  const handleNewChat = async () => {
    try {
      // Clear current chat and messages without creating a new one
      setCurrentChatId(null);
      setSelectedChatId('');
      setMessages([]);
      setChatInput('');
      
      // Navigate to home page for new chat
      router.push('/');
    } catch (error) {
      console.error("Failed to prepare new chat:", error);
    }
  };

  const handleDeleteChat = async (chatId: number, chatTitle: string) => {
    // Show custom confirmation modal
    setChatToDelete({ id: chatId, title: chatTitle });
    setShowDeleteModal(true);
  };

  const confirmDeleteChat = async () => {
    if (!chatToDelete) return;
    
    try {
      const response = await apiCall(`/chat/chats/${chatToDelete.id}`, {
        method: 'DELETE'
      });
      
      // Remove the chat from the list
      setChats(chats.filter(chat => chat.id !== chatToDelete.id));
      
      // If this was the currently selected chat, clear it
      if (selectedChatId === chatToDelete.id.toString()) {
        setCurrentChatId(null);
        setMessages([]);
        setSelectedChatId('');
      }
      
      console.log('Chat deleted successfully');
    } catch (error) {
      console.error('Failed to delete chat:', error);
      alert('Failed to delete chat. Please try again.');
    } finally {
      setShowDeleteModal(false);
      setChatToDelete(null);
    }
  };

  // Detect page refresh
  useEffect(() => {
    const handleBeforeUnload = () => {
      console.log("⚠️ Page is about to refresh/reload - this is NOT the MCP refresh button");
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Handle URL restoration on component mount
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const currentPath = window.location.pathname;
    console.log("[DEBUG] === COMPONENT MOUNTED ===");
    console.log("[DEBUG] Current path:", currentPath);
    
    // If we're on a chat URL, we're already in the right place
    if (currentPath.match(/^\/chat\/(.+)$/)) {
      console.log("[DEBUG] Already on chat URL, no restoration needed");
      return;
    }
  }, []);

  // Simple authentication check - middleware handles most routing
  useEffect(() => {
    console.log("[DEBUG] === AUTHENTICATION CHECK ===");
    
    const token = getAuthToken();
    if (token) {
      console.log("[DEBUG] Valid token found, setting loading to false");
      setIsLoading(false);
    } else {
      console.log("[DEBUG] No valid token found, but middleware will handle routing");
      // Don't redirect here - let middleware handle it
      setIsLoading(false);
    }
  }, []);

  // Fetch user info and chats after authentication check
  useEffect(() => {
    const fetchUserInfo = async () => {
      const token = getAuthToken();
      if (!token) return;
      
      let timeoutId: NodeJS.Timeout | undefined;
      
      // Cleanup function to clear timeout
      const cleanup = () => {
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = undefined;
        }
      };
      
      try {
        console.log("[DEBUG] Fetching user info...");
        setIsLoadingUser(true);
        
        // Add timeout to prevent hanging
        const controller = new AbortController();
        timeoutId = setTimeout(() => {
          console.log("[DEBUG] Request timeout - aborting fetch");
          controller.abort();
        }, 10000); // 10 second timeout (increased from 5)
        
        const res = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal
        });
        
        // Clear timeout if request completes successfully
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = undefined;
        }
        
        if (!res.ok) {
          console.log("[DEBUG] Failed to fetch user info, status:", res.status);
          // Don't redirect on API failure - let middleware handle auth
          console.log("[DEBUG] API call failed, but not redirecting - letting middleware handle auth");
          return;
        }
        
        const data = await res.json();
        console.log("[DEBUG] User data fetched:", data);
        setUser({ name: data.name || '', email: data.email || '' });
      } catch (err: any) {
        cleanup(); // Clear timeout
        
        // Handle AbortError specifically (timeout or manual abort)
        if (err.name === 'AbortError') {
          console.log("[DEBUG] Request was aborted (likely due to timeout)");
          // Don't show this as an error since it's expected behavior
          return;
        }
        
        console.error("[ERROR] Error fetching user info:", err);
        // Don't redirect on network error - let middleware handle auth
        console.log("[DEBUG] Network error, but not redirecting - letting middleware handle auth");
      } finally {
        setIsLoadingUser(false);
      }
    };
    
    // Only fetch user info and chats if we have a token and passed the initial auth check
    if (!isLoading) {
      fetchUserInfo();
      fetchChats();
      fetchMCPServers();
      fetchMCPTools();
    }
  }, [router, isLoading]);

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f7f7f8] dark:bg-[#18181a]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Debug render
  console.log('RENDER DEBUG:', {
    isLoadingMessages,
    messagesLength: messages.length,
    selectedChatId,
    currentChatId
  });

  return (
    <div className="min-h-screen flex bg-[#f7f7f8] dark:bg-gradient-to-r dark:from-[#000046] dark:to-[#1CB5E0]">
      {/* Fixed Sidebar */}
      {sidebarOpen && (
        <aside
          className="fixed left-0 top-0 z-40 flex flex-col w-64 h-screen backdrop-blur-xl bg-white/10 dark:bg-black/20 border-r border-white/20 dark:border-gray-800/50 px-3 py-4 shadow-2xl"
          style={{
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
            boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)'
          }}
          onMouseMove={e => {
            const sidebar = e.currentTarget;
            const x = e.nativeEvent.offsetX;
            setShowHideBtn(x > sidebar.offsetWidth - 32);
          }}
          onMouseLeave={() => setShowHideBtn(false)}
        >
          {/* Top bar: favicon + close button */}
          <div className="flex items-center justify-between mb-4">
            <img src="/favicon.ico" alt="Vee" className="h-7 w-7 rounded" />
            <button
              className="p-2 rounded-lg backdrop-blur-md bg-white/20 dark:bg-black/30 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center border border-white/20 dark:border-gray-700/50"
              onClick={() => setSidebarOpen(false)}
              title="Close sidebar"
            >
              {/* X (close) icon */}
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          {/* New Chat Button */}
          <button 
            onClick={handleNewChat}
            className="flex items-center gap-2 backdrop-blur-md bg-white/30 dark:bg-white/20 text-black dark:text-white font-semibold rounded-lg px-4 py-2 mb-3 hover:bg-white/40 dark:hover:bg-white/30 transition-all border border-white/30 dark:border-white/20 shadow-lg"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            New Chat
          </button>
          {/* Search Chats Button */}
          <button 
            onClick={handleSearchClick}
            className="flex items-center gap-2 w-full text-white dark:text-gray-200 font-medium rounded-lg px-3 py-2 mb-2 backdrop-blur-md bg-black/30 dark:bg-black/40 hover:bg-black/40 dark:hover:bg-black/50 transition-all border border-white/20 dark:border-gray-700/50"
            style={{ cursor: 'pointer' }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" /></svg>
            🔍 Search Chats
          </button>
          
          {/* MCP Servers Button */}
          <button 
            onClick={() => setShowMCPServerModal(true)}
            className="flex items-center justify-between w-full text-white dark:text-gray-200 font-medium rounded-lg px-3 py-2 mb-2 backdrop-blur-md bg-blue-600/80 dark:bg-blue-700/80 hover:bg-blue-700/90 dark:hover:bg-blue-800/90 transition-all border border-blue-400/30 dark:border-blue-500/30 shadow-lg"
            style={{ cursor: 'pointer' }}
          >
            <div className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>
              🔌 Quick Add MCP
            </div>
            {mcpServers.length > 0 && (
              <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                {mcpServers.length}
              </span>
            )}
          </button>
          {/* Recent Chats */}
          <div className="flex-1 overflow-y-auto mt-2 mb-2 scrollbar-hide">
            <div className="px-2 py-1">
              <span className="font-bold text-white dark:text-gray-200 text-base">Chats</span>
            </div>
            {isLoadingChats ? (
              // Skeleton loading for chats
              <div className="px-2 py-2 space-y-2">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center gap-2 px-2 py-2 rounded-lg backdrop-blur-sm bg-white/10 dark:bg-black/20 border border-white/20 dark:border-gray-700/50">
                    <div className="w-4 h-4 bg-white/30 dark:bg-gray-600/50 rounded animate-pulse"></div>
                    <div className="flex-1">
                      <div className="w-24 h-3 bg-white/30 dark:bg-gray-600/50 rounded animate-pulse mb-1"></div>
                      <div className="w-16 h-2 bg-white/20 dark:bg-gray-700/50 rounded animate-pulse"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // Chat list
              chats.map((chat: Chat) => (
                <div 
                  key={chat.id} 
                  className={`flex items-center gap-2 px-2 py-2 rounded-lg transition-all group backdrop-blur-sm mb-2 ${
                    selectedChatId === chat.id.toString() 
                      ? 'bg-white/20 dark:bg-black/40 border border-white/30 dark:border-gray-600/50' 
                      : 'hover:bg-white/15 dark:hover:bg-black/30 hover:border hover:border-white/20 dark:hover:border-gray-700/50'
                  }`}
                >
                  <div 
                    className={`flex items-center gap-2 flex-1 cursor-pointer ${
                      isLoadingMessages ? 'pointer-events-none opacity-50' : ''
                    }`}
                    onClick={() => !isLoadingMessages && handleSelectChat(chat.id)}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a1 1 0 011-1h6a1 1 0 011 1v4" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h8" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 7h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2z" /></svg>
                    <span className="truncate max-w-[100px] text-white dark:text-gray-200 text-sm font-medium" title={chat.title}>
                      {chat.title}
                      {isLoadingMessages && selectedChatId === chat.id.toString() && (
                        <span className="ml-2 inline-block w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></span>
                      )}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteChat(chat.id, chat.title);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-600 text-gray-400 hover:text-white transition-all"
                    title="Delete chat"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))
            )}
          </div>
          {/* Profile Section - DYNAMIC */}
          <div className="flex flex-col gap-2 px-2 py-3 border-t border-white/20 dark:border-gray-800/50 mt-2">
            <button
              className="flex items-center gap-2 px-3 py-2 rounded backdrop-blur-md hover:bg-black/40 dark:hover:bg-black/50 text-white font-medium mb-1 transition-all border border-white/20 dark:border-gray-700/50"
              title="Settings"
              onClick={() => router.push('/settings')}
            >
              {/* Settings (gear) icon */}
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0a1.724 1.724 0 002.573 1.01c.797-.46 1.757.388 1.3 1.2a1.724 1.724 0 00.457 2.573c.921.3.921 1.603 0 1.902a1.724 1.724 0 00-1.01 2.573c.46.797-.388 1.757-1.2 1.3a1.724 1.724 0 00-2.573.457c-.3.921-1.603.921-1.902 0a1.724 1.724 0 00-2.573-1.01c-.797.46-1.757-.388-1.3-1.2a1.724 1.724 0 00-.457-2.573c-.921-.3-.921-1.603 0-1.902a1.724 1.724 0 001.01-2.573c-.46-.797.388-1.757 1.2-1.3a1.724 1.724 0 002.573-.457z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
              Settings
            </button>
            {isLoadingUser ? (
              // Skeleton loading for user info
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-white/30 dark:bg-gray-600/50 rounded-full animate-pulse"></div>
                <div className="flex flex-col flex-1">
                  <div className="w-24 h-3 bg-white/30 dark:bg-gray-600/50 rounded animate-pulse mb-1"></div>
                  <div className="w-32 h-2 bg-white/20 dark:bg-gray-700/50 rounded animate-pulse"></div>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                {/* User icon */}
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white dark:text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="12" cy="8" r="4" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 20v-2a6 6 0 0112 0v2" /></svg>
                <div className="flex flex-col flex-1">
                  <span className="text-white dark:text-gray-200 text-sm font-semibold">{user.name || 'Vee User'}</span>
                  <span className="text-xs text-gray-400">{user.email || 'Pro Plan'}</span>
                </div>
                {/* Logout button */}
                <button
                  className="p-1 rounded hover:bg-gray-800 text-gray-400 hover:text-white transition-all"
                  onClick={handleLogout}
                  title="Logout"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>
              </div>
            )}
          </div>
          {/* Sidebar toggle button at the right edge, only on hover */}
          {showHideBtn && (
            <button
              className="absolute bottom-6 right-0 px-3 py-2 rounded-l-lg backdrop-blur-md bg-black/30 dark:bg-black/40 text-white dark:text-gray-200 hover:bg-black/40 dark:hover:bg-black/50 transition-all flex items-center gap-1 border border-white/20 dark:border-gray-700/50"
              onClick={() => setSidebarOpen(false)}
              title="Hide sidebar"
            >
              {/* Chevron Left Heroicon */}
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
            </button>
          )}
        </aside>
      )}
      {/* Main content area (rest of your page) */}
      <div className="flex-1">
        {/* Minimal vertical sidebar when sidebarOpen is false */}
        {!sidebarOpen && (
          <div className="fixed left-0 top-0 z-50 h-screen w-16 backdrop-blur-xl bg-white/10 dark:bg-black/20 border-r border-white/20 dark:border-gray-800/50 flex flex-col items-center py-4 gap-6 shadow-2xl"
            style={{
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
              boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)'
            }}>
            {/* Favicon */}
            <img src="/favicon.ico" alt="Vee" className="h-7 w-7 rounded mb-2" />
            {/* New Chat Icon */}
            <button onClick={handleNewChat} className="p-2 rounded-lg backdrop-blur-md bg-white/20 dark:bg-black/30 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center border border-white/20 dark:border-gray-700/50 shadow-lg" title="New Chat">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            </button>
            {/* Search Icon */}
            <button onClick={handleSearchClick} className="p-2 rounded-lg backdrop-blur-md bg-white/20 dark:bg-black/30 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center border border-white/20 dark:border-gray-700/50 shadow-lg" title="Search Chats">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" /></svg>
            </button>
            {/* MCP Servers Icon */}
            <button onClick={() => setShowMCPServerModal(true)} className="p-2 rounded-lg backdrop-blur-md bg-white/20 dark:bg-black/30 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center border border-white/20 dark:border-gray-700/50 shadow-lg" title="MCP Servers">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>
            </button>
            {/* Spacer */}
            <div className="flex-1" />
            {/* User Icon */}
            <button onClick={() => router.push('/settings')} className="p-2 rounded-lg backdrop-blur-md bg-white/20 text-white dark:text-gray-200 hover:bg-white/30 dark:hover:bg-black/40 transition-all flex items-center mb-2 border border-white/20 dark:border-gray-700/50 shadow-lg" title="Settings">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="12" cy="8" r="4" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 20v-2a6 6 0 0112 0v2" /></svg>
            </button>
            {/* Show button to open sidebar at right edge, vertically centered */}
            <button
              className="absolute right-0 top-1/2 px-3 py-2 rounded-l-lg backdrop-blur-md bg-black/30 dark:bg-black/40 text-white dark:text-gray-200 hover:bg-black/40 dark:hover:bg-black/50 transition-all flex items-center gap-1 border border-white/20 dark:border-gray-700/50"
              style={{ transform: 'translateY(-50%)' }}
              onClick={() => setSidebarOpen(true)}
              title="Show sidebar"
            >
              {/* Chevron Right Heroicon */}
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
            </button>
          </div>
        )}
        {/* Main Content */}
        <main className={`flex-1 flex items-center justify-center min-h-screen relative transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
          {/* Dynamic Content Area */}
          {renderEditHeader()}
          {isLoadingMessages ? (
            /* Loading Messages Screen */
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400 text-lg">Loading messages...</p>
              <p className="text-gray-500 dark:text-gray-500 text-sm mt-2">Please wait while we fetch your conversation</p>
            </div>
          ) : messages.length === 0 ? (
            /* Welcome Screen */
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 max-w-2xl w-full mx-auto text-center flex flex-col items-center justify-center pb-16">
              {isPromptCardLoading && (
                <div className="fixed inset-0 bg-black/20 dark:bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center">
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-xl">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-900 dark:text-gray-100 text-lg">Processing your request...</p>
                    <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">Please wait while we set up your chat</p>
                  </div>
                </div>
              )}
              <h1 className="text-3xl md:text-4xl font-bold mb-4 text-gray-900 dark:text-gray-100 font-sans">Welcome to ChatConnect</h1>
              <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">Your AI assistant with MCP server integration. Connect tools, automate workflows, and chat with intelligence.</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10 w-full">
                {promptCards.map((card) => (
                  <div
                    key={card.title}
                    className={`flex flex-col items-center justify-center bg-[#0E5A93] rounded-2xl shadow-lg p-6 transition-all border border-gray-100 dark:border-gray-800 ${
                      isPromptCardLoading 
                        ? 'opacity-50 cursor-not-allowed' 
                        : 'cursor-pointer hover:scale-[1.03] hover:shadow-[0_0_25px_#1CB5E0]'
                    }`}
                    onClick={() => {
                      if (!isPromptCardLoading) {
                        handleSendMessage(card.title === "Send Email" ? "Help me send an email using Gmail integration" : card.title === "MCP Setup" ? "How do I set up MCP servers in ChatConnect?" : "How do I configure OAuth authentication for my MCP servers?");
                      }
                    }}
                  >
                    {isPromptCardLoading ? (
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mb-4"></div>
                    ) : (
                      card.icon
                    )}
                    <h2 className="mt-4 text-lg font-semibold text-gray-900 dark:text-gray-100">{card.title}</h2>
                    <p className="mt-2 text-gray-500 dark:text-gray-400 text-sm">
                      {isPromptCardLoading ? 'Processing...' : card.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Chat Messages Area */
            <div className="w-full h-full flex flex-col">
              <div className="flex-1 overflow-y-auto px-4 py-8 pb-40">
                <div className="max-w-3xl mx-auto space-y-6">
                  {messages.map((message, index) => {
                    console.log('Rendering message in main page:', { id: message.id, role: message.role, content: message.content.substring(0, 50) + '...' });
                    return (
                    <div
                      key={message.id}
                      style={{
                        animation: `slideUp 0.5s ease-out ${index * 0.1}s both`
                      }}
                    >
                      {message.role === 'user' ? (
                        /* User Message - Bubble Style */
                        <div className="flex w-full justify-end">
                          <div className="max-w-[70%] rounded-2xl px-5 py-4 bg-blue-500 text-white ml-12 shadow-lg">
                            <div className="whitespace-pre-wrap break-words text-lg leading-relaxed">
                              {message.content}
                            </div>
                          </div>
                        </div>
                      ) : (
                        /* AI Message - Full Width with Markdown */
                        <div className="w-full">
                          <div className="relative group">
                            <MarkdownRenderer 
                              content={message.content}
                              className="prose prose-gray dark:prose-invert max-w-none text-lg leading-relaxed markdown-content"
                            />
                            {/* Copy button - fixed position that slides with content */}
                            <div className="sticky top-4 float-right -mt-8 mr-4 z-10">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  const button = e.currentTarget as HTMLButtonElement;
                                  
                                  if (!button) {
                                    console.error('Button element not found');
                                    return;
                                  }
                                  
                                  navigator.clipboard.writeText(message.content).then(() => {
                                    // Show temporary success feedback
                                    const originalHTML = button.innerHTML;
                                    const originalClass = button.className;
                                  
                                    // Change to green checkmark with success styling
                                    button.innerHTML = `
                                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                      </svg>
                                    `;
                                    button.className = "opacity-100 p-2 rounded-full bg-green-500 hover:bg-green-600 text-white transition-all duration-200 shadow-lg";
                                  
                                    // Add a subtle scale animation
                                    button.style.transform = 'scale(1.1)';
                                  
                                    setTimeout(() => {
                                      if (button) {
                                        button.innerHTML = originalHTML;
                                        button.className = originalClass;
                                        button.style.transform = 'scale(1)';
                                      }
                                    }, 2000);
                                  }).catch(err => {
                                    console.error('Failed to copy text: ', err);
                                    // Show error feedback
                                    const originalHTML = button.innerHTML;
                                    const originalClass = button.className;
                                  
                                    button.innerHTML = `
                                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                      </svg>
                                    `;
                                    button.className = "opacity-100 p-2 rounded-full bg-red-500 hover:bg-red-600 text-white transition-all duration-200 shadow-lg";
                                  
                                    setTimeout(() => {
                                      if (button) {
                                        button.innerHTML = originalHTML;
                                        button.className = originalClass;
                                      }
                                    }, 2000);
                                  });
                                }}
                                className="opacity-0 group-hover:opacity-100 p-2 rounded-full bg-gray-800/80 dark:bg-gray-700/80 hover:bg-gray-700 dark:hover:bg-gray-600 text-gray-300 hover:text-white backdrop-blur-sm transition-all duration-200 shadow-lg border border-gray-600/30 dark:border-gray-500/30"
                                title="Copy response"
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 00-2-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    );
                  })}
                  
                                     {/* Typing Indicator */}
                   {isAITyping && (
                     <div className="w-full">
                       <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-black/30 dark:bg-black/40 border border-white/20 dark:border-gray-700/50 shadow-sm">
                         <div className="flex space-x-1 text-blue-300">
                           <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                           <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                           <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                           </div>
                         <span className="text-xs text-blue-200">AI is thinking…</span>
                       </div>
                     </div>
                   )}
                   
                   {/* Invisible div for auto-scroll */}
                   <div ref={messagesEndRef} />
                 </div>
               </div>
             </div>
          )}
          {/* Chatbox fixed at bottom - Always centered */}
                <div
        className={`fixed bottom-0 ${sidebarOpen ? 'left-64' : 'left-16'} right-0 flex flex-col items-center justify-end z-30 transition-all duration-300`}
        style={{ pointerEvents: 'none' }}
      >
            <div className={`relative w-full flex flex-col items-center mb-6 px-4 transition-all duration-300 max-w-4xl`} style={{ pointerEvents: 'auto' }}>
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
                      onClick={() => currentRequestController?.abort()}
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
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke={chatInput.trim() ? 'white' : 'black'}>
                        <circle cx="12" cy="12" r="11" stroke="white" strokeWidth="2" fill="white" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 16V8m0 0l-4 4m4-4l4 4" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Search Modal */}
      {showSearchModal && (
        <div 
          className="fixed inset-0 bg-black/40 dark:bg-black/30 flex items-center justify-center z-[99999] backdrop-blur-xl"
          onClick={handleBackdropClick}
        >
          <div 
            className="backdrop-blur-xl bg-white/10 dark:bg-black/30 rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[80vh] flex flex-col border border-white/30 dark:border-gray-700/50"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/20 dark:border-gray-700/50">
              <h2 className="text-lg font-semibold text-white dark:text-gray-100">Search Chats</h2>
              <button
                onClick={() => {
                  setShowSearchModal(false);
                  setModalSearch("");
                }}
                className="text-gray-400 hover:text-gray-200 dark:hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-800"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Search Input */}
            <div className="p-4 border-b border-white/20 dark:border-gray-700/50">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search for chats..."
                  value={modalSearch}
                  onChange={(e) => setModalSearch(e.target.value)}
                  className="w-full px-4 py-3 pl-10 rounded-lg border border-gray-600 dark:border-gray-700 bg-gray-800 dark:bg-gray-900 text-white dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
                  autoFocus
                />
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 absolute left-3 top-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Chat Results */}
            <div className="flex-1 overflow-y-auto p-4">
              {modalFilteredChats.length === 0 ? (
                <div className="text-center text-gray-400 dark:text-gray-500 py-8">
                  {modalSearch ? "No chats found" : "Start typing to search chats"}
                </div>
              ) : (
                <div className="space-y-2">
                  {modalFilteredChats.map((chat) => (
                    <button
                      key={chat.id}
                      onClick={() => handleChatSelect(chat.id)}
                      className={`w-full text-left p-3 rounded-lg transition-all duration-200 ${
                        selectedChatId === chat.id.toString()
                          ? "bg-blue-600 dark:bg-blue-700 text-white shadow-lg"
                          : "bg-gray-800 dark:bg-gray-900 hover:bg-gray-700 dark:hover:bg-gray-800 text-gray-100 dark:text-gray-200 border border-gray-700 dark:border-gray-800"
                      }`}
                    >
                      <div className="font-medium">{chat.title}</div>
                      {selectedChatId === chat.id.toString() && (
                        <div className="text-xs text-blue-200 dark:text-blue-300 mt-1">Currently selected</div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-gray-700 dark:border-gray-800">
              <div className="text-sm text-gray-400 dark:text-gray-500 text-center">
                {modalFilteredChats.length} chat{modalFilteredChats.length !== 1 ? 's' : ''} found
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MCP Server Modal */}
      {showMCPServerModal && (
        <div 
          className="fixed inset-0 bg-black/40 dark:bg-black/30 flex items-center justify-center z-[99999] backdrop-blur-2xl"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowMCPServerModal(false);
            }
          }}
        >
          <div 
            className="backdrop-blur-xl bg-white/20 dark:bg-black/40 rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] flex flex-col border border-white/30 dark:border-gray-700/50"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/20 dark:border-gray-700/50">
              <h2 className="text-lg font-semibold text-white dark:text-gray-100">MCP Server Management</h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={async (e) => {
                    e.preventDefault(); // Prevent any default browser behavior
                    e.stopPropagation(); // Stop event bubbling
                    
                    console.log("🎯 MCP Refresh button clicked - this should NOT refresh the page");
                    
                    if (isRefreshingMCP) return; // Prevent multiple clicks
                    try {
                      setIsRefreshingMCP(true);
                      console.log("🔄 Refreshing MCP servers and tools...");
                      
                      // Refresh both sections with loading states
                      await Promise.all([
                        fetchMCPServers(),
                        fetchMCPTools()
                      ]);
                      
                      console.log("✅ Refresh completed");
                      // Show success feedback
                      const button = document.querySelector('[title="Refreshing..."]') as HTMLElement;
                      if (button) {
                        const originalTitle = button.getAttribute('title');
                        button.setAttribute('title', 'Refresh completed!');
                        setTimeout(() => {
                          button.setAttribute('title', originalTitle || 'Refresh servers and tools');
                        }, 2000);
                      }
                    } catch (error) {
                      console.error("❌ Refresh failed:", error);
                      // Show error feedback
                      alert('Failed to refresh MCP servers and tools. Please try again.');
                    } finally {
                      setIsRefreshingMCP(false);
                    }
                  }}
                  type="button"
                  disabled={isRefreshingMCP}
                  className={`transition-colors p-1 rounded-lg ${
                    isRefreshingMCP 
                      ? 'text-gray-600 cursor-not-allowed' 
                      : 'text-gray-400 hover:text-gray-200 dark:hover:text-gray-300 hover:bg-gray-700 dark:hover:bg-gray-800'
                  }`}
                  title={isRefreshingMCP ? "Refreshing servers and tools..." : "Refresh servers and tools"}
                >
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    className={`h-5 w-5 ${isRefreshingMCP ? 'animate-spin' : ''}`} 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
                <button
                  onClick={() => setShowMCPServerModal(false)}
                  className="text-gray-400 hover:text-gray-200 dark:hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-800"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {/* Quick Add Section */}
              <div className="mb-6 p-4 bg-blue-900/20 dark:bg-blue-900/10 rounded-lg border border-blue-700 dark:border-blue-800">
                <h3 className="text-md font-semibold text-blue-200 dark:text-blue-300 mb-3">🚀 Quick Add MCP Server</h3>
                <p className="text-sm text-blue-300 dark:text-blue-400 mb-4">
                  Paste your MCP server URL from Pipedream, GitHub, or any other platform to quickly connect it.
                </p>
                
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
                  <input
                    type="text"
                    value={newServerUrl}
                    onChange={(e) => setNewServerUrl(e.target.value)}
                    placeholder="Paste MCP server URL here (e.g., https://your-pipedream-workflow.m.pipedream.net)"
                    className="w-full px-3 py-2 rounded-lg border border-blue-600 dark:border-blue-700 bg-blue-900/20 dark:bg-blue-900/10 text-white dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-blue-400 dark:placeholder-blue-500"
                  />
                  <input
                    type="text"
                    value={newServerName}
                    onChange={(e) => setNewServerName(e.target.value)}
                    placeholder="Give it a name (optional - will auto-generate if empty)"
                    className="w-full px-3 py-2 rounded-lg border border-blue-600 dark:border-blue-700 bg-blue-900/20 dark:bg-blue-900/10 text-white dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-blue-400 dark:placeholder-blue-500"
                  />
                  <button
                    onClick={() => {
                      if (!newServerName.trim()) {
                        // Auto-generate name from URL
                        const url = new URL(newServerUrl);
                        const hostname = url.hostname.replace(/^www\./, '');
                        setNewServerName(`${hostname} MCP Server`);
                      }
                      addMCPServer();
                    }}
                    disabled={!newServerUrl.trim()}
                    className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
                  >
                    Quick Connect
                  </button>
                </div>
              </div>

              {/* Advanced Add Section */}
              <div className="mb-6 p-4 bg-gray-800 dark:bg-gray-900 rounded-lg border border-gray-700 dark:border-gray-800">
                <h3 className="text-md font-semibold text-white dark:text-gray-100 mb-4">⚙️ Advanced Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 dark:text-gray-400 mb-2">
                      Server Name
                    </label>
                    <input
                      type="text"
                      value={newServerName}
                      onChange={(e) => setNewServerName(e.target.value)}
                      placeholder="Enter server name"
                      className="w-full px-3 py-2 rounded-lg border border-gray-600 dark:border-gray-700 bg-gray-700 dark:bg-gray-800 text-white dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 dark:text-gray-400 mb-2">
                      Description
                    </label>
                    <input
                      type="text"
                      value={newServerDescription}
                      onChange={(e) => setNewServerDescription(e.target.value)}
                      placeholder="Enter server description (optional)"
                      className="w-full px-3 py-2 rounded-lg border border-gray-600 dark:border-gray-700 bg-gray-700 dark:bg-gray-800 text-white dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 dark:text-gray-400 mb-2">
                      Server Type
                    </label>
                    <select
                      value={newServerType}
                      onChange={(e) => setNewServerType(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-gray-600 dark:border-gray-700 bg-gray-700 dark:bg-gray-800 text-white dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="custom">Custom HTTP/HTTPS</option>
                      <option value="stdio">STDIO</option>
                      <option value="websocket">WebSocket</option>
                      <option value="sse">Server-Sent Events</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 dark:text-gray-400 mb-2">
                      Server URL/Command
                    </label>
                    <input
                      type="text"
                      value={newServerUrl}
                      onChange={(e) => setNewServerUrl(e.target.value)}
                      placeholder={newServerType === 'stdio' ? 'Enter command (e.g., python server.py)' : 'Enter server URL'}
                      className="w-full px-3 py-2 rounded-lg border border-gray-600 dark:border-gray-700 bg-gray-700 dark:bg-gray-800 text-white dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <button
                    onClick={addMCPServer}
                    disabled={!newServerName.trim() || !newServerUrl.trim()}
                    className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-500 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
                  >
                    Add Server
                  </button>
                </div>
              </div>

              {/* Existing Servers List */}
              <div className="mb-6">
                <h3 className="text-md font-semibold text-white dark:text-gray-100 mb-4">
                  Connected Servers {isLoadingMCPServers && <span className="text-blue-400">(Refreshing...)</span>}
                </h3>
                {isLoadingMCPServers ? (
                  <div className="text-center text-gray-400 dark:text-gray-500 py-8">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-2"></div>
                      <span>Loading servers...</span>
                    </div>
                  </div>
                ) : mcpServers.length === 0 ? (
                  <div className="text-center text-gray-400 dark:text-gray-500 py-8">
                    No MCP servers connected
                  </div>
                ) : (
                  <div className="space-y-3">
                    {Array.isArray(mcpServers) ? mcpServers.map((server) => (
                      <div
                        key={server.id}
                        className="p-4 bg-gray-800 dark:bg-gray-900 rounded-lg border border-gray-700 dark:border-gray-800"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h4 className="font-medium text-white dark:text-gray-100">{server.name}</h4>
                            {server.description && (
                              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">{server.description}</p>
                            )}
                            <div className="text-xs text-gray-500 dark:text-gray-600 mt-2">
                              Type: {server.config?.type || 'unknown'} | 
                              URL: {server.config?.uri || 'N/A'}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            {/* Toggle Switch */}
                            <button
                              onClick={() => toggleServerStatus(server.id)}
                              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                                enabledServers.has(server.id)
                                  ? 'bg-green-600'
                                  : 'bg-gray-600'
                              }`}
                              title={enabledServers.has(server.id) ? 'Disable server' : 'Enable server'}
                            >
                              <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                  enabledServers.has(server.id) ? 'translate-x-6' : 'translate-x-1'
                                }`}
                              />
                            </button>
                            {/* Delete Button */}
                            <button
                              onClick={() => deleteMCPServer(server.id)}
                              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    )) : (
                      <div className="text-center text-gray-400 dark:text-gray-500 py-8">
                        Error loading MCP servers
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Available Tools */}
              <div>
                <h3 className="text-md font-semibold text-white dark:text-gray-100 mb-4">
                  Available Tools ({mcpTools.filter(tool => {
                    const server = mcpServers.find(s => s.name === tool.server_name);
                    return server ? enabledServers.has(server.id) : false;
                  }).length}) {isLoadingMCPTools && <span className="text-blue-400">(Refreshing...)</span>}
                </h3>
                {isLoadingMCPTools ? (
                  <div className="text-center text-gray-400 dark:text-gray-500 py-8">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-2"></div>
                      <span>Loading tools...</span>
                    </div>
                  </div>
                ) : mcpTools.filter(tool => {
                  const server = mcpServers.find(s => s.name === tool.server_name);
                  return server ? enabledServers.has(server.id) : false;
                }).length === 0 ? (
                  <div className="text-center text-gray-400 dark:text-gray-500 py-8">
                    {mcpTools.length > 0 
                      ? 'No tools available from enabled servers. Enable servers to see their tools.'
                      : 'No tools available from connected servers'
                    }
                  </div>
                ) : (
                  <div className="space-y-4">
                    {(() => {
                      // Filter tools to only show from enabled servers
                      const filteredTools = mcpTools.filter((tool) => {
                        // Find the server by name and check if it's enabled
                        const server = mcpServers.find(s => s.name === tool.server_name);
                        return server ? enabledServers.has(server.id) : false;
                      });
                      
                      // Group tools by server name
                      const toolsByServer: Record<string, any[]> = {};
                      filteredTools.forEach((tool) => {
                        const serverName = tool.server_name || 'Unknown Server';
                        if (!toolsByServer[serverName]) {
                          toolsByServer[serverName] = [];
                        }
                        toolsByServer[serverName].push(tool);
                      });

                      return Object.entries(toolsByServer).map(([serverName, tools]) => (
                        <div key={serverName} className="bg-gray-800 dark:bg-gray-900 rounded-lg border border-gray-700 dark:border-gray-800 overflow-hidden">
                          {/* Server Header */}
                          <div className="px-4 py-3 bg-gray-700 dark:bg-gray-800 border-b border-gray-600 dark:border-gray-700">
                            <h4 className="font-semibold text-white dark:text-gray-100 text-sm">
                              {serverName} ({tools.length} tools)
                            </h4>
                          </div>
                          
                          {/* Tools List */}
                          <div className="p-3">
                            {tools.slice(0, expandedServers.has(serverName) ? tools.length : 3).map((tool, index) => (
                              <div
                                key={index}
                                className="mb-3 last:mb-0 p-3 bg-gray-700 dark:bg-gray-800 rounded-lg border border-gray-600 dark:border-gray-700"
                              >
                                <div className="flex items-start justify-between">
                                  <div className="flex-1 min-w-0">
                                    <h5 className="font-medium text-white dark:text-gray-100 text-sm truncate">
                                      {tool.name || 'Unnamed Tool'}
                                    </h5>
                                    {tool.description && (
                                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 line-clamp-2 overflow-hidden">
                                        {tool.description}
                                      </p>
                                    )}
                                  </div>
                                  <span className="ml-2 px-2 py-1 bg-green-600 text-white rounded text-xs flex-shrink-0">
                                    Available
                                  </span>
                                </div>
                              </div>
                            ))}
                            
                            {/* View More/Less Button */}
                            {tools.length > 3 && (
                              <button
                                onClick={() => {
                                  const newExpanded = new Set(expandedServers);
                                  if (newExpanded.has(serverName)) {
                                    newExpanded.delete(serverName);
                                  } else {
                                    newExpanded.add(serverName);
                                  }
                                  setExpandedServers(newExpanded);
                                }}
                                className="w-full mt-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors"
                              >
                                {expandedServers.has(serverName) 
                                  ? `Show Less` 
                                  : `View ${tools.length - 3} More Tools`
                                }
                              </button>
                            )}
                          </div>
                        </div>
                      ));
                    })()}
                  </div>
                )}
              </div>
              
              {/* Settings Link */}
              <div className="p-4 border-t border-gray-700 dark:border-gray-800">
                <div className="text-center">
                  <p className="text-sm text-gray-400 dark:text-gray-500 mb-2">
                    Need more control over your MCP servers?
                  </p>
                  <button
                    onClick={() => {
                      setShowMCPServerModal(false);
                      router.push('/settings?tab=mcp-servers');
                    }}
                    className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                  >
                    Open Full Settings →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

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
                    Delete "{chatToDelete.title}"?
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
