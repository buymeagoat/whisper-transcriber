import React, { useState, useEffect } from 'react';
import { X, Download, RefreshCw, Eye, EyeOff } from 'lucide-react';

interface JobDetailsModalProps {
  jobId: string;
  isOpen: boolean;
  onClose: () => void;
}

interface JobDetails {
  job_id: string;
  original_filename: string;
  saved_filename: string;
  model: string;
  status: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  finished_at?: string;
  transcript_path?: string;
  log_path?: string;
  transcript_content?: string;
  log_content?: string;
  queue_details?: {
    queue_status?: string;
    queue_progress?: number;
    queue_worker?: string;
  };
}

const JobDetailsModal: React.FC<JobDetailsModalProps> = ({ jobId, isOpen, onClose }) => {
  const [jobDetails, setJobDetails] = useState<JobDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('details');
  const [showFullLogs, setShowFullLogs] = useState(false);

  const tabs = [
    { id: 'details', name: 'Job Details', icon: '📄' },
    { id: 'transcript', name: 'Transcript', icon: '📝' },
    { id: 'logs', name: 'Logs', icon: '📊' }
  ];

  const fetchJobDetails = async () => {
    if (!jobId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`/api/admin/jobs/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch job details');
      }

      const data: JobDetails = await response.json();
      setJobDetails(data);
    } catch (error) {
      console.error('Error fetching job details:', error);
      setError('Failed to load job details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && jobId) {
      fetchJobDetails();
    }
  }, [isOpen, jobId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (start?: string, end?: string) => {
    if (!start || !end) return 'N/A';
    const duration = (new Date(end).getTime() - new Date(start).getTime()) / 1000;
    const minutes = Math.floor(duration / 60);
    const seconds = Math.floor(duration % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900',
      queued: 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900',
      running: 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900',
      processing: 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900',
      completed: 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900',
      failed: 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900',
      cancelled: 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900'
    };
    return colors[status] || colors.cancelled;
  };

  const downloadTranscript = () => {
    if (!jobDetails?.transcript_content) return;
    
    const blob = new Blob([jobDetails.transcript_content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${jobDetails.original_filename}_transcript.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadLogs = () => {
    if (!jobDetails?.log_content) return;
    
    const blob = new Blob([jobDetails.log_content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${jobDetails.original_filename}_logs.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderTabContent = () => {
    if (!jobDetails) return null;

    switch (activeTab) {
      case 'details':
        return (
          <div className="space-y-6">
            {/* Basic Information */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Basic Information
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Job ID
                  </label>
                  <p className="mt-1 text-sm font-mono text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-2 rounded">
                    {jobDetails.job_id}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Original Filename
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-2 rounded">
                    {jobDetails.original_filename}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Model
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-2 rounded">
                    {jobDetails.model}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Status
                  </label>
                  <p className={`mt-1 text-sm px-2 py-1 rounded inline-block ${getStatusColor(jobDetails.status)}`}>
                    {jobDetails.queue_details?.queue_status || jobDetails.status}
                  </p>
                </div>
              </div>
            </div>

            {/* Timestamps */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Timeline
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Created
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-2 rounded">
                    {formatDate(jobDetails.created_at)}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Updated
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-2 rounded">
                    {formatDate(jobDetails.updated_at)}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Started
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-2 rounded">
                    {jobDetails.started_at ? formatDate(jobDetails.started_at) : 'Not started'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Finished
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-2 rounded">
                    {jobDetails.finished_at ? formatDate(jobDetails.finished_at) : 'Not finished'}
                  </p>
                </div>
              </div>
            </div>

            {/* Duration and Progress */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Processing Information
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Duration
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-2 rounded">
                    {formatDuration(jobDetails.started_at, jobDetails.finished_at)}
                  </p>
                </div>
                {jobDetails.queue_details?.queue_progress !== undefined && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Progress
                    </label>
                    <div className="mt-1 bg-gray-50 dark:bg-gray-700 p-2 rounded">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${jobDetails.queue_details.queue_progress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        {jobDetails.queue_details.queue_progress}%
                      </p>
                    </div>
                  </div>
                )}
                {jobDetails.queue_details?.queue_worker && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Worker
                    </label>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-2 rounded">
                      {jobDetails.queue_details.queue_worker}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* File Information */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Files
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Transcript
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {jobDetails.transcript_path || 'Not available'}
                    </p>
                  </div>
                  {jobDetails.transcript_content && (
                    <button
                      onClick={downloadTranscript}
                      className="flex items-center px-3 py-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </button>
                  )}
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Logs
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {jobDetails.log_path || 'Not available'}
                    </p>
                  </div>
                  {jobDetails.log_content && (
                    <button
                      onClick={downloadLogs}
                      className="flex items-center px-3 py-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      case 'transcript':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                Transcript Content
              </h4>
              {jobDetails.transcript_content && (
                <button
                  onClick={downloadTranscript}
                  className="flex items-center px-3 py-2 text-sm text-blue-600 bg-blue-50 rounded hover:bg-blue-100 dark:bg-blue-900 dark:text-blue-400"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </button>
              )}
            </div>
            {jobDetails.transcript_content ? (
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <pre className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap font-mono">
                  {jobDetails.transcript_content}
                </pre>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No transcript available
              </div>
            )}
          </div>
        );

      case 'logs':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                Processing Logs
              </h4>
              <div className="flex gap-2">
                {jobDetails.log_content && (
                  <>
                    <button
                      onClick={() => setShowFullLogs(!showFullLogs)}
                      className="flex items-center px-3 py-2 text-sm text-gray-600 bg-gray-100 rounded hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400"
                    >
                      {showFullLogs ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
                      {showFullLogs ? 'Show Less' : 'Show All'}
                    </button>
                    <button
                      onClick={downloadLogs}
                      className="flex items-center px-3 py-2 text-sm text-blue-600 bg-blue-50 rounded hover:bg-blue-100 dark:bg-blue-900 dark:text-blue-400"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </button>
                  </>
                )}
              </div>
            </div>
            {jobDetails.log_content ? (
              <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                <pre className="text-sm text-green-400 whitespace-pre-wrap font-mono">
                  {showFullLogs ? jobDetails.log_content : jobDetails.log_content.slice(-2000)}
                  {!showFullLogs && jobDetails.log_content.length > 2000 && (
                    <div className="text-yellow-400 mt-2">
                      ... (showing last 2KB, click "Show All" to see complete logs)
                    </div>
                  )}
                </pre>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No logs available
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
        
        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-white dark:bg-gray-800 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                Job Details
              </h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={fetchJobDetails}
                  disabled={loading}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-50"
                >
                  <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
                </button>
                <button
                  onClick={onClose}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
            
            {/* Tabs */}
            <div className="mt-4">
              <nav className="flex space-x-8">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    <span className="mr-2">{tab.icon}</span>
                    {tab.name}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Content */}
          <div className="bg-white dark:bg-gray-800 px-6 py-6 max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex justify-center items-center py-8">
                <RefreshCw className="animate-spin h-8 w-8 text-gray-400" />
                <span className="ml-2 text-gray-500 dark:text-gray-400">Loading job details...</span>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <p className="text-red-600 dark:text-red-400">{error}</p>
                <button
                  onClick={fetchJobDetails}
                  className="mt-4 px-4 py-2 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
                >
                  Try Again
                </button>
              </div>
            ) : (
              renderTabContent()
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 dark:bg-gray-700 px-6 py-3">
            <div className="flex justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-gray-600 dark:text-white dark:border-gray-500 dark:hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobDetailsModal;
