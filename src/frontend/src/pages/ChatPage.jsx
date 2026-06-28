import React from "react";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import ChatWindow from "../components/Chat/ChatWindow";
import Sidebar from "../components/Chat/Sidebar";

const ChatPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="chat-page">
      <div className="chat-layout">
        <Sidebar onLogout={handleLogout} />
        <ChatWindow />
      </div>
    </div>
  );
};

export default ChatPage;
