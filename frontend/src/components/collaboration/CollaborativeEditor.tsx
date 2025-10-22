/**
 * T036: Real-time Collaboration Features - Collaborative Editor Component
 * Main editor component with real-time collaborative editing capabilities.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { UserPresence } from './UserPresence';
import { CommentPanel } from './CommentPanel';
import './CollaborativeEditor.css';

interface User {
  id: number;
  username: string;
  avatar?: string;
  color: string;
}

interface TextOperation {
  type: 'insert' | 'delete' | 'retain';
  position: number;
  content?: string;
  length?: number;
  user_id?: number;
  timestamp?: string;
  operation_id?: string;
}

interface CursorPosition {
  user: User;
  position: number;
  selection?: { start: number; end: number };
}

interface CollaborativeEditorProps {
  documentId: string;
  initialContent: string;
  currentUser: User;
  websocketUrl: string;
  onSave?: (content: string) => void;
  readOnly?: boolean;
}

export const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  documentId,
  initialContent,
  currentUser,
  websocketUrl,
  onSave,
  readOnly = false
}) => {
  const [content, setContent] = useState(initialContent);
  const [isConnected, setIsConnected] = useState(false);
  const [cursors, setCursors] = useState<Map<number, CursorPosition>>(new Map());
  const [showComments, setShowComments] = useState(false);
  const [selectedText, setSelectedText] = useState<{ start: number; end: number; text: string } | null>(null);
  
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const lastCursorPosition = useRef<number>(0);
  const isTyping = useRef(false);

  // Initialize WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(`${websocketUrl}?document_id=${documentId}&user_id=${currentUser.id}`);
      websocketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
        
        // Join document session
        ws.send(JSON.stringify({
          type: 'join_document',
          data: {
            document_id: documentId,
            user: currentUser
          }
        }));
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');
        
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onmessage = handleWebSocketMessage;
    };

    connectWebSocket();

    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [documentId, currentUser, websocketUrl]);

  const handleWebSocketMessage = (event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'document_operation':
          handleRemoteOperation(message.data);
          break;
        case 'cursor_update':
          handleCursorUpdate(message.data);
          break;
        case 'document_sync':
          handleDocumentSync(message.data);
          break;
        case 'user_joined_document':
          console.log('User joined document:', message.data);
          break;
        case 'user_left_document':
          handleUserLeft(message.data);
          break;
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  const handleRemoteOperation = (operation: TextOperation) => {
    if (operation.user_id === currentUser.id) {
      return; // Ignore our own operations
    }

    applyOperation(operation);
  };

  const applyOperation = (operation: TextOperation) => {
    setContent(prevContent => {
      let newContent = prevContent;
      
      switch (operation.type) {
        case 'insert':
          if (operation.content && operation.position >= 0) {
            newContent = 
              prevContent.slice(0, operation.position) + 
              operation.content + 
              prevContent.slice(operation.position);
          }
          break;
        case 'delete':
          if (operation.position >= 0 && operation.length) {
            newContent = 
              prevContent.slice(0, operation.position) + 
              prevContent.slice(operation.position + operation.length);
          }
          break;
      }
      
      return newContent;
    });
  };

  const handleCursorUpdate = (data: { user_id: number; user: User; position: number; selection?: { start: number; end: number } }) => {
    if (data.user_id !== currentUser.id) {
      setCursors(prev => {
        const updated = new Map(prev);
        updated.set(data.user_id, {
          user: data.user,
          position: data.position,
          selection: data.selection
        });
        return updated;
      });
    }
  };

  const handleUserLeft = (data: { user_id: number }) => {
    setCursors(prev => {
      const updated = new Map(prev);
      updated.delete(data.user_id);
      return updated;
    });
  };

  const handleDocumentSync = (data: { content: string; version: number }) => {
    setContent(data.content);
  };

  const sendOperation = (operation: TextOperation) => {
    if (websocketRef.current && isConnected) {
      websocketRef.current.send(JSON.stringify({
        type: 'document_operation',
        data: {
          document_id: documentId,
          operation: {
            ...operation,
            user_id: currentUser.id,
            timestamp: new Date().toISOString()
          }
        }
      }));
    }
  };

  const sendCursorUpdate = useCallback((position: number, selection?: { start: number; end: number }) => {
    if (websocketRef.current && isConnected) {
      websocketRef.current.send(JSON.stringify({
        type: 'cursor_update',
        data: {
          document_id: documentId,
          position,
          selection,
          user: currentUser
        }
      }));
    }
  }, [documentId, currentUser, isConnected]);

  const handleTextChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (readOnly) return;

    const newContent = event.target.value;
    const cursorPosition = event.target.selectionStart;
    
    // Calculate the operation
    const operation = calculateOperation(content, newContent, cursorPosition);
    
    if (operation) {
      // Apply locally first for immediate feedback
      setContent(newContent);
      
      // Send to other users
      sendOperation(operation);
      
      // Update cursor position
      lastCursorPosition.current = cursorPosition;
      sendCursorUpdate(cursorPosition);
    }
  };

  const calculateOperation = (oldContent: string, newContent: string, cursorPosition: number): TextOperation | null => {
    if (oldContent === newContent) return null;

    if (newContent.length > oldContent.length) {
      // Insert operation
      const insertPosition = cursorPosition - (newContent.length - oldContent.length);
      const insertedText = newContent.slice(insertPosition, cursorPosition);
      
      return {
        type: 'insert',
        position: insertPosition,
        content: insertedText
      };
    } else {
      // Delete operation
      const deleteLength = oldContent.length - newContent.length;
      
      return {
        type: 'delete',
        position: cursorPosition,
        length: deleteLength
      };
    }
  };

  const handleSelectionChange = () => {
    if (!editorRef.current) return;

    const start = editorRef.current.selectionStart;
    const end = editorRef.current.selectionEnd;
    
    // Update cursor position for other users
    if (start === end) {
      sendCursorUpdate(start);
      setSelectedText(null);
    } else {
      sendCursorUpdate(start, { start, end });
      setSelectedText({
        start,
        end,
        text: content.slice(start, end)
      });
    }
    
    lastCursorPosition.current = start;
  };

  const handleSave = () => {
    if (onSave) {
      onSave(content);
    }
  };

  const renderCursors = () => {
    if (!editorRef.current) return null;

    const cursorsArray = Array.from(cursors.values());
    
    return cursorsArray.map(cursor => (
      <div
        key={cursor.user.id}
        className="remote-cursor"
        style={{
          backgroundColor: cursor.user.color,
          // Position calculation would need more sophisticated text measurement
          // This is a simplified version
        }}
        title={`${cursor.user.username}'s cursor`}
      >
        <div className="cursor-label" style={{ backgroundColor: cursor.user.color }}>
          {cursor.user.username}
        </div>
      </div>
    ));
  };

  return (
    <div className="collaborative-editor">
      <div className="editor-header">
        <div className="editor-title">
          <h3>Collaborative Document</h3>
          <div className="connection-status">
            <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
        
        <div className="editor-actions">
          <button
            className="comment-toggle"
            onClick={() => setShowComments(!showComments)}
            title="Toggle comments"
          >
            💬 Comments
          </button>
          
          <button
            className="save-button"
            onClick={handleSave}
            disabled={!isConnected}
            title="Save document"
          >
            💾 Save
          </button>
        </div>
      </div>

      <div className="editor-container">
        <div className="editor-main">
          <div className="text-editor-container">
            <textarea
              ref={editorRef}
              className="text-editor"
              value={content}
              onChange={handleTextChange}
              onSelect={handleSelectionChange}
              onKeyUp={handleSelectionChange}
              onClick={handleSelectionChange}
              readOnly={readOnly}
              placeholder="Start typing to collaborate..."
            />
            {renderCursors()}
          </div>
          
          {selectedText && (
            <div className="selection-actions">
              <button
                className="add-comment-button"
                onClick={() => {
                  // This would open a comment dialog
                  console.log('Add comment to:', selectedText);
                }}
              >
                💬 Add Comment
              </button>
              
              <button
                className="highlight-button"
                onClick={() => {
                  // This would add a highlight annotation
                  console.log('Highlight:', selectedText);
                }}
              >
                🖍️ Highlight
              </button>
            </div>
          )}
        </div>

        <div className="editor-sidebar">
          <UserPresence
            sessionId={documentId}
            currentUser={currentUser}
            websocket={websocketRef.current || undefined}
          />
          
          {showComments && (
            <CommentPanel
              documentId={documentId}
              currentUser={currentUser}
              selectedText={selectedText}
              onCommentAdded={() => {
                // Refresh comments or handle new comment
                console.log('Comment added');
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default CollaborativeEditor;