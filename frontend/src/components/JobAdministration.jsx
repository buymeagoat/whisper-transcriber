import React, { useState, useEffect } from 'react';
import { jobsService } from '../services/jobsService';

/**
 * JobAdministration - Comprehensive job administration interface for administrators
 * Provides job listing, details, status management, and administrative actions
 */
const JobAdministration = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [pagination, setPagination] = useState({ skip: 0, limit: 50 });
  const [totalJobs, setTotalJobs] = useState(0);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchJobs();
    // Refresh every 30 seconds to show real-time updates
    const interval = setInterval(fetchJobs, 30000);
    return () => clearInterval(interval);
  }, [pagination]);

  const fetchJobs = async () => {
    try {
      setError(null);
      setLoading(true);
      const response = await jobsService.listJobs(pagination.skip, pagination.limit);
      setJobs(response.jobs || []);
      setTotalJobs(response.total || 0);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = !searchTerm || 
      job.original_filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.job_id?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || job.status === filterStatus;
    
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400';
      case 'processing':
      case 'running':
        return 'text-blue-600 bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400';
      case 'pending':
      case 'queued':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'failed':
      case 'error':
        return 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400';
      case 'cancelled':
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20 dark:text-gray-400';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed': return '✅';
      case 'processing':
      case 'running': return '🔄';
      case 'pending':
      case 'queued': return '⏳';
      case 'failed':
      case 'error': return '❌';
      case 'cancelled': return '🚫';
      default: return '❓';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  };

  const handleJobAction = async (action, jobId) => {
    try {
      switch (action) {
        case 'cancel':
          // Placeholder for cancel action
          alert(`Job cancellation would be performed here for job ${jobId}`);
          break;
        case 'retry':
          // Placeholder for retry action
          alert(`Job retry would be performed here for job ${jobId}`);
          break;
        case 'delete':
          if (window.confirm('Are you sure you want to delete this job?')) {
            await jobsService.deleteJob(jobId);
            await fetchJobs(); // Refresh the list
          }
          break;
        default:
          console.log(`Action ${action} for job ${jobId}`);
      }
    } catch (err) {
      console.error(`Failed to perform ${action} on job ${jobId}:`, err);
      alert(`Failed to ${action} job: ${err.message}`);
    }
  };

  const handlePageChange = (newSkip) => {
    setPagination(prev => ({ ...prev, skip: newSkip }));
  };

  const JobCard = ({ job }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-lg">{getStatusIcon(job.status)}</span>
            <h3 className="font-medium text-gray-900 dark:text-white truncate">
              {job.original_filename || 'Unknown File'}
            </h3>
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
              {job.status}
            </span>
          </div>
          <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
            <p>🔑 Job ID: <span className="font-mono text-xs">{job.job_id}</span></p>
            <p>📅 Created: {formatDate(job.created_at)}</p>
            <p>⏱️ Duration: {job.processing_time ? `${job.processing_time}s` : 'N/A'}</p>
            {job.model && <p>🤖 Model: {job.model}</p>}
          </div>
        </div>
        <div className="flex flex-col space-y-1 ml-4">
          <button
            onClick={() => setSelectedJob(job)}
            className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            View Details
          </button>
          {job.status === 'processing' && (
            <button
              onClick={() => handleJobAction('cancel', job.job_id)}
              className="text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Cancel
            </button>
          )}
          {job.status === 'failed' && (
            <button
              onClick={() => handleJobAction('retry', job.job_id)}
              className="text-xs px-2 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
            >
              Retry
            </button>
          )}
          <button
            onClick={() => handleJobAction('delete', job.job_id)}
            className="text-xs px-2 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );

  const JobDetailsModal = ({ job, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Job Details: {job.original_filename}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ✕
            </button>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white mb-3">Job Information</h3>
              <div className="space-y-2 text-sm">
                <p><strong>Job ID:</strong> <span className="font-mono">{job.job_id}</span></p>
                <p><strong>Filename:</strong> {job.original_filename}</p>
                <p><strong>Status:</strong> 
                  <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                    {getStatusIcon(job.status)} {job.status}
                  </span>
                </p>
                <p><strong>Model:</strong> {job.model || 'Default'}</p>
                <p><strong>Language:</strong> {job.language || 'Auto-detect'}</p>
                <p><strong>Created:</strong> {formatDate(job.created_at)}</p>
                <p><strong>Processing Time:</strong> {job.processing_time ? `${job.processing_time}s` : 'N/A'}</p>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white mb-3">Technical Details</h3>
              <div className="space-y-2 text-sm">
                <p><strong>File Size:</strong> {job.file_size ? `${(job.file_size / 1024 / 1024).toFixed(2)} MB` : 'N/A'}</p>
                <p><strong>File Type:</strong> {job.file_type || 'Unknown'}</p>
                <p><strong>Progress:</strong> {job.progress || 0}%</p>
                <p><strong>Error Message:</strong> {job.error_message || 'None'}</p>
                <p><strong>Worker ID:</strong> {job.worker_id || 'N/A'}</p>
                <p><strong>Queue Priority:</strong> {job.priority || 'Normal'}</p>
              </div>
            </div>
          </div>
          
          {job.result && (
            <div className="mt-6">
              <h3 className="font-medium text-gray-900 dark:text-white mb-3">Transcription Result</h3>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 max-h-40 overflow-y-auto">
                <pre className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                  {job.result}
                </pre>
              </div>
            </div>
          )}
          
          <div className="flex space-x-2 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => handleJobAction('download', job.job_id)}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
            >
              Download Result
            </button>
            <button
              onClick={() => handleJobAction('logs', job.job_id)}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
            >
              View Logs
            </button>
            {job.status === 'processing' && (
              <button
                onClick={() => handleJobAction('cancel', job.job_id)}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Cancel Job
              </button>
            )}
            {job.status === 'failed' && (
              <button
                onClick={() => handleJobAction('retry', job.job_id)}
                className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
              >
                Retry Job
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const Pagination = () => {
    const totalPages = Math.ceil(totalJobs / pagination.limit);
    const currentPage = Math.floor(pagination.skip / pagination.limit) + 1;
    
    return (
      <div className="flex items-center justify-between bg-white dark:bg-gray-800 px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div className="text-sm text-gray-700 dark:text-gray-300">
          Showing {pagination.skip + 1} to {Math.min(pagination.skip + pagination.limit, totalJobs)} of {totalJobs} jobs
        </div>
        <div className="flex space-x-1">
          <button
            onClick={() => handlePageChange(Math.max(0, pagination.skip - pagination.limit))}
            disabled={pagination.skip === 0}
            className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="px-3 py-1 text-sm bg-indigo-600 text-white rounded">
            {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => handlePageChange(pagination.skip + pagination.limit)}
            disabled={pagination.skip + pagination.limit >= totalJobs}
            className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-500 dark:text-gray-400">Loading jobs...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Job Administration
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Monitor and manage all transcription jobs
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {lastUpdate && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchJobs}
            disabled={loading}
            className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '⟳' : '🔄'} Refresh
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4 mb-6">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Search and Filter */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search jobs by filename or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>
          <div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
      </div>

      {/* Jobs Summary */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Jobs</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{totalJobs}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed</h3>
          <p className="text-2xl font-bold text-green-600">
            {jobs.filter(j => j.status === 'completed').length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Processing</h3>
          <p className="text-2xl font-bold text-blue-600">
            {jobs.filter(j => j.status === 'processing').length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Failed</h3>
          <p className="text-2xl font-bold text-red-600">
            {jobs.filter(j => j.status === 'failed').length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Filtered</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{filteredJobs.length}</p>
        </div>
      </div>

      {/* Jobs List */}
      {filteredJobs.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
          <div className="text-gray-400 dark:text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {totalJobs === 0 ? 'No Jobs Found' : 'No Matching Jobs'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              {totalJobs === 0 
                ? 'No transcription jobs have been created yet. Jobs will appear here once users upload files.'
                : 'Try adjusting your search criteria or filters.'
              }
            </p>
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-6">
            {filteredJobs.map((job) => (
              <JobCard key={job.job_id} job={job} />
            ))}
          </div>
          
          {/* Pagination */}
          {totalJobs > pagination.limit && <Pagination />}
        </>
      )}

      {/* Job Details Modal */}
      {selectedJob && (
        <JobDetailsModal
          job={selectedJob}
          onClose={() => setSelectedJob(null)}
        />
      )}
    </div>
  );
};

export default JobAdministration;
