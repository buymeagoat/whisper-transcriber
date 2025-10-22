/**
 * T036: Real-time Collaboration Features - Comment Panel Component
 * Component for displaying and managing comments and annotations.
 */

import React, { useState, useEffect } from 'react';
import './CommentPanel.css';

interface User {
  id: number;
  username: string;
  avatar?: string;
  color: string;
}

interface Comment {
  id: string;
  content: string;
  comment_type: string;
  status: string;
  author_id: number;
  author_name: string;
  parent_id?: string;
  start_position?: number;
  end_position?: number;
  line_number?: number;
  selected_text?: string;
  created_at: string;
  updated_at: string;
  replies?: Comment[];
  reactions?: Array<{ type: string; count: number; users: string[] }>;
}

interface Annotation {
  id: string;
  annotation_type: string;
  start_position: number;
  end_position: number;
  selected_text: string;
  title: string;
  content: string;
  color: string;
  author_id: number;
  author_name: string;
  is_visible: boolean;
  created_at: string;
  updated_at: string;
}

interface CommentPanelProps {
  documentId: string;
  currentUser: User;
  selectedText?: { start: number; end: number; text: string } | null;
  onCommentAdded?: () => void;
}

export const CommentPanel: React.FC<CommentPanelProps> = ({
  documentId,
  currentUser,
  selectedText,
  onCommentAdded
}) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'comments' | 'annotations'>('comments');
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [newReply, setNewReply] = useState('');

  useEffect(() => {
    fetchComments();
    fetchAnnotations();
  }, [documentId]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/documents/${documentId}/comments`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setComments(data.comments || []);
      }
    } catch (error) {
      console.error('Error fetching comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnnotations = async () => {
    try {
      const response = await fetch(`/api/v1/documents/${documentId}/annotations`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAnnotations(data.annotations || []);
      }
    } catch (error) {
      console.error('Error fetching annotations:', error);
    }
  };

  const createComment = async () => {
    if (!newComment.trim()) return;

    try {
      const payload: any = {
        content: newComment,
        comment_type: 'general'
      };

      if (selectedText) {
        payload.start_position = selectedText.start;
        payload.end_position = selectedText.end;
        payload.selected_text = selectedText.text;
      }

      const response = await fetch(`/api/v1/documents/${documentId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setNewComment('');
        fetchComments();
        onCommentAdded?.();
      }
    } catch (error) {
      console.error('Error creating comment:', error);
    }
  };

  const createReply = async (parentId: string) => {
    if (!newReply.trim()) return;

    try {
      const response = await fetch(`/api/v1/documents/${documentId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          content: newReply,
          comment_type: 'general',
          parent_id: parentId
        })
      });

      if (response.ok) {
        setNewReply('');
        setReplyingTo(null);
        fetchComments();
      }
    } catch (error) {
      console.error('Error creating reply:', error);
    }
  };

  const resolveComment = async (commentId: string) => {
    try {
      const response = await fetch(`/api/v1/comments/${commentId}/resolve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        fetchComments();
      }
    } catch (error) {
      console.error('Error resolving comment:', error);
    }
  };

  const addReaction = async (commentId: string, reactionType: string) => {
    try {
      const response = await fetch(`/api/v1/comments/${commentId}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ reaction_type: reactionType })
      });

      if (response.ok) {
        fetchComments();
      }
    } catch (error) {
      console.error('Error adding reaction:', error);
    }
  };

  const createAnnotation = async (type: string, color: string) => {
    if (!selectedText) return;

    try {
      const response = await fetch(`/api/v1/documents/${documentId}/annotations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          annotation_type: type,
          start_position: selectedText.start,
          end_position: selectedText.end,
          selected_text: selectedText.text,
          color: color,
          title: `${type} annotation`,
          content: ''
        })
      });

      if (response.ok) {
        fetchAnnotations();
      }
    } catch (error) {
      console.error('Error creating annotation:', error);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const getCommentTypeIcon = (type: string) => {
    switch (type) {
      case 'suggestion': return '💡';
      case 'question': return '❓';
      case 'approval': return '✅';
      case 'correction': return '✏️';
      default: return '💬';
    }
  };

  const getAnnotationTypeIcon = (type: string) => {
    switch (type) {
      case 'highlight': return '🖍️';
      case 'note': return '📝';
      case 'bookmark': return '🔖';
      case 'task': return '☑️';
      case 'issue': return '⚠️';
      default: return '📌';
    }
  };

  return (
    <div className="comment-panel">
      <div className="panel-header">
        <div className="panel-tabs">
          <button
            className={`tab ${activeTab === 'comments' ? 'active' : ''}`}
            onClick={() => setActiveTab('comments')}
          >
            💬 Comments ({comments.length})
          </button>
          <button
            className={`tab ${activeTab === 'annotations' ? 'active' : ''}`}
            onClick={() => setActiveTab('annotations')}
          >
            📌 Annotations ({annotations.length})
          </button>
        </div>
      </div>

      <div className="panel-content">
        {activeTab === 'comments' && (
          <div className="comments-section">
            <div className="new-comment">
              <textarea
                className="comment-input"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder={selectedText ? 
                  `Comment on "${selectedText.text.slice(0, 50)}..."` : 
                  "Add a comment..."
                }
                rows={3}
              />
              <div className="comment-actions">
                {selectedText && (
                  <span className="selected-text-indicator">
                    📄 Commenting on selected text
                  </span>
                )}
                <button
                  className="submit-comment"
                  onClick={createComment}
                  disabled={!newComment.trim()}
                >
                  💬 Comment
                </button>
              </div>
            </div>

            <div className="comments-list">
              {loading ? (
                <div className="loading">Loading comments...</div>
              ) : comments.length === 0 ? (
                <div className="empty-state">
                  <p>No comments yet</p>
                  <p>Be the first to add a comment!</p>
                </div>
              ) : (
                comments.map(comment => (
                  <div key={comment.id} className={`comment ${comment.status}`}>
                    <div className="comment-header">
                      <div className="comment-author">
                        <span className="author-name">{comment.author_name}</span>
                        <span className="comment-time">{formatTimestamp(comment.created_at)}</span>
                      </div>
                      <div className="comment-meta">
                        <span className="comment-type">
                          {getCommentTypeIcon(comment.comment_type)}
                        </span>
                        {comment.status === 'resolved' && (
                          <span className="resolved-badge">✅ Resolved</span>
                        )}
                      </div>
                    </div>

                    {comment.selected_text && (
                      <div className="quoted-text">
                        <div className="quote-marker">📄</div>
                        <div className="quote-content">"{comment.selected_text}"</div>
                      </div>
                    )}

                    <div className="comment-content">{comment.content}</div>

                    <div className="comment-footer">
                      <div className="comment-reactions">
                        <button
                          className="reaction-button"
                          onClick={() => addReaction(comment.id, 'like')}
                        >
                          👍
                        </button>
                        <button
                          className="reaction-button"
                          onClick={() => addReaction(comment.id, 'heart')}
                        >
                          ❤️
                        </button>
                      </div>

                      <div className="comment-actions-footer">
                        <button
                          className="reply-button"
                          onClick={() => setReplyingTo(comment.id)}
                        >
                          💬 Reply
                        </button>
                        {comment.status !== 'resolved' && (
                          <button
                            className="resolve-button"
                            onClick={() => resolveComment(comment.id)}
                          >
                            ✅ Resolve
                          </button>
                        )}
                      </div>
                    </div>

                    {replyingTo === comment.id && (
                      <div className="reply-form">
                        <textarea
                          className="reply-input"
                          value={newReply}
                          onChange={(e) => setNewReply(e.target.value)}
                          placeholder="Write a reply..."
                          rows={2}
                        />
                        <div className="reply-actions">
                          <button
                            className="cancel-reply"
                            onClick={() => {
                              setReplyingTo(null);
                              setNewReply('');
                            }}
                          >
                            Cancel
                          </button>
                          <button
                            className="submit-reply"
                            onClick={() => createReply(comment.id)}
                            disabled={!newReply.trim()}
                          >
                            💬 Reply
                          </button>
                        </div>
                      </div>
                    )}

                    {comment.replies && comment.replies.length > 0 && (
                      <div className="replies">
                        {comment.replies.map(reply => (
                          <div key={reply.id} className="reply">
                            <div className="reply-header">
                              <span className="reply-author">{reply.author_name}</span>
                              <span className="reply-time">{formatTimestamp(reply.created_at)}</span>
                            </div>
                            <div className="reply-content">{reply.content}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'annotations' && (
          <div className="annotations-section">
            {selectedText && (
              <div className="annotation-tools">
                <h4>Add Annotation</h4>
                <div className="annotation-buttons">
                  <button
                    className="annotation-btn highlight"
                    onClick={() => createAnnotation('highlight', '#FFD700')}
                  >
                    🖍️ Highlight
                  </button>
                  <button
                    className="annotation-btn note"
                    onClick={() => createAnnotation('note', '#87CEEB')}
                  >
                    📝 Note
                  </button>
                  <button
                    className="annotation-btn bookmark"
                    onClick={() => createAnnotation('bookmark', '#FF6B6B')}
                  >
                    🔖 Bookmark
                  </button>
                </div>
              </div>
            )}

            <div className="annotations-list">
              {annotations.length === 0 ? (
                <div className="empty-state">
                  <p>No annotations yet</p>
                  <p>Select text to add annotations</p>
                </div>
              ) : (
                annotations.map(annotation => (
                  <div key={annotation.id} className="annotation">
                    <div className="annotation-header">
                      <span className="annotation-type">
                        {getAnnotationTypeIcon(annotation.annotation_type)}
                      </span>
                      <span className="annotation-title">{annotation.title}</span>
                      <div
                        className="annotation-color"
                        style={{ backgroundColor: annotation.color }}
                      />
                    </div>
                    
                    <div className="annotation-text">
                      "{annotation.selected_text}"
                    </div>
                    
                    {annotation.content && (
                      <div className="annotation-content">{annotation.content}</div>
                    )}
                    
                    <div className="annotation-footer">
                      <span className="annotation-author">{annotation.author_name}</span>
                      <span className="annotation-time">{formatTimestamp(annotation.created_at)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CommentPanel;