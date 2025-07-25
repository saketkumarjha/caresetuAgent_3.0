import { useEffect } from "react";

function ErrorDisplay({ error, errorType, onClear }) {
  // Auto-clear error after 10 seconds for non-critical errors
  useEffect(() => {
    if (
      error &&
      errorType !== "CONNECTION_LOST" &&
      errorType !== "BACKEND_UNAVAILABLE"
    ) {
      const timer = setTimeout(() => {
        if (onClear) onClear();
      }, 10000);

      return () => clearTimeout(timer);
    }
  }, [error, errorType, onClear]);

  if (!error) return null;

  // Determine error severity and styling
  const isWarning = errorType === "HIGH_LATENCY";
  const isCritical =
    errorType === "CONNECTION_LOST" || errorType === "BACKEND_UNAVAILABLE";

  const baseClasses =
    "px-4 py-3 rounded-lg mb-4 shadow-md transition-all duration-300";
  const warningClasses =
    "bg-yellow-900 border border-yellow-600 text-yellow-200";
  const errorClasses = "bg-red-900 border border-red-600 text-red-200";
  const criticalClasses = "bg-red-800 border-2 border-red-500 text-red-100";

  let containerClasses = baseClasses;
  let iconColor = "text-red-400";
  let icon = "⚠️";

  if (isWarning) {
    containerClasses += ` ${warningClasses}`;
    iconColor = "text-yellow-400";
    icon = "⚠️";
  } else if (isCritical) {
    containerClasses += ` ${criticalClasses}`;
    iconColor = "text-red-300";
    icon = "🚫";
  } else {
    containerClasses += ` ${errorClasses}`;
    iconColor = "text-red-400";
    icon = "⚠️";
  }

  return (
    <div className={containerClasses}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`text-lg ${iconColor}`}>{icon}</span>
          <div className="flex flex-col">
            <span className="font-medium">
              {isWarning
                ? "Warning:"
                : isCritical
                ? "Critical Error:"
                : "Error:"}
            </span>
            <span className="text-sm">{error}</span>
          </div>
        </div>

        {/* Close button for non-critical errors */}
        {!isCritical && onClear && (
          <button
            onClick={onClear}
            className="ml-4 text-gray-400 hover:text-gray-200 transition-colors duration-200"
            aria-label="Close error message"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Additional info for specific error types */}
      {errorType === "TOKEN_EXPIRED" && (
        <div className="mt-2 text-xs opacity-75">
          Please refresh the page to get a new authentication token.
        </div>
      )}

      {errorType === "MICROPHONE_DENIED" && (
        <div className="mt-2 text-xs opacity-75">
          Please allow microphone access in your browser settings and refresh
          the page.
        </div>
      )}

      {errorType === "HIGH_LATENCY" && (
        <div className="mt-2 text-xs opacity-75">
          Check your internet connection for better performance.
        </div>
      )}

      {(errorType === "BACKEND_UNAVAILABLE" ||
        errorType === "CONNECTION_TIMEOUT") && (
        <div className="mt-2 text-xs opacity-75">
          <p>
            The voice agent is hosted on Render.com's free tier, which may take
            20-30 seconds to start up after being idle.
          </p>
          <p className="mt-1">Please wait a moment and try connecting again.</p>
        </div>
      )}

      {errorType === "CONNECTION_LOST" && (
        <div className="mt-2 text-xs opacity-75">
          <p>
            Connection was lost. The system will automatically try to reconnect.
          </p>
          <p className="mt-1">
            If this persists, the Render.com service may have gone to sleep.
          </p>
        </div>
      )}
    </div>
  );
}

export default ErrorDisplay;
