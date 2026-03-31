import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || "Something went wrong" };
  }

  componentDidCatch(error, info) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex flex-col items-center justify-center p-8 rounded-xl bg-slate-800/60 border border-red-500/30 text-center space-y-3">
            <span className="text-3xl">⚠️</span>
            <p className="text-slate-200 font-medium">Something went wrong loading this section.</p>
            <p className="text-slate-400 text-sm">{this.state.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, message: null })}
              className="px-4 py-2 text-sm rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors"
            >
              Try again
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
