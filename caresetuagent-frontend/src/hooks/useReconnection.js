import { useState, useEffect, useCallback, useRef } from "react";

// Exponential backoff configuration
const INITIAL_RETRY_DELAY = 1000; // 1 second
const MAX_RETRY_DELAY = 30000; // 30 seconds
const MAX_RETRY_ATTEMPTS = 5;
const BACKOFF_MULTIPLIER = 2;

export const useReconnection = (
  connectionState,
  connect,
  disconnect,
  token
) => {
  const [isAutoReconnecting, setIsAutoReconnecting] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [nextRetryDelay, setNextRetryDelay] = useState(INITIAL_RETRY_DELAY);
  const [manualReconnectAvailable, setManualReconnectAvailable] =
    useState(false);

  const reconnectTimeoutRef = useRef(null);
  const isReconnectingRef = useRef(false);

  // Calculate exponential backoff delay
  const calculateBackoffDelay = useCallback((attempt) => {
    const delay = INITIAL_RETRY_DELAY * Math.pow(BACKOFF_MULTIPLIER, attempt);
    return Math.min(delay, MAX_RETRY_DELAY);
  }, []);

  // Reset reconnection state
  const resetReconnectionState = useCallback(() => {
    setIsAutoReconnecting(false);
    setReconnectAttempts(0);
    setNextRetryDelay(INITIAL_RETRY_DELAY);
    setManualReconnectAvailable(false);
    isReconnectingRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Perform automatic reconnection attempt
  const attemptReconnection = useCallback(async () => {
    if (isReconnectingRef.current || reconnectAttempts >= MAX_RETRY_ATTEMPTS) {
      return;
    }

    isReconnectingRef.current = true;
    setIsAutoReconnecting(true);

    try {
      console.log(
        `Reconnection attempt ${reconnectAttempts + 1}/${MAX_RETRY_ATTEMPTS}`
      );

      // Ensure clean disconnect before reconnecting
      await disconnect();

      // Wait a brief moment for cleanup
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Attempt to reconnect
      await connect(token);

      // If successful, reset reconnection state
      resetReconnectionState();
      console.log("Automatic reconnection successful");
    } catch (error) {
      console.error("Reconnection attempt failed:", error);

      const newAttempts = reconnectAttempts + 1;
      setReconnectAttempts(newAttempts);

      if (newAttempts >= MAX_RETRY_ATTEMPTS) {
        // Max attempts reached, enable manual reconnection
        setIsAutoReconnecting(false);
        setManualReconnectAvailable(true);
        isReconnectingRef.current = false;
        console.log(
          "Max reconnection attempts reached, manual reconnection available"
        );
      } else {
        // Schedule next attempt with exponential backoff
        const delay = calculateBackoffDelay(newAttempts);
        setNextRetryDelay(delay);

        reconnectTimeoutRef.current = setTimeout(() => {
          isReconnectingRef.current = false;
          attemptReconnection();
        }, delay);

        console.log(`Next reconnection attempt in ${delay}ms`);
      }
    }
  }, [
    reconnectAttempts,
    connect,
    disconnect,
    token,
    calculateBackoffDelay,
    resetReconnectionState,
  ]);

  // Manual reconnection function
  const manualReconnect = useCallback(async () => {
    try {
      console.log("Manual reconnection initiated");

      // Reset state for manual attempt
      resetReconnectionState();
      setIsAutoReconnecting(true);

      // Ensure clean disconnect
      await disconnect();
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Attempt reconnection
      await connect(token);

      console.log("Manual reconnection successful");
    } catch (error) {
      console.error("Manual reconnection failed:", error);
      setIsAutoReconnecting(false);
      setManualReconnectAvailable(true);
      throw error; // Re-throw to allow error handling in UI
    }
  }, [connect, disconnect, token, resetReconnectionState]);

  // Track previous connection state to detect unexpected disconnections
  const prevConnectionStateRef = useRef(connectionState);

  // Track if disconnect was manual
  const manualDisconnectRef = useRef(false);

  // Start automatic reconnection when connection is lost unexpectedly
  useEffect(() => {
    const prevState = prevConnectionStateRef.current;
    prevConnectionStateRef.current = connectionState;

    // Start auto-reconnection if:
    // 1. We just became disconnected
    // 2. We were previously connected or connecting
    // 3. We're not already reconnecting
    // 4. We haven't exceeded max attempts
    // 5. The disconnect was NOT manual
    if (
      connectionState === "disconnected" &&
      (prevState === "connected" || prevState === "connecting") &&
      !isReconnectingRef.current &&
      reconnectAttempts < MAX_RETRY_ATTEMPTS &&
      !manualDisconnectRef.current
    ) {
      console.log(
        "Connection lost unexpectedly, starting automatic reconnection"
      );
      attemptReconnection();
    }

    // Reset manual disconnect flag after processing
    if (connectionState === "disconnected") {
      setTimeout(() => {
        manualDisconnectRef.current = false;
      }, 1000);
    }
  }, [connectionState, attemptReconnection, reconnectAttempts]);

  // Reset when successfully connected
  useEffect(() => {
    if (connectionState === "connected") {
      resetReconnectionState();
    }
  }, [connectionState, resetReconnectionState]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Stop auto-reconnection (for manual disconnect)
  const stopAutoReconnection = useCallback(() => {
    console.log("🔄 Stopping auto-reconnection - manual disconnect");
    manualDisconnectRef.current = true;

    // Clear any pending reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Reset all reconnection state
    resetReconnectionState();

    console.log("🔄 Auto-reconnection stopped successfully");
  }, [resetReconnectionState]);

  return {
    isAutoReconnecting,
    reconnectAttempts,
    maxAttempts: MAX_RETRY_ATTEMPTS,
    nextRetryDelay,
    manualReconnectAvailable,
    manualReconnect,
    stopAutoReconnection,
    resetReconnectionState,
  };
};
