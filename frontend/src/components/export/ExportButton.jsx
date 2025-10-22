/**
 * T022: Multi-Format Export System - Export Button Component
 * 
 * Reusable button component for triggering transcript exports
 * with format selection and download functionality.
 */

import React, { useState } from 'react';
import {
  Button,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  CircularProgress,
  Typography,
  Divider
} from '@mui/material';
import {
  Download as DownloadIcon,
  MoreVert as MoreVertIcon,
  Description as DescriptionIcon,
  FileDownload as FileDownloadIcon
} from '@mui/icons-material';

import transcriptExportService, { EXPORT_FORMATS } from '../services/transcriptExportService';
import ExportDialog from './ExportDialog';

const ExportButton = ({
  job,
  variant = 'icon', // 'icon', 'button', 'menu'
  size = 'medium',
  disabled = false,
  onExportStart,
  onExportComplete,
  onExportError,
  showFormats = false
}) => {
  // State management
  const [anchorEl, setAnchorEl] = useState(null);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [availableFormats, setAvailableFormats] = useState([]);

  const handleClick = async (event) => {
    if (variant === 'menu' || showFormats) {
      setAnchorEl(event.currentTarget);
      
      // Load available formats if not loaded
      if (availableFormats.length === 0) {
        try {
          const formats = await transcriptExportService.getAvailableFormats();
          setAvailableFormats(formats.filter(f => transcriptExportService.isFormatAvailable(f)));
        } catch (error) {
          console.error('Error loading formats:', error);
          if (onExportError) {
            onExportError(error.message || 'Failed to load export formats');
          }
        }
      }
    } else {
      // Open export dialog directly
      handleOpenDialog();
    }
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleOpenDialog = () => {
    setExportDialogOpen(true);
    handleClose();
  };

  const handleQuickExport = async (format) => {
    if (!job || !format) return;
    
    setLoading(true);
    handleClose();
    
    if (onExportStart) {
      onExportStart(format);
    }
    
    try {
      await transcriptExportService.downloadExport(job.id, format);
      
      if (onExportComplete) {
        onExportComplete(format, null, job);
      }
    } catch (error) {
      console.error('Error in quick export:', error);
      if (onExportError) {
        onExportError(error.message || 'Export failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDialogExportComplete = (format, template) => {
    setExportDialogOpen(false);
    if (onExportComplete) {
      onExportComplete(format, template, job);
    }
  };

  const isJobReady = job && job.status === 'completed';
  const isDisabled = disabled || !isJobReady || loading;

  const renderButton = () => {
    const commonProps = {
      disabled: isDisabled,
      onClick: handleClick
    };

    if (variant === 'icon') {
      return (
        <Tooltip title={isJobReady ? "Export transcript" : "Job must be completed to export"}>
          <span>
            <IconButton {...commonProps} size={size}>
              {loading ? <CircularProgress size={20} /> : <DownloadIcon />}
            </IconButton>
          </span>
        </Tooltip>
      );
    }

    if (variant === 'button') {
      return (
        <Button
          {...commonProps}
          startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
          size={size}
        >
          Export
        </Button>
      );
    }

    if (variant === 'menu') {
      return (
        <Tooltip title="Export options">
          <span>
            <IconButton {...commonProps} size={size}>
              {loading ? <CircularProgress size={20} /> : <MoreVertIcon />}
            </IconButton>
          </span>
        </Tooltip>
      );
    }

    return null;
  };

  const renderMenu = () => (
    <Menu
      anchorEl={anchorEl}
      open={Boolean(anchorEl)}
      onClose={handleClose}
      transformOrigin={{ horizontal: 'right', vertical: 'top' }}
      anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
    >
      <MenuItem onClick={handleOpenDialog}>
        <ListItemIcon>
          <DescriptionIcon />
        </ListItemIcon>
        <ListItemText 
          primary="Export with Options"
          secondary="Choose format and template"
        />
      </MenuItem>
      
      <Divider />
      
      <MenuItem disabled>
        <ListItemText 
          primary={
            <Typography variant="caption" color="text.secondary">
              Quick Export
            </Typography>
          }
        />
      </MenuItem>
      
      {availableFormats.slice(0, 4).map((format) => (
        <MenuItem 
          key={format.format}
          onClick={() => handleQuickExport(format.format)}
        >
          <ListItemIcon>
            <span style={{ fontSize: '1.2rem' }}>
              {transcriptExportService.getFormatIcon(format.format)}
            </span>
          </ListItemIcon>
          <ListItemText 
            primary={format.name}
            secondary={format.description}
          />
        </MenuItem>
      ))}
      
      {availableFormats.length > 4 && (
        <MenuItem onClick={handleOpenDialog}>
          <ListItemIcon>
            <FileDownloadIcon />
          </ListItemIcon>
          <ListItemText 
            primary="More formats..."
            secondary={`${availableFormats.length - 4} more available`}
          />
        </MenuItem>
      )}
    </Menu>
  );

  return (
    <>
      {renderButton()}
      {renderMenu()}
      
      <ExportDialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        jobId={job?.id}
        jobFilename={job?.original_filename}
        onExportComplete={handleDialogExportComplete}
      />
    </>
  );
};

export default ExportButton;