import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import axios from 'axios'
import { vi, describe, it, beforeEach, expect } from 'vitest'
import TranscribePage from './TranscribePage'

const dropzoneHandlers = {}

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

vi.mock('react-dropzone', () => ({
  useDropzone: (config) => {
    dropzoneHandlers.onDrop = config.onDrop
    return {
      getRootProps: () => ({}),
      getInputProps: () => ({}),
      isDragActive: false
    }
  }
}))

vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('TranscribePage upload flow', () => {
  beforeEach(() => {
    axios.post.mockReset()
    axios.get.mockReset()
  })

  it('uploads large files using chunked flow and reaches finalize step', async () => {
    axios.post
      .mockResolvedValueOnce({
        data: {
          session_id: 'session123',
          chunk_size: 200 * 1024 * 1024,
          total_chunks: 1
        }
      })
      .mockResolvedValueOnce({ data: {} })
      .mockResolvedValueOnce({ data: { job_id: 'job-1' } })

    axios.get.mockResolvedValue({
      data: {
        status: 'COMPLETED',
        transcript: 'Test transcript'
      }
    })

    render(<TranscribePage />)

    const file = new File(['test'], 'sample.wav', { type: 'audio/wav' })
    Object.defineProperty(file, 'size', {
      value: 101 * 1024 * 1024
    })

    if (!dropzoneHandlers.onDrop) {
      throw new Error('Drop handler was not registered')
    }

    await dropzoneHandlers.onDrop([file])

    expect(await screen.findByText('sample.wav')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /start transcription/i }))

    await waitFor(() => {
      expect(axios.post).toHaveBeenNthCalledWith(
        1,
        '/uploads/initialize',
        expect.objectContaining({
          filename: 'sample.wav',
          file_size: file.size
        })
      )
    })

    await waitFor(() => {
      expect(axios.post).toHaveBeenNthCalledWith(
        2,
        '/uploads/session123/chunks/0',
        expect.any(FormData),
        expect.objectContaining({ signal: expect.any(AbortSignal) })
      )
    })

    await waitFor(() => {
      expect(axios.post).toHaveBeenNthCalledWith(
        3,
        '/uploads/session123/finalize',
        null,
        expect.objectContaining({ signal: expect.any(AbortSignal) })
      )
    })

  })
})
