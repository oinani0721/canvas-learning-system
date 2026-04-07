import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { ErrorBoundary } from './components/ErrorBoundary';
import { createLogger } from './services/logger';

const logger = createLogger('App');

// FR-KG-04 Phase 2 Task 2.9: Verify the internal API key is provisioned at
// startup so /api/v1/sync/batch and other auth-protected endpoints can be
// reached. The key itself is read by ApiClient via import.meta.env on its
// own constructor — this block exists purely to surface a warning when the
// key is missing (e.g. forgot to copy .env.example to .env on first install).
const INTERNAL_KEY = (import.meta.env.VITE_INTERNAL_API_KEY as string | undefined) ?? '';
if (!INTERNAL_KEY) {
  logger.warn(
    'VITE_INTERNAL_API_KEY is not set; backend sync/batch will reject requests with 403 in production. ' +
      'Set VITE_INTERNAL_API_KEY in your .env file (matches backend INTERNAL_API_KEY).',
  );
}

window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
  logger.error('unhandledrejection', {
    reason: event.reason instanceof Error ? event.reason.message : String(event.reason),
    stack: event.reason instanceof Error ? event.reason.stack : undefined,
  });
});

window.addEventListener('error', (event: ErrorEvent) => {
  logger.error('uncaught error', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
  });
});

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
