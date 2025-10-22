/**
 * T036: Real-time Collaboration Features - User Presence Component
 * Displays real-time user presence indicators for collaborative editing.
 */

import React, { useState, useEffect } from 'react';
import './UserPresence.css';

interface User {
  id: number;
  username: string;
  avatar?: string;
  color: string;
}

interface UserPresenceData {
  user: User;
  isOnline: boolean;
  lastSeen?: string;
  cursor?: {
    position: number;
    selection?: { start: number; end: number };
  };
  activeDocument?: string;
}

interface UserPresenceProps {
  sessionId: string;
  currentUser: User;
  websocket?: WebSocket;
  onUserClick?: (user: User) => void;
}

export const UserPresence: React.FC<UserPresenceProps> = ({
  sessionId,
  currentUser,
  websocket,
  onUserClick
}) => {
  const [activeUsers, setActiveUsers] = useState<Map<number, UserPresenceData>>(new Map());
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!websocket) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'user_joined':
            handleUserJoined(message.data);
            break;
          case 'user_left':
            handleUserLeft(message.data);
            break;
          case 'user_presence_update':
            handlePresenceUpdate(message.data);
            break;
          case 'cursor_update':
            handleCursorUpdate(message.data);
            break;
          case 'connection_established':
            setIsConnected(true);
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    const handleOpen = () => {
      setIsConnected(true);
      // Send initial presence
      websocket.send(JSON.stringify({
        type: 'join_session',
        data: {
          session_id: sessionId,
          user: currentUser
        }
      }));
    };

    const handleClose = () => {
      setIsConnected(false);
    };

    websocket.addEventListener('message', handleMessage);
    websocket.addEventListener('open', handleOpen);
    websocket.addEventListener('close', handleClose);

    return () => {
      websocket.removeEventListener('message', handleMessage);
      websocket.removeEventListener('open', handleOpen);
      websocket.removeEventListener('close', handleClose);
    };
  }, [websocket, sessionId, currentUser]);

  const handleUserJoined = (data: { user: User; session_id: string }) => {
    if (data.session_id === sessionId) {
      setActiveUsers(prev => new Map(prev).set(data.user.id, {
        user: data.user,
        isOnline: true,
        lastSeen: new Date().toISOString()
      }));
    }
  };

  const handleUserLeft = (data: { user_id: number; session_id: string }) => {
    if (data.session_id === sessionId) {
      setActiveUsers(prev => {
        const updated = new Map(prev);
        const userData = updated.get(data.user_id);
        if (userData) {
          updated.set(data.user_id, {
            ...userData,
            isOnline: false,
            lastSeen: new Date().toISOString()
          });
        }
        return updated;
      });
    }
  };

  const handlePresenceUpdate = (data: { user_id: number; session_id: string; active_document?: string }) => {
    if (data.session_id === sessionId) {
      setActiveUsers(prev => {
        const updated = new Map(prev);
        const userData = updated.get(data.user_id);
        if (userData) {
          updated.set(data.user_id, {
            ...userData,
            activeDocument: data.active_document,
            lastSeen: new Date().toISOString()
          });
        }
        return updated;
      });
    }
  };

  const handleCursorUpdate = (data: { 
    user_id: number; 
    session_id: string; 
    cursor_position: number;
    selection?: { start: number; end: number };
  }) => {
    if (data.session_id === sessionId && data.user_id !== currentUser.id) {
      setActiveUsers(prev => {
        const updated = new Map(prev);
        const userData = updated.get(data.user_id);
        if (userData) {
          updated.set(data.user_id, {
            ...userData,
            cursor: {
              position: data.cursor_position,
              selection: data.selection
            }
          });
        }
        return updated;
      });
    }
  };

  const sendCursorUpdate = (position: number, selection?: { start: number; end: number }) => {
    if (websocket && isConnected) {
      websocket.send(JSON.stringify({
        type: 'cursor_update',
        data: {
          session_id: sessionId,
          cursor_position: position,
          selection
        }
      }));
    }
  };

  const getActiveUsersArray = () => {
    return Array.from(activeUsers.values()).filter(userData => userData.isOnline);
  };

  const formatLastSeen = (lastSeen: string) => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const activeUsersArray = getActiveUsersArray();

  return (
    <div className="user-presence">
      <div className="presence-header">
        <div className="connection-status">
          <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
          <span className="status-text">
            {isConnected ? 'Connected' : 'Connecting...'}
          </span>
        </div>
        <div className="active-count">
          {activeUsersArray.length} active
        </div>
      </div>

      <div className="users-list">
        {activeUsersArray.map(userData => (
          <div 
            key={userData.user.id}
            className="user-item"
            onClick={() => onUserClick?.(userData.user)}
            title={`${userData.user.username} - ${formatLastSeen(userData.lastSeen!)}`}
          >
            <div 
              className="user-avatar"
              style={{ backgroundColor: userData.user.color }}
            >
              {userData.user.avatar ? (
                <img src={userData.user.avatar} alt={userData.user.username} />
              ) : (
                <span className="avatar-initials">
                  {userData.user.username.charAt(0).toUpperCase()}
                </span>
              )}
            </div>
            
            <div className="user-info">
              <div className="username">{userData.user.username}</div>
              <div className="user-status">
                {userData.activeDocument && (
                  <span className="active-document">
                    Editing document
                  </span>
                )}
              </div>
            </div>
            
            <div className="presence-indicator online" />
          </div>
        ))}
      </div>

      {activeUsersArray.length === 0 && (
        <div className="no-users">
          <p>No other users currently active</p>
          <p className="invite-hint">Invite collaborators to get started</p>
        </div>
      )}
    </div>
  );
};

export default UserPresence;