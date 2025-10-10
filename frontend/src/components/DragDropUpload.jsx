import React, { useState, useRef } from 'react';

const DragDropUpload = ({ onFileDrop, accept = "audio/*", maxFileSize = 100 * 1024 * 1024, multiple = true }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errors, setErrors] = useState([]);
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    const errors = [];
    
    // Check file size
    if (file.size > maxFileSize) {
      errors.push(`File "${file.name}" is too large. Maximum size is ${(maxFileSize / (1024 * 1024)).toFixed(1)}MB`);
    }
    
    // Check file type for audio files
    if (accept.includes('audio') && !file.type.startsWith('audio/')) {
      errors.push(`File "${file.name}" is not a valid audio file`);
    }
    
    return errors;
  };

  const processFiles = (files) => {
    const fileArray = Array.from(files);
    const allErrors = [];
    const validFiles = [];

    fileArray.forEach(file => {
      const fileErrors = validateFile(file);
      if (fileErrors.length > 0) {
        allErrors.push(...fileErrors);
      } else {
        validFiles.push(file);
      }
    });

    setErrors(allErrors);

    if (validFiles.length > 0) {
      onFileDrop(validFiles);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processFiles(files);
    }
  };

  const handleFileInputChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      processFiles(files);
    }
    // Reset input so the same file can be selected again
    e.target.value = '';
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const dropZoneStyle = {
    border: `2px dashed ${isDragOver ? '#3b82f6' : '#d1d5db'}`,
    borderRadius: '8px',
    padding: '3rem 2rem',
    textAlign: 'center',
    backgroundColor: isDragOver ? '#eff6ff' : '#f9fafb',
    transition: 'all 0.3s ease',
    cursor: 'pointer',
    position: 'relative',
    minHeight: '200px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center'
  };

  const iconStyle = {
    width: '48px',
    height: '48px',
    color: isDragOver ? '#3b82f6' : '#9ca3af',
    marginBottom: '1rem'
  };

  return (
    <div>
      <div
        style={dropZoneStyle}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        {/* Upload Icon */}
        <svg style={iconStyle} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>

        <div style={{ 
          fontSize: '1.25rem', 
          fontWeight: '600', 
          color: isDragOver ? '#3b82f6' : '#374151',
          marginBottom: '0.5rem'
        }}>
          {isDragOver ? 'Drop files here' : 'Drop audio files here or click to browse'}
        </div>

        <div style={{ 
          fontSize: '0.9rem', 
          color: '#6b7280',
          marginBottom: '0.5rem'
        }}>
          Supports MP3, WAV, M4A, FLAC and other audio formats
        </div>

        <div style={{ 
          fontSize: '0.8rem', 
          color: '#9ca3af'
        }}>
          Maximum file size: {(maxFileSize / (1024 * 1024)).toFixed(1)}MB
        </div>

        {isDragOver && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.5rem',
            fontWeight: '600',
            color: '#3b82f6'
          }}>
            Release to upload
          </div>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
      />

      {/* Error messages */}
      {errors.length > 0 && (
        <div style={{ 
          marginTop: '1rem', 
          padding: '1rem',
          backgroundColor: '#fee2e2',
          border: '1px solid #fecaca',
          borderRadius: '6px'
        }}>
          <div style={{ 
            fontSize: '0.9rem', 
            fontWeight: '600', 
            color: '#dc2626',
            marginBottom: '0.5rem'
          }}>
            Upload Errors:
          </div>
          {errors.map((error, index) => (
            <div key={index} style={{ 
              fontSize: '0.8rem', 
              color: '#b91c1c',
              marginBottom: '0.25rem'
            }}>
              • {error}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DragDropUpload;
