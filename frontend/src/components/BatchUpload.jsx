/**
 * T020: Enhanced Batch Upload Page Component
 * Full-page component for batch upload management with T020 functionality
 */

import React from 'react';
import { BatchList } from './batch';

const BatchUpload = () => {
  const handleBatchComplete = (batchData) => {
    console.log('Batch completed:', batchData);
  };

  const handleBatchError = (error) => {
    console.error('Batch error:', error);
  };

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Batch Upload Management
        </h1>
        <p className="text-gray-600">
          Upload and manage multiple audio files for batch transcription processing
        </p>
      </div>

      {/* T020 Batch Upload Interface */}
      <BatchList
        onBatchComplete={handleBatchComplete}
        onBatchError={handleBatchError}
        maxDisplayBatches={0} // Show all batches on dedicated page
      />
    </div>
  );
};

export default BatchUpload;