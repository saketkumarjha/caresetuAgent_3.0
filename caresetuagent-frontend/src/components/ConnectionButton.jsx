function ConnectionButton({
  connectionState,
  isConnected,
  isConnecting,
  onConnect,
  onDisconnect,
  errorHandlers,
  // Reconnection props
  isAutoReconnecting,
  reconnectAttempts,
  maxAttempts,
  manualReconnectAvailable,
  onManualReconnect,
  onStopAutoReconnection,
}) {
  const handleClick = async () => {
    if (isConnected) {
      // Stop auto-reconnection when manually disconnecting
      onStopAutoReconnection?.();
      onDisconnect();
      errorHandlers?.clearError();
    } else if (manualReconnectAvailable) {
      // Manual reconnection
      try {
        await onManualReconnect();
        errorHandlers?.clearError();
      } catch (error) {
        errorHandlers?.detectConnectionError(error);
      }
    } else {
      // Normal connection
      await onConnect();
    }
  };

  const getButtonText = () => {
    if (isAutoReconnecting) {
      return `Reconnecting... (${reconnectAttempts}/${maxAttempts})`;
    }

    switch (connectionState) {
      case "connected":
        return "Disconnect";
      case "connecting":
        return "Connecting...";
      case "reconnecting":
        return "Reconnecting...";
      default:
        if (manualReconnectAvailable) {
          return "Retry Connection";
        }
        return "Connect to Agent";
    }
  };

  const getButtonStyle = () => {
    if (isConnected) {
      return "bg-red-600 hover:bg-red-700";
    }
    if (
      isConnecting ||
      connectionState === "reconnecting" ||
      isAutoReconnecting
    ) {
      return "bg-yellow-600 hover:bg-yellow-700";
    }
    if (manualReconnectAvailable) {
      return "bg-green-600 hover:bg-green-700";
    }
    return "bg-blue-600 hover:bg-blue-700";
  };

  const isDisabled =
    isConnecting || connectionState === "reconnecting" || isAutoReconnecting;

  return (
    <div className="flex flex-col items-center space-y-2">
      <button
        className={`${getButtonStyle()} text-white px-6 py-3 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed min-w-[200px]`}
        onClick={handleClick}
        disabled={isDisabled}
      >
        {getButtonText()}
      </button>

      {/* Show reconnection status */}
      {isAutoReconnecting && (
        <div className="text-sm text-gray-600 text-center">
          <p>Attempting to reconnect automatically...</p>
          <p>
            Attempt {reconnectAttempts} of {maxAttempts}
          </p>
        </div>
      )}

      {/* Show manual reconnection option */}
      {manualReconnectAvailable && !isAutoReconnecting && (
        <div className="text-sm text-gray-600 text-center">
          <p>Automatic reconnection failed</p>
          <p>Click "Retry Connection" to try again</p>
        </div>
      )}

      {/* Stop auto-reconnection button */}
      {isAutoReconnecting && (
        <button
          className="text-sm text-red-600 hover:text-red-800 underline"
          onClick={() => {
            onStopAutoReconnection?.();
            errorHandlers?.clearError();
          }}
        >
          Stop trying to reconnect
        </button>
      )}
    </div>
  );
}

export default ConnectionButton;
