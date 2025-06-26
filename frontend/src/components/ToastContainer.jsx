import { useSelector, useDispatch } from 'react-redux';
import { selectToasts, removeToast } from '../store';

export default function ToastContainer() {
  const toasts = useSelector(selectToasts);
  const dispatch = useDispatch();

  const colors = {
    success: '#16a34a',
    error: '#dc2626',
    info: '#2563eb',
  };

  return (
    <div style={{ position: 'fixed', top: '1rem', right: '1rem', zIndex: 1000 }}>
      {toasts.map((t) => (
        <div
          key={t.id}
          style={{
            backgroundColor: colors[t.type] || '#27272a',
            color: 'white',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            marginBottom: '0.5rem',
            minWidth: '200px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{t.message}</span>
            <button
              onClick={() => dispatch(removeToast(t.id))}
              style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer' }}
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
