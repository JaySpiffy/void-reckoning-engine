import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    children?: ReactNode;
    title?: string;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class PanelErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Panel Error:', error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    padding: '2rem',
                    background: 'rgba(255, 0, 0, 0.05)',
                    border: '1px solid rgba(255, 0, 0, 0.2)',
                    borderRadius: '1rem',
                    color: '#ff6b6b',
                    textAlign: 'center'
                }}>
                    <h3>{this.props.title || 'Analysis Panel'} Error</h3>
                    <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>
                        {this.state.error?.message || 'An unexpected error occurred while rendering this panel.'}
                    </p>
                    <button
                        onClick={() => this.setState({ hasError: false })}
                        style={{
                            marginTop: '1rem',
                            padding: '0.5rem 1rem',
                            background: 'rgba(255, 255, 255, 0.1)',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            borderRadius: '0.5rem',
                            color: 'white',
                            cursor: 'pointer'
                        }}
                    >
                        Retry Panel
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
