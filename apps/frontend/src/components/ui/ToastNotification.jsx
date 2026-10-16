import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

const ToastContext = createContext({
  showToast: () => {},
  success: () => {},
  error: () => {},
  info: () => {},
});

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((message, type = 'success', duration = 3000) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [removeToast]);

  const success = useCallback((message, duration) => addToast(message, 'success', duration), [addToast]);
  const error = useCallback((message, duration) => addToast(message, 'error', duration), [addToast]);
  const info = useCallback((message, duration) => addToast(message, 'info', duration), [addToast]);

  return (
    <ToastContext.Provider value={{ showToast: addToast, success, error, info }}>
      {children}
      {/* Floating Pop-up Notification Container */}
      <aside aria-label="Notificaciones" className="fixed top-4 right-4 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-3">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="alert"
            className="pointer-events-auto flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-white/90 backdrop-blur-md border border-border/80 shadow-lg text-xs sm:text-sm font-medium text-brand-ink transition-all duration-200 animate-in slide-in-from-top-2 fade-in select-none"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              {toast.type === 'success' && (
                <CheckCircle2 size={18} strokeWidth={2} className="text-emerald-600 shrink-0" />
              )}
              {toast.type === 'error' && (
                <AlertCircle size={18} strokeWidth={2} className="text-rose-600 shrink-0" />
              )}
              {toast.type === 'info' && (
                <Info size={18} strokeWidth={2} className="text-brand-ink shrink-0" />
              )}
              <span className="leading-snug truncate">{toast.message}</span>
            </div>
            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              aria-label="Cerrar notificación"
              className="size-5 rounded-md flex items-center justify-center text-text-muted hover:text-brand-ink hover:bg-surface-muted transition-colors shrink-0 cursor-pointer"
            >
              <X size={13} />
            </button>
          </div>
        ))}
      </aside>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    return {
      showToast: () => {},
      success: () => {},
      error: () => {},
      info: () => {},
    };
  }
  return context;
}
