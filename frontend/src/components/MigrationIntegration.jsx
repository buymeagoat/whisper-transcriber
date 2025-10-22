/**
 * T030 User Preferences Enhancement: Migration Integration Component
 * Integrates migration system with main settings interfaces
 */

import React, { useState, useEffect } from 'react';
import settingsMigrationService from '../services/settingsMigrationService.js';
import SettingsMigrationManager from './SettingsMigrationManager.jsx';

const MigrationIntegration = ({ children }) => {
  const [showMigrationDialog, setShowMigrationDialog] = useState(false);
  const [migrationNeeded, setMigrationNeeded] = useState(false);
  const [migrationStatus, setMigrationStatus] = useState(null);
  const [notification, setNotification] = useState(null);
  
  useEffect(() => {
    // Initialize migration monitoring
    const initializeMigration = async () => {
      try {
        // Check for pending migrations
        await settingsMigrationService.checkForPendingMigrations();
        
        // Get current status
        const status = settingsMigrationService.getMigrationStatus();
        setMigrationStatus(status);
        
        // Check if migration is needed
        if (status.currentVersion !== status.targetVersion) {
          setMigrationNeeded(true);
          
          // Show notification for available upgrade
          setNotification({
            type: 'info',
            title: 'Settings Update Available',
            message: `Your settings can be upgraded from ${status.currentVersion} to ${status.targetVersion}`,
            actions: [
              {
                label: 'Upgrade Now',
                action: () => handleAutoMigrate(),
                primary: true
              },
              {
                label: 'Manage',
                action: () => setShowMigrationDialog(true)
              },
              {
                label: 'Later',
                action: () => setNotification(null)
              }
            ]
          });
        }
      } catch (error) {
        console.error('Migration initialization failed:', error);
      }
    };
    
    // Subscribe to migration events
    const unsubscribe = settingsMigrationService.subscribe(handleMigrationEvent);
    
    initializeMigration();
    
    return () => {
      unsubscribe();
    };
  }, []);
  
  const handleMigrationEvent = (event, data) => {
    switch (event) {
      case 'migration-needed':
        setMigrationNeeded(true);
        setNotification({
          type: 'info',
          title: 'Migration Required',
          message: `Settings migration available: ${data.from} → ${data.to}`,
          actions: [
            {
              label: 'Start Migration',
              action: () => handleAutoMigrate(),
              primary: true
            },
            {
              label: 'View Details',
              action: () => setShowMigrationDialog(true)
            }
          ]
        });
        break;
        
      case 'migration-completed':
        setMigrationNeeded(false);
        setNotification({
          type: 'success',
          title: 'Migration Completed',
          message: `Settings successfully upgraded to ${data.toVersion}`,
          autoClose: 5000
        });
        break;
        
      case 'migration-failed':
        setNotification({
          type: 'error',
          title: 'Migration Failed',
          message: data.error,
          actions: [
            {
              label: 'Retry',
              action: () => handleAutoMigrate()
            },
            {
              label: 'Manual Migration',
              action: () => setShowMigrationDialog(true)
            }
          ]
        });
        break;
        
      case 'validation-failed':
        setNotification({
          type: 'warning',
          title: 'Settings Validation Failed',
          message: 'Some settings may be corrupted or outdated',
          actions: [
            {
              label: 'Fix Issues',
              action: () => setShowMigrationDialog(true),
              primary: true
            }
          ]
        });
        break;
    }
  };
  
  const handleAutoMigrate = async () => {
    try {
      setNotification({
        type: 'info',
        title: 'Migration In Progress',
        message: 'Please wait while your settings are being upgraded...',
        loading: true
      });
      
      await settingsMigrationService.forceMigration();
    } catch (error) {
      console.error('Auto-migration failed:', error);
    }
  };
  
  const renderNotification = () => {
    if (!notification) return null;
    
    return (
      <div className={`migration-notification notification-${notification.type}`}>
        <div className="notification-content">
          <div className="notification-header">
            <h4>{notification.title}</h4>
            {!notification.loading && (
              <button 
                onClick={() => setNotification(null)}
                className="notification-close"
                aria-label="Close notification"
              >
                ✕
              </button>
            )}
          </div>
          
          <p>{notification.message}</p>
          
          {notification.actions && (
            <div className="notification-actions">
              {notification.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.action}
                  className={`notification-btn ${action.primary ? 'primary' : 'secondary'}`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
          
          {notification.loading && (
            <div className="notification-loading">
              <div className="loading-spinner"></div>
            </div>
          )}
        </div>
      </div>
    );
  };
  
  // Auto-close notifications
  useEffect(() => {
    if (notification?.autoClose) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, notification.autoClose);
      
      return () => clearTimeout(timer);
    }
  }, [notification]);
  
  return (
    <div className="migration-integration">
      {/* Migration status indicator for developers */}
      {process.env.NODE_ENV === 'development' && migrationStatus && (
        <div className="migration-dev-status">
          <span>Migration: {migrationStatus.currentVersion} → {migrationStatus.targetVersion}</span>
          {migrationNeeded && <span className="status-indicator">!</span>}
          <button onClick={() => setShowMigrationDialog(true)}>Manage</button>
        </div>
      )}
      
      {/* Main content */}
      {children}
      
      {/* Migration notification */}
      {renderNotification()}
      
      {/* Migration manager dialog */}
      {showMigrationDialog && (
        <SettingsMigrationManager 
          onClose={() => setShowMigrationDialog(false)}
        />
      )}
      
      <style jsx>{`
        .migration-integration {
          position: relative;
        }
        
        .migration-dev-status {
          position: fixed;
          bottom: 20px;
          right: 20px;
          background: #1f2937;
          color: white;
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 0.8rem;
          font-family: monospace;
          z-index: 1000;
          display: flex;
          align-items: center;
          gap: 8px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        .migration-dev-status button {
          background: #3b82f6;
          color: white;
          border: none;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 0.7rem;
          cursor: pointer;
        }
        
        .status-indicator {
          background: #ef4444;
          color: white;
          border-radius: 50%;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.7rem;
          font-weight: bold;
        }
        
        .migration-notification {
          position: fixed;
          top: 20px;
          right: 20px;
          max-width: 400px;
          border-radius: 8px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
          z-index: 1000;
          animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        .notification-info {
          background: #dbeafe;
          border: 1px solid #93c5fd;
          color: #1e40af;
        }
        
        .notification-success {
          background: #dcfce7;
          border: 1px solid #86efac;
          color: #166534;
        }
        
        .notification-warning {
          background: #fef3c7;
          border: 1px solid #fcd34d;
          color: #92400e;
        }
        
        .notification-error {
          background: #fecaca;
          border: 1px solid #fca5a5;
          color: #991b1b;
        }
        
        .notification-content {
          padding: 16px;
        }
        
        .notification-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;
        }
        
        .notification-header h4 {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
        }
        
        .notification-close {
          background: none;
          border: none;
          font-size: 1.2rem;
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          opacity: 0.7;
          transition: opacity 0.2s ease;
        }
        
        .notification-close:hover {
          opacity: 1;
        }
        
        .notification-content p {
          margin: 0 0 12px 0;
          font-size: 0.9rem;
          line-height: 1.4;
        }
        
        .notification-actions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        
        .notification-btn {
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          font-size: 0.85rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        
        .notification-btn.primary {
          background: currentColor;
          color: white;
        }
        
        .notification-btn.secondary {
          background: transparent;
          color: currentColor;
          border: 1px solid currentColor;
        }
        
        .notification-btn:hover {
          opacity: 0.8;
          transform: translateY(-1px);
        }
        
        .notification-loading {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-top: 12px;
        }
        
        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid transparent;
          border-top: 2px solid currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
          .migration-notification {
            top: 10px;
            right: 10px;
            left: 10px;
            max-width: none;
          }
          
          .migration-dev-status {
            bottom: 10px;
            right: 10px;
            left: 10px;
            justify-content: center;
          }
          
          .notification-actions {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default MigrationIntegration;