import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback } from 'react';

const API_BASE = '/api';

// Types
interface Message {
  id: number;
  content: string;
  role: string;
  createdAt: string;
  isEdited?: boolean;
}

interface Chat {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

// Chat data hook with caching
export const useChatData = (chatId: string) => {
  const queryClient = useQueryClient();
  const [optimisticMessages, setOptimisticMessages] = useState<Message[]>([]);

  // Fetch chat messages with caching
  const {
    data: messages = [],
    isLoading: isLoadingMessages,
    error: messagesError,
    refetch: refetchMessages,
  } = useQuery({
    queryKey: ['chat-messages', chatId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/chat/chats/${chatId}/messages`);
      if (!response.ok) throw new Error('Failed to fetch messages');
      return response.json();
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false, // Don't refetch on every focus
  });

  // Fetch chat details with caching
  const {
    data: chat,
    isLoading: isLoadingChat,
    error: chatError,
  } = useQuery({
    queryKey: ['chat', chatId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/chat/chats/${chatId}`);
      if (!response.ok) throw new Error('Failed to fetch chat');
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  // Send message mutation with optimistic updates
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await fetch(`${API_BASE}/chat/chats/${chatId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: message, chatId }),
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      return response.json();
    },
    onMutate: async (message) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['chat-messages', chatId] });

      // Snapshot previous value
      const previousMessages = queryClient.getQueryData(['chat-messages', chatId]);

      // Optimistically update messages
      const optimisticMessage: Message = {
        id: Date.now(),
        content: message,
        role: 'user',
        createdAt: new Date().toISOString(),
      };

      const optimisticAIResponse: Message = {
        id: Date.now() + 1,
        content: '', // Will be filled by typewriter effect
        role: 'assistant',
        createdAt: new Date().toISOString(),
      };

      queryClient.setQueryData(['chat-messages', chatId], (old: Message[] = []) => [
        ...old,
        optimisticMessage,
        optimisticAIResponse,
      ]);

      return { previousMessages, optimisticMessage, optimisticAIResponse };
    },
    onSuccess: (data, variables, context) => {
      if (context) {
        // Update with real data
        queryClient.setQueryData(['chat-messages', chatId], (old: Message[] = []) => {
          const filtered = old.filter(msg => 
            msg.id !== context.optimisticMessage.id && 
            msg.id !== context.optimisticAIResponse.id
          );
          return [...filtered, data.user_message, data.assistant_message];
        });
      }
      
      // Invalidate and refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['chat-messages', chatId] });
    },
    onError: (error, variables, context) => {
      if (context?.previousMessages) {
        // Rollback on error
        queryClient.setQueryData(['chat-messages', chatId], context.previousMessages);
      }
    },
  });

  // Update message mutation (for editing)
  const updateMessageMutation = useMutation({
    mutationFn: async ({ messageId, content }: { messageId: number; content: string }) => {
      const response = await fetch(`${API_BASE}/chat/messages/${messageId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      
      if (!response.ok) throw new Error('Failed to update message');
      return response.json();
    },
    onMutate: async ({ messageId, content }) => {
      await queryClient.cancelQueries({ queryKey: ['chat-messages', chatId] });
      
      const previousMessages = queryClient.getQueryData(['chat-messages', chatId]);
      
      // Optimistically update the message
      queryClient.setQueryData(['chat-messages', chatId], (old: Message[] = []) =>
        old.map(msg => 
          msg.id === messageId 
            ? { ...msg, content, isEdited: true }
            : msg
        )
      );
      
      return { previousMessages };
    },
    onError: (error, variables, context) => {
      if (context?.previousMessages) {
        queryClient.setQueryData(['chat-messages', chatId], context.previousMessages);
      }
    },
  });

  // Prefetch next page of messages
  const prefetchNextPage = useCallback(() => {
    if (messages.length > 0) {
      queryClient.prefetchQuery({
        queryKey: ['chat-messages', chatId, 'next'],
        queryFn: async () => {
          const lastMessageId = messages[messages.length - 1].id;
          const response = await fetch(
            `${API_BASE}/chat/chats/${chatId}/messages?after=${lastMessageId}`
          );
          if (!response.ok) throw new Error('Failed to fetch next page');
          return response.json();
        },
      });
    }
  }, [chatId, messages, queryClient]);

  return {
    // Data
    messages: optimisticMessages.length > 0 ? optimisticMessages : messages,
    chat,
    
    // Loading states
    isLoadingMessages,
    isLoadingChat,
    
    // Errors
    messagesError,
    chatError,
    
    // Actions
    sendMessage: sendMessageMutation.mutate,
    updateMessage: updateMessageMutation.mutate,
    refetchMessages,
    prefetchNextPage,
    
    // Mutation states
    isSending: sendMessageMutation.isPending,
    isUpdating: updateMessageMutation.isPending,
  };
};

// Chat list hook with caching
export const useChatList = () => {
  const queryClient = useQueryClient();

  const {
    data: chats = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['chats'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/chat/chats`);
      if (!response.ok) throw new Error('Failed to fetch chats');
      return response.json();
    },
    staleTime: 1 * 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
  });

  // Create new chat mutation
  const createChatMutation = useMutation({
    mutationFn: async (title: string) => {
      const response = await fetch(`${API_BASE}/chat/chats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      
      if (!response.ok) throw new Error('Failed to create chat');
      return response.json();
    },
    onSuccess: (newChat) => {
      // Optimistically add to chat list
      queryClient.setQueryData(['chats'], (old: Chat[] = []) => [newChat, ...old]);
      
      // Invalidate to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['chats'] });
    },
  });

  return {
    chats,
    isLoading,
    error,
    refetch,
    createChat: createChatMutation.mutate,
    isCreating: createChatMutation.isPending,
  };
};
