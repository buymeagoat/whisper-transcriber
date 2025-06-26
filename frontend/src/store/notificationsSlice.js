import { createSlice } from '@reduxjs/toolkit';

let nextId = 1;

const notificationsSlice = createSlice({
  name: 'notifications',
  initialState: [],
  reducers: {
    addToast: {
      reducer(state, action) {
        state.push(action.payload);
      },
      prepare(message, type = 'info') {
        return { payload: { id: nextId++, message, type } };
      },
    },
    removeToast(state, action) {
      return state.filter((t) => t.id !== action.payload);
    },
  },
});

export const { addToast, removeToast } = notificationsSlice.actions;

export const selectToasts = (state) => state.notifications;

export default notificationsSlice.reducer;
