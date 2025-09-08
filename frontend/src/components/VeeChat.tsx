"use client";
import React from "react";
import Sidebar from "../app/chat/components/Sidebar";
import ChatHeader from "../app/chat/components/ChatHeader";
import MessageBubble from "../app/chat/components/MessageBubble";
import ChatInput from "../app/chat/components/ChatInput";

type Message = {
  id: string;
  sender: "user" | "Vee";
  content: string | React.ReactNode;
};

type Chat = {
  id: string;
  title: string;
};

const dummyChats: Chat[] = [
  { id: "1", title: "How to use Vee?" },
  { id: "2", title: "Project ideas" },
  { id: "3", title: "Travel tips" },
];

const dummyMessages: Record<string, Message[]> = {
  "1": [
    { id: "m1", sender: "user", content: "Hi Vee!" },
    { id: "m2", sender: "Vee", content: "Hello! How can I help you today?" },
  ],
  "2": [
    { id: "m1", sender: "user", content: "Give me some project ideas." },
    { id: "m2", sender: "Vee", content: "Sure! What kind of projects are you interested in?" },
  ],
  "3": [
    { id: "m1", sender: "user", content: "Any travel tips for Japan?" },
    { id: "m2", sender: "Vee", content: "Absolutely! Japan is amazing. What cities are you visiting?" },
  ],
};

export default function VeeChat() {
  const [selectedChatId, setSelectedChatId] = React.useState<string>(dummyChats[0].id);
  const [messages, setMessages] = React.useState<Message[]>(dummyMessages[dummyChats[0].id]);
  const [isVeeTyping, setIsVeeTyping] = React.useState<boolean>(false);
  const chatWindowRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    setMessages(dummyMessages[selectedChatId]);
  }, [selectedChatId]);

  React.useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages, isVeeTyping]);

  const handleSend = (msg: string) => {
    if (!msg.trim()) return;
    const newMsg: Message = { id: Date.now().toString(), sender: "user", content: msg };
    setMessages((prev: Message[]) => [...prev, newMsg]);
    setIsVeeTyping(true);
    setTimeout(() => {
      setMessages((prev: Message[]) => [
        ...prev,
        { id: Date.now().toString(), sender: "Vee", content: "This is a mock reply from Vee." },
      ]);
      setIsVeeTyping(false);
    }, 1200);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-pink-50">
      <Sidebar
        chats={dummyChats}
        selectedChatId={selectedChatId}
        onSelectChat={setSelectedChatId}
      />
      <div className="flex flex-col flex-1 h-full">
        <div className="flex justify-end items-center p-4 gap-3">
          <img
            src="https://randomuser.me/api/portraits/men/32.jpg"
            alt="User Avatar"
            className="w-8 h-8 rounded-full shadow"
          />
          <button className="px-3 py-1 rounded bg-pink-200 hover:bg-pink-300 text-pink-900 shadow">Logout</button>
        </div>
        <ChatHeader
          title={dummyChats.find((c) => c.id === selectedChatId)?.title || "Chat"}
        />
        <div
          ref={chatWindowRef}
          className="flex-1 overflow-y-auto px-4 py-2 space-y-2"
          style={{ scrollBehavior: "smooth" }}
        >
          {messages.map((msg: Message) => (
            <MessageBubble key={msg.id} sender={msg.sender} content={msg.content} />
          ))}
          {isVeeTyping && (
            <MessageBubble sender="Vee" content={<span className="animate-pulse">Vee is typing...</span>} />
          )}
        </div>
        <div className="p-4">
          <ChatInput onSend={handleSend} />
        </div>
      </div>
    </div>
  );
}
