import { configureStore } from '@reduxjs/toolkit';
import jobsReducer from './jobsSlice';
import notificationsReducer from './notificationsSlice';

export const store = configureStore({
  reducer: {
    jobs: jobsReducer,
    notifications: notificationsReducer,
  },
});

export * from './jobsSlice';
export * from './notificationsSlice';
