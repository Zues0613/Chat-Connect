import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Components } from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  const components: Components = {
    // Code blocks with syntax highlighting
    code({ node, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      const isInline = !match;
      
      if (isInline) {
        return (
          <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700" {...props}>
            {children}
          </code>
        );
      }
      
      const codeString = String(children).replace(/\n$/, '');
      
      const handleCopy = async () => {
        try {
          await navigator.clipboard.writeText(codeString);
          // You could add a toast notification here
        } catch (err) {
          console.error('Failed to copy code:', err);
        }
      };
      
      return (
        <div className="my-6">
          {/* Code block container with ChatGPT-like styling */}
          <div className="bg-gray-900 dark:bg-gray-800 rounded-lg overflow-hidden border border-gray-700 dark:border-gray-600 shadow-lg">
            {/* Header with language label and copy button */}
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800 dark:bg-gray-700 border-b border-gray-700 dark:border-gray-600">
              <span className="text-xs font-medium text-gray-300 dark:text-gray-400 uppercase tracking-wide">
                {language || 'text'}
              </span>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-gray-200 dark:hover:text-gray-300 hover:bg-gray-700 dark:hover:bg-gray-600 rounded transition-colors"
                title="Copy code"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 00-2-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy
              </button>
            </div>
            
            {/* Code content */}
            <div className="relative">
              <SyntaxHighlighter
                style={oneDark}
                language={language}
                PreTag="div"
                customStyle={{
                  margin: '0',
                  padding: '1rem',
                  fontSize: '14px',
                  lineHeight: '1.6',
                  backgroundColor: 'transparent',
                  borderRadius: '0',
                }}
                codeTagProps={{
                  style: {
                    fontSize: '14px',
                    fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
                  }
                }}
                {...props}
              >
                {codeString}
              </SyntaxHighlighter>
            </div>
          </div>
        </div>
      );
    },
    
    // Headers with proper styling
    h1: ({ children }) => (
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-6 mb-4 pb-2 border-b border-gray-200 dark:border-gray-700">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mt-5 mb-3">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-4 mb-2">
        {children}
      </h3>
    ),
    h4: ({ children }) => (
      <h4 className="text-base font-semibold text-gray-900 dark:text-gray-100 mt-3 mb-2">
        {children}
      </h4>
    ),
    
    // Paragraphs
    p: ({ children }) => (
      <p className="mb-3 text-gray-700 dark:text-gray-300 leading-relaxed">
        {children}
      </p>
    ),
    
    // Lists
    ul: ({ children }) => (
      <ul className="mb-3 ml-6 space-y-1 list-disc text-gray-700 dark:text-gray-300">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className="mb-3 ml-6 space-y-1 list-decimal text-gray-700 dark:text-gray-300">
        {children}
      </ol>
    ),
    li: ({ children }) => (
      <li className="leading-relaxed">
        {children}
      </li>
    ),
    
    // Blockquotes
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-500 dark:border-blue-400 pl-6 my-4 italic text-gray-600 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 py-3 rounded-r-lg">
        {children}
      </blockquote>
    ),
    
    // Links
    a: ({ href, children }) => (
      <a 
        href={href} 
        className="text-blue-600 dark:text-blue-400 hover:underline font-medium" 
        target="_blank" 
        rel="noopener noreferrer"
      >
        {children}
      </a>
    ),
    
    // Tables
    table: ({ children }) => (
      <div className="overflow-x-auto my-4">
        <table className="min-w-full border border-gray-300 dark:border-gray-600 rounded-lg">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="bg-gray-50 dark:bg-gray-800">
        {children}
      </thead>
    ),
    tbody: ({ children }) => (
      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
        {children}
      </tbody>
    ),
    tr: ({ children }) => (
      <tr className="hover:bg-gray-50 dark:hover:bg-gray-800">
        {children}
      </tr>
    ),
    th: ({ children }) => (
      <th className="px-4 py-2 text-left text-sm font-semibold text-gray-900 dark:text-gray-100 border-b border-gray-300 dark:border-gray-600">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
        {children}
      </td>
    ),
    
    // Horizontal rules
    hr: () => (
      <hr className="my-6 border-gray-300 dark:border-gray-600" />
    ),
    
    // Strong and emphasis
    strong: ({ children }) => (
      <strong className="font-semibold text-gray-900 dark:text-gray-100">
        {children}
      </strong>
    ),
    em: ({ children }) => (
      <em className="italic text-gray-800 dark:text-gray-200">
        {children}
      </em>
    ),
  };

  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer; 