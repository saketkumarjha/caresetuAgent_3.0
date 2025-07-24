import { useState, useCallback } from "react";

// Error types based on requirements
export const ERROR_TYPES = {
  HIGH_LATENCY: "HIGH_LATENCY",
  CONNECTION_LOST: "CONNECTION_LOST",
  TOKEN_EXPIRED: "TOKEN_EXPIRED",
  LLM_OVERLOAD: "LLM_OVERLOAD",
  NETWORK_ERROR: "NETWORK_ERROR",
  BACKEND_UNAVAILABLE: "BACKEND_UNAVAILABLE",
  MICROPHONE_DENIED: "MICROPHONE_DENIED",
  CONNECTION_TIMEOUT: "CONNECTION_TIMEOUT",
};

// Predefined error message mappings based on requirements
const ERROR_MESSAGES = {
  [ERROR_TYPES.HIGH_LATENCY]: "High latency - slow response",
  [ERROR_TYPES.CONNECTION_LOST]: "Connection lost",
  [ERROR_TYPES.TOKEN_EXPIRED]: "Token expired - refresh needed",
  [ERROR_TYPES.LLM_OVERLOAD]: "AI service overloaded",
  [ERROR_TYPES.NETWORK_ERROR]: "Network error",
  [ERROR_TYPES.BACKEND_UNAVAILABLE]: "Backend server unavailable",
  [ERROR_TYPES.MICROPHONE_DENIED]: "Microphone access required",
  [ERROR_TYPES.CONNECTION_TIMEOUT]: "Backend server unavailable",
};

export function useError() {
  const [error, setError] = useState(null);
  const [errorType, setErrorType] = useState(null);

  const showError = useCallback((type, customMessage = null) => {
    const message =
      customMessage || ERROR_MESSAGES[type] || "An unknown error occurred";
    setError(message);
    setErrorType(type);

    // Log technical details for debugging
    console.error(`Error [${type}]:`, message);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    setErrorType(null);
  }, []);

  // Helper functions for specific error types
  const showLatencyError = useCallback(() => {
    showError(ERROR_TYPES.HIGH_LATENCY);
  }, [showError]);

  const showConnectionLostError = useCallback(() => {
    showError(ERROR_TYPES.CONNECTION_LOST);
  }, [showError]);

  const showTokenExpiredError = useCallback(() => {
    showError(ERROR_TYPES.TOKEN_EXPIRED);
  }, [showError]);

  const showLLMOverloadError = useCallback(() => {
    showError(ERROR_TYPES.LLM_OVERLOAD);
  }, [showError]);

  const showNetworkError = useCallback(() => {
    showError(ERROR_TYPES.NETWORK_ERROR);
  }, [showError]);

  const showBackendUnavailableError = useCallback(() => {
    showError(ERROR_TYPES.BACKEND_UNAVAILABLE);
  }, [showError]);

  const showMicrophoneDeniedError = useCallback(() => {
    showError(ERROR_TYPES.MICROPHONE_DENIED);
  }, [showError]);

  const showConnectionTimeoutError = useCallback(() => {
    showError(ERROR_TYPES.CONNECTION_TIMEOUT);
  }, [showError]);

  // Error detection helpers
  const detectConnectionError = useCallback(
    (error) => {
      if (!error) return;

      const errorMessage = error.message?.toLowerCase() || "";
      const errorCode = error.code;

      // Detect specific error types based on error patterns
      if (errorMessage.includes("timeout") || errorCode === "TIMEOUT") {
        showConnectionTimeoutError();
      } else if (errorMessage.includes("taking longer than expected")) {
        showError(
          "SERVER_STARTING",
          "Server is starting up - this may take a moment on Render.com"
        );
      } else if (
        errorMessage.includes("network") ||
        errorMessage.includes("fetch")
      ) {
        showNetworkError();
      } else if (
        errorMessage.includes("token") ||
        errorMessage.includes("unauthorized") ||
        errorCode === 401
      ) {
        showTokenExpiredError();
      } else if (
        errorMessage.includes("overload") ||
        errorMessage.includes("rate limit") ||
        errorCode === 429
      ) {
        showLLMOverloadError();
      } else if (
        errorMessage.includes("connection") ||
        errorMessage.includes("websocket")
      ) {
        showConnectionLostError();
      } else if (
        errorMessage.includes("microphone") ||
        errorMessage.includes("permission")
      ) {
        showMicrophoneDeniedError();
      } else {
        // Default to backend unavailable for unknown errors
        showBackendUnavailableError();
      }
    },
    [
      showConnectionTimeoutError,
      showNetworkError,
      showTokenExpiredError,
      showLLMOverloadError,
      showConnectionLostError,
      showMicrophoneDeniedError,
      showBackendUnavailableError,
    ]
  );

  return {
    error,
    errorType,
    showError,
    clearError,
    showLatencyError,
    showConnectionLostError,
    showTokenExpiredError,
    showLLMOverloadError,
    showNetworkError,
    showBackendUnavailableError,
    showMicrophoneDeniedError,
    showConnectionTimeoutError,
    detectConnectionError,
  };
}
