import React, { useState } from 'react'
import { Toaster } from 'react-hot-toast'
import { Mic, History, Home, ArrowLeft } from 'lucide-react'
import UploadComponent from './components/Upload'
import ProgressComponent from './components/Progress'
import HistoryComponent from './components/History'

const App = () => {
  const [currentView, setCurrentView] = useState('upload') // upload, progress, history
  const [currentJobId, setCurrentJobId] = useState(null)

  const handleUploadStart = (jobId) => {
    setCurrentJobId(jobId)
    setCurrentView('progress')
  }

  const handleSelectJob = (jobId) => {
    setCurrentJobId(jobId)
    setCurrentView('progress')
  }

  const handleBackToUpload = () => {
    setCurrentView('upload')
    setCurrentJobId(null)
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case 'progress':
        return (
          <ProgressComponent 
            jobId={currentJobId} 
            onComplete={() => {
              // Stay on progress view to show results
            }}
          />
        )
      case 'history':
        return <HistoryComponent onSelectJob={handleSelectJob} />
      default:
        return <UploadComponent onUploadStart={handleUploadStart} />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and Title */}
            <div className="flex items-center space-x-3">
              {currentView !== 'upload' && (
                <button
                  onClick={handleBackToUpload}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
              )}
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-primary-600 rounded-lg">
                  <Mic className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Whisper Transcriber</h1>
                  <p className="text-xs text-gray-500">Modern audio transcription</p>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex items-center space-x-1">
              <button
                onClick={() => setCurrentView('upload')}
                className={`
                  flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                  ${currentView === 'upload' 
                    ? 'bg-primary-100 text-primary-700' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }
                `}
              >
                <Home className="w-4 h-4" />
                <span className="hidden sm:inline">Upload</span>
              </button>
              
              <button
                onClick={() => setCurrentView('history')}
                className={`
                  flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                  ${currentView === 'history' 
                    ? 'bg-primary-100 text-primary-700' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }
                `}
              >
                <History className="w-4 h-4" />
                <span className="hidden sm:inline">History</span>
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="animate-fade-in">
          {renderCurrentView()}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-sm text-gray-500">
              Powered by OpenAI Whisper • Built for modern devices
            </p>
            <div className="mt-2 flex justify-center space-x-4 text-xs text-gray-400">
              <span>Supports: MP3, WAV, M4A, FLAC</span>
              <span>•</span>
              <span>Max file size: 100MB</span>
              <span>•</span>
              <span>Real-time progress</span>
            </div>
          </div>
        </div>
      </footer>

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </div>
  )
}

export default App
