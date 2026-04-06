import React from 'react';
import { createLogger } from '../services/logger';

const logger = createLogger('ErrorBoundary');

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    logger.error('render error caught', {
      message: error.message,
      stack: error.stack,
      componentStack: info.componentStack,
    });
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
          <h2 style={{ color: '#1a1a1a', marginBottom: '1rem' }}>
            Something went wrong
          </h2>
          <pre style={{ color: '#dc2626', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
            {this.state.error?.message}
          </pre>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              fontSize: '0.85rem',
              border: '1px solid #d1d5db',
              borderRadius: '0.375rem',
              background: '#fff',
              cursor: 'pointer',
            }}
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
