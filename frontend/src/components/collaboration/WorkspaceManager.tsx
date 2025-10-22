/**
 * T036: Real-time Collaboration Features - Workspace Manager Component
 * Component for managing collaborative workspaces, projects, and team members.
 */

import React, { useState, useEffect } from 'react';
import './WorkspaceManager.css';

interface User {
  id: number;
  username: string;
  email: string;
  avatar?: string;
}

interface WorkspaceMember {
  user_id: number;
  username: string;
  email: string;
  role: 'owner' | 'admin' | 'editor' | 'viewer' | 'guest';
}

interface Workspace {
  id: string;
  name: string;
  description: string;
  status: string;
  role: string;
  member_count?: number;
  project_count?: number;
  created_at: string;
  updated_at: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
  project_type: string;
  status: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

interface WorkspaceManagerProps {
  currentUser: User;
  onWorkspaceSelect?: (workspace: Workspace) => void;
  onProjectSelect?: (project: Project) => void;
}

export const WorkspaceManager: React.FC<WorkspaceManagerProps> = ({
  currentUser,
  onWorkspaceSelect,
  onProjectSelect
}) => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [activeTab, setActiveTab] = useState<'projects' | 'members' | 'settings'>('projects');
  const [showCreateWorkspace, setShowCreateWorkspace] = useState(false);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showInviteUser, setShowInviteUser] = useState(false);
  const [loading, setLoading] = useState(false);

  // Form states
  const [newWorkspace, setNewWorkspace] = useState({ name: '', description: '' });
  const [newProject, setNewProject] = useState({ name: '', description: '', project_type: 'transcription' });
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<string>('editor');

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  useEffect(() => {
    if (selectedWorkspace) {
      fetchWorkspaceData();
    }
  }, [selectedWorkspace]);

  const fetchWorkspaces = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/workspaces', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setWorkspaces(data.workspaces || []);
        
        // Auto-select first workspace if none selected
        if (data.workspaces?.length > 0 && !selectedWorkspace) {
          setSelectedWorkspace(data.workspaces[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching workspaces:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkspaceData = async () => {
    if (!selectedWorkspace) return;

    try {
      // Fetch projects, members, and detailed workspace info in parallel
      const [projectsRes, membersRes] = await Promise.all([
        fetch(`/api/v1/workspaces/${selectedWorkspace.id}/projects`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`/api/v1/workspaces/${selectedWorkspace.id}/members`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (projectsRes.ok) {
        const projectsData = await projectsRes.json();
        setProjects(projectsData.projects || []);
      }

      if (membersRes.ok) {
        const membersData = await membersRes.json();
        setMembers(membersData.members || []);
      }
    } catch (error) {
      console.error('Error fetching workspace data:', error);
    }
  };

  const createWorkspace = async () => {
    if (!newWorkspace.name.trim()) return;

    try {
      const response = await fetch('/api/v1/workspaces/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newWorkspace)
      });

      if (response.ok) {
        const workspace = await response.json();
        setWorkspaces(prev => [...prev, workspace]);
        setSelectedWorkspace(workspace);
        setShowCreateWorkspace(false);
        setNewWorkspace({ name: '', description: '' });
      }
    } catch (error) {
      console.error('Error creating workspace:', error);
    }
  };

  const createProject = async () => {
    if (!newProject.name.trim() || !selectedWorkspace) return;

    try {
      const response = await fetch(`/api/v1/workspaces/${selectedWorkspace.id}/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newProject)
      });

      if (response.ok) {
        const project = await response.json();
        setProjects(prev => [...prev, project]);
        setShowCreateProject(false);
        setNewProject({ name: '', description: '', project_type: 'transcription' });
      }
    } catch (error) {
      console.error('Error creating project:', error);
    }
  };

  const inviteUser = async () => {
    if (!inviteEmail.trim() || !selectedWorkspace) return;

    try {
      const response = await fetch(`/api/v1/workspaces/${selectedWorkspace.id}/invite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          email: inviteEmail,
          role: inviteRole
        })
      });

      if (response.ok) {
        setShowInviteUser(false);
        setInviteEmail('');
        setInviteRole('editor');
        // Optionally show success message
        alert('Invitation sent successfully!');
      }
    } catch (error) {
      console.error('Error inviting user:', error);
    }
  };

  const handleWorkspaceSelect = (workspace: Workspace) => {
    setSelectedWorkspace(workspace);
    onWorkspaceSelect?.(workspace);
  };

  const handleProjectSelect = (project: Project) => {
    onProjectSelect?.(project);
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'owner': return '#dc2626';
      case 'admin': return '#ea580c';
      case 'editor': return '#2563eb';
      case 'viewer': return '#059669';
      case 'guest': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading && workspaces.length === 0) {
    return (
      <div className="workspace-manager loading">
        <div className="loading-spinner">Loading workspaces...</div>
      </div>
    );
  }

  return (
    <div className="workspace-manager">
      <div className="workspace-sidebar">
        <div className="sidebar-header">
          <h3>Workspaces</h3>
          <button
            className="create-workspace-btn"
            onClick={() => setShowCreateWorkspace(true)}
            title="Create new workspace"
          >
            ➕
          </button>
        </div>

        <div className="workspaces-list">
          {workspaces.map(workspace => (
            <div
              key={workspace.id}
              className={`workspace-item ${selectedWorkspace?.id === workspace.id ? 'selected' : ''}`}
              onClick={() => handleWorkspaceSelect(workspace)}
            >
              <div className="workspace-info">
                <div className="workspace-name">{workspace.name}</div>
                <div className="workspace-meta">
                  <span className="workspace-role" style={{ color: getRoleColor(workspace.role) }}>
                    {workspace.role}
                  </span>
                  <span className="workspace-stats">
                    {workspace.project_count || 0} projects
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="workspace-main">
        {selectedWorkspace ? (
          <>
            <div className="workspace-header">
              <div className="workspace-title">
                <h2>{selectedWorkspace.name}</h2>
                <p className="workspace-description">{selectedWorkspace.description}</p>
              </div>
              <div className="workspace-actions">
                <span className="member-count">👥 {members.length} members</span>
              </div>
            </div>

            <div className="workspace-tabs">
              <button
                className={`tab ${activeTab === 'projects' ? 'active' : ''}`}
                onClick={() => setActiveTab('projects')}
              >
                📁 Projects ({projects.length})
              </button>
              <button
                className={`tab ${activeTab === 'members' ? 'active' : ''}`}
                onClick={() => setActiveTab('members')}
              >
                👥 Members ({members.length})
              </button>
              <button
                className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
                onClick={() => setActiveTab('settings')}
              >
                ⚙️ Settings
              </button>
            </div>

            <div className="workspace-content">
              {activeTab === 'projects' && (
                <div className="projects-section">
                  <div className="section-header">
                    <h3>Projects</h3>
                    <button
                      className="create-project-btn"
                      onClick={() => setShowCreateProject(true)}
                    >
                      ➕ New Project
                    </button>
                  </div>

                  <div className="projects-grid">
                    {projects.length === 0 ? (
                      <div className="empty-state">
                        <p>No projects yet</p>
                        <p>Create your first project to get started</p>
                      </div>
                    ) : (
                      projects.map(project => (
                        <div
                          key={project.id}
                          className="project-card"
                          onClick={() => handleProjectSelect(project)}
                        >
                          <div className="project-header">
                            <h4>{project.name}</h4>
                            <span className="project-type">{project.project_type}</span>
                          </div>
                          <p className="project-description">{project.description}</p>
                          <div className="project-footer">
                            <span className="project-date">Created {formatDate(project.created_at)}</span>
                            <span className={`project-status ${project.status}`}>{project.status}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'members' && (
                <div className="members-section">
                  <div className="section-header">
                    <h3>Members</h3>
                    <button
                      className="invite-user-btn"
                      onClick={() => setShowInviteUser(true)}
                    >
                      ➕ Invite User
                    </button>
                  </div>

                  <div className="members-list">
                    {members.map(member => (
                      <div key={member.user_id} className="member-item">
                        <div className="member-info">
                          <div className="member-avatar">
                            {member.username.charAt(0).toUpperCase()}
                          </div>
                          <div className="member-details">
                            <div className="member-name">{member.username}</div>
                            <div className="member-email">{member.email}</div>
                          </div>
                        </div>
                        <div className="member-role">
                          <span className="role-badge" style={{ backgroundColor: getRoleColor(member.role) }}>
                            {member.role}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'settings' && (
                <div className="settings-section">
                  <h3>Workspace Settings</h3>
                  <div className="settings-content">
                    <div className="setting-group">
                      <label>Workspace Name</label>
                      <input
                        type="text"
                        value={selectedWorkspace.name}
                        readOnly
                        className="setting-input"
                      />
                    </div>
                    <div className="setting-group">
                      <label>Description</label>
                      <textarea
                        value={selectedWorkspace.description}
                        readOnly
                        className="setting-textarea"
                        rows={3}
                      />
                    </div>
                    <div className="setting-group">
                      <label>Created</label>
                      <input
                        type="text"
                        value={formatDate(selectedWorkspace.created_at)}
                        readOnly
                        className="setting-input"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="no-workspace">
            <h3>No Workspace Selected</h3>
            <p>Select a workspace from the sidebar or create a new one</p>
          </div>
        )}
      </div>

      {/* Create Workspace Modal */}
      {showCreateWorkspace && (
        <div className="modal-overlay" onClick={() => setShowCreateWorkspace(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create New Workspace</h3>
              <button className="modal-close" onClick={() => setShowCreateWorkspace(false)}>✕</button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>Workspace Name</label>
                <input
                  type="text"
                  value={newWorkspace.name}
                  onChange={e => setNewWorkspace(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter workspace name"
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newWorkspace.description}
                  onChange={e => setNewWorkspace(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe your workspace"
                  rows={3}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="cancel-btn" onClick={() => setShowCreateWorkspace(false)}>
                Cancel
              </button>
              <button className="create-btn" onClick={createWorkspace} disabled={!newWorkspace.name.trim()}>
                Create Workspace
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateProject && (
        <div className="modal-overlay" onClick={() => setShowCreateProject(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create New Project</h3>
              <button className="modal-close" onClick={() => setShowCreateProject(false)}>✕</button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>Project Name</label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={e => setNewProject(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter project name"
                />
              </div>
              <div className="form-group">
                <label>Project Type</label>
                <select
                  value={newProject.project_type}
                  onChange={e => setNewProject(prev => ({ ...prev, project_type: e.target.value }))}
                >
                  <option value="transcription">Transcription</option>
                  <option value="analysis">Analysis</option>
                  <option value="notes">Notes</option>
                </select>
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newProject.description}
                  onChange={e => setNewProject(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe your project"
                  rows={3}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="cancel-btn" onClick={() => setShowCreateProject(false)}>
                Cancel
              </button>
              <button className="create-btn" onClick={createProject} disabled={!newProject.name.trim()}>
                Create Project
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Invite User Modal */}
      {showInviteUser && (
        <div className="modal-overlay" onClick={() => setShowInviteUser(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Invite User</h3>
              <button className="modal-close" onClick={() => setShowInviteUser(false)}>✕</button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>Email Address</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={e => setInviteEmail(e.target.value)}
                  placeholder="Enter user's email"
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  value={inviteRole}
                  onChange={e => setInviteRole(e.target.value)}
                >
                  <option value="viewer">Viewer</option>
                  <option value="editor">Editor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="cancel-btn" onClick={() => setShowInviteUser(false)}>
                Cancel
              </button>
              <button className="create-btn" onClick={inviteUser} disabled={!inviteEmail.trim()}>
                Send Invitation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkspaceManager;