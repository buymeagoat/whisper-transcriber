import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { ROUTES } from '../routes';

const initialState = { jobs: [], status: 'idle', error: null };

const authHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const fetchJobs = createAsyncThunk('jobs/fetchJobs', async (search = '', { rejectWithValue }) => {
  const url = search ? `${ROUTES.API}/jobs?search=${encodeURIComponent(search)}` : `${ROUTES.API}/jobs`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) {
    return rejectWithValue(await res.text());
  }
  return res.json();
});

export const deleteJob = createAsyncThunk('jobs/deleteJob', async (jobId, { rejectWithValue }) => {
  const res = await fetch(`${ROUTES.API}/jobs/${jobId}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) {
    return rejectWithValue(await res.text());
  }
  return jobId;
});

export const restartJob = createAsyncThunk('jobs/restartJob', async (jobId, { rejectWithValue }) => {
  const res = await fetch(`${ROUTES.API}/jobs/${jobId}/restart`, { method: 'POST', headers: authHeaders() });
  if (!res.ok) {
    return rejectWithValue(await res.text());
  }
  return jobId;
});

const jobsSlice = createSlice({
  name: 'jobs',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchJobs.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchJobs.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.jobs = action.payload;
      })
      .addCase(fetchJobs.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || action.error.message;
      })
      .addCase(deleteJob.fulfilled, (state, action) => {
        state.jobs = state.jobs.filter((j) => j.id !== action.payload);
      })
      .addCase(restartJob.fulfilled, (state) => {
        state.status = 'idle';
      });
  },
});

export const selectJobs = (state) => state.jobs.jobs;

export default jobsSlice.reducer;
