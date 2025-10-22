/**
 * T029 Enhanced User Experience: Advanced File Upload Component
 * React component with audio preview, waveform visualization, and comprehensive validation
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  File, 
  CheckCircle, 
  AlertCircle, 
  XCircle, 
  Play, 
  Pause, 
  Volume2,
  Info,
  Trash2,
  Eye,
  Settings
} from 'lucide-react';
import advancedFileUploadService from '../services/advancedFileUploadService';

const AdvancedFileUpload = ({ onFilesSelected, onFileRemoved, maxFiles = 10 }) => {
  const [files, setFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [currentPreview, setCurrentPreview] = useState(null);
  const [audioPlaying, setAudioPlaying] = useState(null);
  const [processingFiles, setProcessingFiles] = useState(new Set());
  const [showAdvanced, setShowAdvanced] = useState(false);

  const fileInputRef = useRef(null);
  const audioRef = useRef(null);
  const waveformCanvasRef = useRef(null);

  useEffect(() => {
    return () => {
      // Cleanup audio previews
      files.forEach(file => {
        if (file.audioPreview?.previewUrl) {
          URL.revokeObjectURL(file.audioPreview.previewUrl);
        }
      });
      advancedFileUploadService.cleanup();
    };
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      processFiles(droppedFiles);
    }
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 0) {
      processFiles(selectedFiles);
    }
  };

  const processFiles = async (newFiles) => {
    if (files.length + newFiles.length > maxFiles) {
      alert(`Maximum ${maxFiles} files allowed`);
      return;
    }

    const processedFiles = [];

    for (const file of newFiles) {
      const fileId = `${file.name}_${file.size}_${Date.now()}`;
      setProcessingFiles(prev => new Set([...prev, fileId]));

      try {
        // Validate file
        const validation = await advancedFileUploadService.validateFile(file);
        
        // Generate audio preview if it's an audio/video file
        let audioPreview = null;
        if (validation.metadata.format?.category === 'audio' || 
            validation.metadata.format?.category === 'video') {
          audioPreview = await advancedFileUploadService.generateAudioPreview(file);
        }

        // Assess quality
        const quality = advancedFileUploadService.assessFileQuality(
          validation.metadata, 
          audioPreview
        );

        const processedFile = {
          id: fileId,
          file,
          validation,
          audioPreview,
          quality,
          uploadProgress: 0,
          status: validation.isValid ? 'ready' : 'invalid'
        };

        processedFiles.push(processedFile);
      } catch (error) {
        console.error('Error processing file:', error);
        processedFiles.push({
          id: fileId,
          file,
          validation: {
            isValid: false,
            errors: [`Failed to process file: ${error.message}`],
            warnings: [],
            metadata: {}
          },
          status: 'error'
        });
      }

      setProcessingFiles(prev => {
        const newSet = new Set(prev);
        newSet.delete(fileId);
        return newSet;
      });
    }

    const updatedFiles = [...files, ...processedFiles];
    setFiles(updatedFiles);
    
    if (onFilesSelected) {
      onFilesSelected(updatedFiles);
    }
  };

  const removeFile = (fileId) => {
    const fileToRemove = files.find(f => f.id === fileId);
    if (fileToRemove?.audioPreview?.previewUrl) {
      URL.revokeObjectURL(fileToRemove.audioPreview.previewUrl);
    }

    const updatedFiles = files.filter(f => f.id !== fileId);
    setFiles(updatedFiles);
    
    if (onFileRemoved) {
      onFileRemoved(fileToRemove);
    }

    // Close preview if this file was being previewed
    if (currentPreview?.id === fileId) {
      setCurrentPreview(null);
    }
  };

  const openPreview = (file) => {
    setCurrentPreview(file);
  };

  const closePreview = () => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setAudioPlaying(null);
    setCurrentPreview(null);
  };

  const toggleAudioPlay = () => {
    if (!audioRef.current || !currentPreview?.audioPreview) return;

    if (audioPlaying === currentPreview.id) {
      audioRef.current.pause();
      setAudioPlaying(null);
    } else {
      audioRef.current.play();
      setAudioPlaying(currentPreview.id);
    }
  };

  const drawWaveform = (canvas, waveformData, progress = 0) => {
    if (!canvas || !waveformData) return;

    const ctx = canvas.getContext('2d');
    const { width, height } = canvas;
    
    ctx.clearRect(0, 0, width, height);
    
    const barWidth = width / waveformData.length;
    const maxHeight = height * 0.8;
    
    waveformData.forEach((data, index) => {
      const barHeight = data.peak * maxHeight;
      const x = index * barWidth;
      const y = (height - barHeight) / 2;
      
      // Color based on progress
      const progressPoint = progress * waveformData.length;
      if (index < progressPoint) {
        ctx.fillStyle = '#3B82F6'; // Blue for played portion
      } else {
        ctx.fillStyle = '#E5E7EB'; // Gray for unplayed portion
      }
      
      ctx.fillRect(x, y, barWidth - 1, barHeight);
    });
  };

  const getStatusColor = (status, health) => {
    if (status === 'invalid' || health === 'corrupted') return 'text-red-600 bg-red-50';
    if (status === 'error' || health === 'suspicious') return 'text-orange-600 bg-orange-50';
    if (status === 'ready' && health === 'healthy') return 'text-green-600 bg-green-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getStatusIcon = (status, health) => {
    if (status === 'invalid' || health === 'corrupted') return <XCircle className="w-5 h-5" />;
    if (status === 'error' || health === 'suspicious') return <AlertCircle className="w-5 h-5" />;
    if (status === 'ready' && health === 'healthy') return <CheckCircle className="w-5 h-5" />;
    return <File className="w-5 h-5" />;
  };

  const getQualityColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  useEffect(() => {
    if (currentPreview?.audioPreview?.waveform && waveformCanvasRef.current) {
      drawWaveform(waveformCanvasRef.current, currentPreview.audioPreview.waveform);
    }
  }, [currentPreview]);

  useEffect(() => {
    if (audioRef.current && currentPreview?.audioPreview?.waveform) {
      const audio = audioRef.current;
      const updateWaveform = () => {
        const progress = audio.currentTime / audio.duration || 0;
        drawWaveform(waveformCanvasRef.current, currentPreview.audioPreview.waveform, progress);
      };

      audio.addEventListener('timeupdate', updateWaveform);
      audio.addEventListener('ended', () => setAudioPlaying(null));

      return () => {
        audio.removeEventListener('timeupdate', updateWaveform);
        audio.removeEventListener('ended', () => setAudioPlaying(null));
      };
    }
  }, [currentPreview, audioPlaying]);

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${
          dragActive 
            ? 'border-blue-400 bg-blue-50 scale-105' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="audio/*,video/*"
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        
        <div className="space-y-4">
          <Upload className={`mx-auto h-16 w-16 transition-colors ${
            dragActive ? 'text-blue-500' : 'text-gray-400'
          }`} />
          
          <div>
            <p className="text-lg font-medium text-gray-900">
              {dragActive ? 'Drop files here' : 'Upload audio or video files'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Drag and drop files here, or click to browse
            </p>
          </div>
          
          <div className="text-xs text-gray-400">
            <p>Supported formats: MP3, WAV, FLAC, M4A, OGG, MP4, MOV, AVI</p>
            <p>Maximum file size: 1GB • Maximum {maxFiles} files</p>
          </div>
        </div>
      </div>

      {/* Advanced Options Toggle */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          Selected Files ({files.length})
        </h3>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center text-sm text-blue-600 hover:text-blue-800"
        >
          <Settings className="w-4 h-4 mr-1" />
          {showAdvanced ? 'Hide' : 'Show'} Details
        </button>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-3">
          {files.map((fileData) => (
            <div
              key={fileData.id}
              className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  {/* File Header */}
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${getStatusColor(fileData.status, fileData.validation.health)}`}>
                      {processingFiles.has(fileData.id) ? (
                        <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                      ) : (
                        getStatusIcon(fileData.status, fileData.validation.health)
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {fileData.file.name}
                      </h4>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>{advancedFileUploadService.formatFileSize(fileData.file.size)}</span>
                        {fileData.validation.metadata.duration && (
                          <span>{advancedFileUploadService.formatDuration(fileData.validation.metadata.duration)}</span>
                        )}
                        {fileData.validation.metadata.format && (
                          <span className="uppercase">{fileData.validation.metadata.format.ext}</span>
                        )}
                        {fileData.quality && (
                          <span className={`font-medium ${getQualityColor(fileData.quality.score)}`}>
                            Quality: {fileData.quality.score}%
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Advanced Details */}
                  {showAdvanced && (
                    <div className="mt-3 space-y-2">
                      {/* Validation Errors */}
                      {fileData.validation.errors.length > 0 && (
                        <div className="p-2 bg-red-50 border border-red-200 rounded text-xs">
                          <p className="font-medium text-red-800 mb-1">Errors:</p>
                          <ul className="text-red-700 space-y-1">
                            {fileData.validation.errors.map((error, index) => (
                              <li key={index}>• {error}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Validation Warnings */}
                      {fileData.validation.warnings.length > 0 && (
                        <div className="p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                          <p className="font-medium text-yellow-800 mb-1">Warnings:</p>
                          <ul className="text-yellow-700 space-y-1">
                            {fileData.validation.warnings.map((warning, index) => (
                              <li key={index}>• {warning}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Quality Issues */}
                      {fileData.quality?.issues.length > 0 && (
                        <div className="p-2 bg-orange-50 border border-orange-200 rounded text-xs">
                          <p className="font-medium text-orange-800 mb-1">Quality Issues:</p>
                          <ul className="text-orange-700 space-y-1">
                            {fileData.quality.issues.map((issue, index) => (
                              <li key={index}>• {issue}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Quality Recommendations */}
                      {fileData.quality?.recommendations.length > 0 && (
                        <div className="p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                          <p className="font-medium text-blue-800 mb-1">Recommendations:</p>
                          <ul className="text-blue-700 space-y-1">
                            {fileData.quality.recommendations.map((rec, index) => (
                              <li key={index}>• {rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Audio Properties */}
                      {fileData.audioPreview && (
                        <div className="p-2 bg-gray-50 border border-gray-200 rounded text-xs">
                          <p className="font-medium text-gray-800 mb-1">Audio Properties:</p>
                          <div className="grid grid-cols-2 gap-2 text-gray-600">
                            <span>Sample Rate: {fileData.audioPreview.sampleRate} Hz</span>
                            <span>Channels: {fileData.audioPreview.channels}</span>
                            <span>Duration: {advancedFileUploadService.formatDuration(fileData.audioPreview.duration)}</span>
                            <span>Health: {fileData.validation.health}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 ml-4">
                  {fileData.audioPreview && (
                    <button
                      onClick={() => openPreview(fileData)}
                      className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Preview Audio"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  )}
                  
                  <button
                    onClick={() => removeFile(fileData.id)}
                    className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors"
                    title="Remove File"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Audio Preview Modal */}
      {currentPreview && currentPreview.audioPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-auto">
            <div className="p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Audio Preview
                </h3>
                <button
                  onClick={closePreview}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              {/* File Info */}
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">{currentPreview.file.name}</h4>
                <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                  <span>Size: {advancedFileUploadService.formatFileSize(currentPreview.file.size)}</span>
                  <span>Duration: {advancedFileUploadService.formatDuration(currentPreview.audioPreview.duration)}</span>
                  <span>Sample Rate: {currentPreview.audioPreview.sampleRate} Hz</span>
                  <span>Channels: {currentPreview.audioPreview.channels}</span>
                </div>
              </div>

              {/* Waveform */}
              <div className="mb-4">
                <canvas
                  ref={waveformCanvasRef}
                  width={500}
                  height={100}
                  className="w-full h-24 border border-gray-200 rounded bg-gray-50"
                />
              </div>

              {/* Audio Controls */}
              <div className="flex items-center justify-center space-x-4 mb-4">
                <button
                  onClick={toggleAudioPlay}
                  className="flex items-center justify-center w-12 h-12 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
                >
                  {audioPlaying === currentPreview.id ? (
                    <Pause className="w-6 h-6" />
                  ) : (
                    <Play className="w-6 h-6 ml-1" />
                  )}
                </button>
                
                <Volume2 className="w-5 h-5 text-gray-400" />
              </div>

              {/* Quality Assessment */}
              {currentPreview.quality && (
                <div className="mt-4 p-3 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">Quality Assessment</span>
                    <span className={`font-bold ${getQualityColor(currentPreview.quality.score)}`}>
                      {currentPreview.quality.score}%
                    </span>
                  </div>
                  
                  {currentPreview.quality.issues.length > 0 && (
                    <div className="text-sm text-red-600 mb-2">
                      <p className="font-medium">Issues:</p>
                      <ul className="list-disc list-inside">
                        {currentPreview.quality.issues.map((issue, index) => (
                          <li key={index}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {currentPreview.quality.recommendations.length > 0 && (
                    <div className="text-sm text-blue-600">
                      <p className="font-medium">Recommendations:</p>
                      <ul className="list-disc list-inside">
                        {currentPreview.quality.recommendations.map((rec, index) => (
                          <li key={index}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Hidden Audio Element */}
              <audio
                ref={audioRef}
                src={currentPreview.audioPreview.previewUrl}
                className="hidden"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedFileUpload;