'use client';

import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef, useEffect } from 'react';
import { MarkdownRenderer } from './MarkdownRenderer';

interface Message {
  id: number;
  content: string;
  role: string;
  createdAt: string;
  isEdited?: boolean;
}

interface VirtualizedMessageListProps {
  messages: Message[];
  onEditMessage: (messageId: number, content: string) => void;
  onFeedback: (messageId: number, feedback: 'thumbs_up' | 'thumbs_down') => void;
  messageFeedback: { [key: number]: 'thumbs_up' | 'thumbs_down' | null };
  editingMessageId: number | null;
  editingContent: string;
  setEditingContent: (content: string) => void;
  onSaveEdit: (messageId: number) => void;
  onCancelEdit: () => void;
  promptVersions: string[];
  promptVersionIndex: number;
  setPromptVersionIndex: (index: number) => void;
  typingMessageId: number | null;
  displayedContent: string;
}

export function VirtualizedMessageList({
  messages,
  onEditMessage,
  onFeedback,
  messageFeedback,
  editingMessageId,
  editingContent,
  setEditingContent,
  onSaveEdit,
  onCancelEdit,
  promptVersions,
  promptVersionIndex,
  setPromptVersionIndex,
  typingMessageId,
  displayedContent,
}: VirtualizedMessageListProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // Estimate height per message
    overscan: 5, // Render 5 extra items above/below viewport
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      virtualizer.scrollToIndex(messages.length - 1, { align: 'end' });
    }
  }, [messages.length, virtualizer]);

  const renderMessage = (message: Message, index: number) => {
    if (message.role === 'user') {
      return (
        <div className="flex w-full justify-end mb-4">
          <div className="relative group max-w-[70%] rounded-2xl px-5 py-4 bg-blue-500 text-white ml-12 shadow-lg">
            {editingMessageId === message.id ? (
              /* Inline editing mode */
              <div className="space-y-2">
                <textarea
                  value={editingContent}
                  onChange={(e) => setEditingContent(e.target.value)}
                  className="w-full bg-transparent border-none outline-none text-white resize-none text-lg leading-relaxed placeholder-white/70"
                  placeholder="Edit your message..."
                  rows={Math.max(1, editingContent.split('\n').length)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      onSaveEdit(message.id);
                    } else if (e.key === 'Escape') {
                      onCancelEdit();
                    }
                  }}
                  autoFocus
                />
                <div className="flex gap-2 text-sm">
                  <button
                    onClick={() => onSaveEdit(message.id)}
                    className="px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-white"
                  >
                    Save
                  </button>
                  <button
                    onClick={onCancelEdit}
                    className="px-2 py-1 bg-gray-600 hover:bg-gray-700 rounded text-white"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              /* Normal display mode */
              <>
                <div className="whitespace-pre-wrap break-words text-lg leading-relaxed">
                  {message.content}
                  {message.isEdited && (
                    <span className="text-xs text-blue-200 ml-2">(edited)</span>
                  )}
                </div>
                {/* Edit button - appears on hover */}
                <button
                  onClick={() => onEditMessage(message.id, message.content)}
                  className="absolute -bottom-2 -left-2 p-1 rounded-full bg-gray-800/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Edit message"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                {/* Copy button - appears on hover */}
                <button
                  onClick={() => navigator.clipboard.writeText(message.content)}
                  className="absolute -bottom-2 -right-2 p-1 rounded-full bg-gray-800/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Copy message"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 00-2-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
              </>
            )}
          </div>
        </div>
      );
    } else {
      return (
        <div className="w-full mb-4">
          <div className="relative group">
            <MarkdownRenderer 
              content={message.id === typingMessageId ? displayedContent : message.content}
              className="prose prose-gray dark:prose-invert max-w-none text-lg leading-relaxed markdown-content"
            />
            
            {/* Version slider - appears after AI responses */}
            {promptVersions.length > 1 && (
              <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                <button
                  onClick={() => {
                    if (promptVersionIndex > 0) {
                      const idx = promptVersionIndex - 1;
                      setPromptVersionIndex(idx);
                    }
                  }}
                  className="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
                  disabled={promptVersionIndex <= 0}
                  title="Previous version"
                >
                  «
                </button>
                <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                  {promptVersionIndex + 1}/{promptVersions.length}
                </span>
                <button
                  onClick={() => {
                    if (promptVersionIndex < promptVersions.length - 1) {
                      const idx = promptVersionIndex + 1;
                      setPromptVersionIndex(idx);
                    }
                  }}
                  className="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
                  disabled={promptVersionIndex >= promptVersions.length - 1}
                  title="Next version"
                >
                  »
                </button>
              </div>
            )}
            
            {/* Copy button */}
            <div className="sticky top-4 float-right -mt-8 mr-4 z-10">
              <button
                onClick={() => navigator.clipboard.writeText(message.content)}
                className="opacity-0 group-hover:opacity-100 p-2 rounded-full bg-gray-800/80 dark:bg-gray-700/80 hover:bg-gray-700 dark:hover:bg-gray-600 text-gray-300 hover:text-white backdrop-blur-sm transition-all duration-200 shadow-lg border border-gray-600/30 dark:border-gray-500/30"
                title="Copy response"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 00-2-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
            
            {/* Feedback buttons */}
            <div className="mt-4 flex items-center justify-center gap-2">
              <button
                onClick={() => onFeedback(message.id, 'thumbs_up')}
                className={`p-2 rounded-full transition-all ${
                  messageFeedback[message.id] === 'thumbs_up'
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-green-100 dark:hover:bg-green-900/20 hover:text-green-600 dark:hover:text-green-400'
                }`}
                title="Thumbs up - This response was helpful"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2.76 20.2a2.76 2.76 0 002.74 2.74h10.5a2.76 2.76 0 002.74-2.74V6.29a2.76 2.76 0 00-2.74-2.74H5.5a2.76 2.76 0 00-2.74 2.74v13.91zM7.5 1.5a2.76 2.76 0 012.74-2.74h1.5a2.76 2.76 0 012.74 2.74v1.5a2.76 2.76 0 01-2.74 2.74h-1.5a2.76 2.76 0 01-2.74-2.74v-1.5z"/>
                </svg>
              </button>
              <button
                onClick={() => onFeedback(message.id, 'thumbs_down')}
                className={`p-2 rounded-full transition-all ${
                  messageFeedback[message.id] === 'thumbs_down'
                    ? 'bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-red-100 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400'
                }`}
                title="Thumbs down - This response was not helpful"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M15.3 1.2a2.76 2.76 0 00-2.74 2.74v1.5a2.76 2.76 0 002.74 2.74h1.5a2.76 2.76 0 002.74-2.74v-1.5a2.76 2.76 0 00-2.74-2.74h-1.5zM2.76 20.2a2.76 2.76 0 002.74 2.74h10.5a2.76 2.76 0 002.74-2.74V6.29a2.76 2.76 0 00-2.74-2.74H5.5a2.76 2.76 0 00-2.74 2.74v13.91z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      );
    }
  };

  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const message = messages[virtualItem.index];
          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              {renderMessage(message, virtualItem.index)}
            </div>
          );
        })}
      </div>
    </div>
  );
}
