import { useState, useEffect } from "react";

function StatusDisplay({ connectionStatus, latency }) {
  const [connectionTime, setConnectionTime] = useState(0);
  const [showProgress, setShowProgress] = useState(false);

  // Track connection time
  useEffect(() => {
    let interval;
    if (
      connectionStatus === "Connecting..." ||
      connectionStatus === "Reconnecting..."
    ) {
      setShowProgress(true);
      setConnectionTime(0);
      interval = setInterval(() => {
        setConnectionTime((prev) => prev + 1);
      }, 1000);
    } else {
      setShowProgress(false);
      setConnectionTime(0);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [connectionStatus]);

  const getStatusColor = (status) => {
    switch (status) {
      case "Connected":
        return "bg-green-100 text-green-800 border-green-200";
      case "Connecting...":
      case "Reconnecting...":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "Disconnected":
        return "bg-gray-100 text-gray-800 border-gray-200";
      case "Error":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusMessage = (status) => {
    if (status === "Connecting..." && connectionTime > 5) {
      return "Connecting... (Server may be starting up - please wait)";
    }
    return status;
  };

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${
            connectionStatus === "Connected"
              ? "bg-green-500"
              : connectionStatus === "Connecting..." ||
                connectionStatus === "Reconnecting..."
              ? "bg-yellow-500 animate-pulse"
              : connectionStatus === "Error"
              ? "bg-red-500"
              : "bg-gray-400"
          }`}
        ></div>
        <span className="text-sm font-medium text-gray-700">
          {getStatusMessage(connectionStatus)}
        </span>
      </div>

      {showProgress && connectionTime > 0 && (
        <div className="text-xs text-gray-500">{connectionTime}s</div>
      )}

      {connectionStatus === "Connected" && latency > 0 && (
        <div
          className={`text-xs ${
            latency > 1000 ? "text-red-600" : "text-green-600"
          }`}
        >
          {latency}ms
        </div>
      )}
    </div>
  );
}

export default StatusDisplay;
