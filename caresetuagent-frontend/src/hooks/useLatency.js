import { useState, useEffect, useCallback, useRef } from "react";

const LATENCY_THRESHOLD = 1000; // 1 second as per requirements
const MEASUREMENT_INTERVAL = 5000; // Measure every 5 seconds
const PING_TIMEOUT = 3000; // Timeout for ping measurements

export function useLatency(room, isConnected) {
  const [latency, setLatency] = useState(0);
  const [isHighLatency, setIsHighLatency] = useState(false);
  const [averageLatency, setAverageLatency] = useState(0);
  const [latencyHistory, setLatencyHistory] = useState([]);

  const intervalRef = useRef(null);
  const pingStartTimeRef = useRef(null);
  const measurementCountRef = useRef(0);

  // Measure round-trip time using WebRTC data channel or ping-like mechanism
  const measureLatency = useCallback(async () => {
    if (!room || !isConnected) {
      return null;
    }

    try {
      const startTime = performance.now();
      pingStartTimeRef.current = startTime;

      // Use LiveKit's built-in ping mechanism if available
      if (room.engine && room.engine.ping) {
        const pingResult = await room.engine.ping();
        const roundTripTime = pingResult || performance.now() - startTime;
        return Math.round(roundTripTime);
      }

      // Fallback: Measure time for a simple data channel message
      if (room.localParticipant) {
        // Create a simple ping using data publishing
        const pingData = JSON.stringify({
          type: "ping",
          timestamp: startTime,
          id: Math.random().toString(36).substr(2, 9),
        });

        // Send ping data
        await room.localParticipant.publishData(
          new TextEncoder().encode(pingData),
          { reliable: true }
        );

        // For this fallback, we'll estimate based on connection quality
        // This is not a true round-trip measurement but gives us an indication
        const estimatedLatency = performance.now() - startTime;
        return Math.round(estimatedLatency);
      }

      return null;
    } catch (error) {
      console.warn("Latency measurement failed:", error);
      return null;
    }
  }, [room, isConnected]);

  // Update latency statistics
  const updateLatencyStats = useCallback(
    (newLatency) => {
      if (newLatency === null) return;

      setLatency(newLatency);

      // Update history (keep last 10 measurements)
      setLatencyHistory((prev) => {
        const updated = [...prev, newLatency].slice(-10);

        // Calculate average
        const avg = updated.reduce((sum, val) => sum + val, 0) / updated.length;
        setAverageLatency(Math.round(avg));

        return updated;
      });

      // Check if latency exceeds threshold
      const isHigh = newLatency > LATENCY_THRESHOLD;
      setIsHighLatency(isHigh);

      measurementCountRef.current += 1;

      // Log latency for debugging
      console.log(
        `Latency measurement #${measurementCountRef.current}: ${newLatency}ms (avg: ${averageLatency}ms)`
      );
    },
    [averageLatency]
  );

  // Start continuous latency monitoring
  const startMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    intervalRef.current = setInterval(async () => {
      const measuredLatency = await measureLatency();
      updateLatencyStats(measuredLatency);
    }, MEASUREMENT_INTERVAL);
  }, [measureLatency, updateLatencyStats]);

  // Stop latency monitoring
  const stopMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Manual latency measurement
  const measureNow = useCallback(async () => {
    const measuredLatency = await measureLatency();
    updateLatencyStats(measuredLatency);
    return measuredLatency;
  }, [measureLatency, updateLatencyStats]);

  // Reset latency data
  const resetLatency = useCallback(() => {
    setLatency(0);
    setIsHighLatency(false);
    setAverageLatency(0);
    setLatencyHistory([]);
    measurementCountRef.current = 0;
  }, []);

  // Effect to handle connection state changes
  useEffect(() => {
    if (isConnected && room) {
      // Start monitoring when connected
      startMonitoring();

      // Initial measurement
      setTimeout(() => {
        measureNow();
      }, 1000); // Wait 1 second after connection
    } else {
      // Stop monitoring when disconnected
      stopMonitoring();
      resetLatency();
    }

    return () => {
      stopMonitoring();
    };
  }, [
    isConnected,
    room,
    startMonitoring,
    stopMonitoring,
    measureNow,
    resetLatency,
  ]);

  // Listen for data messages that might be ping responses
  useEffect(() => {
    if (!room) return;

    const handleDataReceived = (payload, participant) => {
      try {
        const data = JSON.parse(new TextDecoder().decode(payload));
        if (data.type === "pong" && pingStartTimeRef.current) {
          const roundTripTime = performance.now() - pingStartTimeRef.current;
          updateLatencyStats(Math.round(roundTripTime));
          pingStartTimeRef.current = null;
        }
      } catch (error) {
        // Ignore non-JSON data
      }
    };

    room.on("dataReceived", handleDataReceived);

    return () => {
      room.off("dataReceived", handleDataReceived);
    };
  }, [room, updateLatencyStats]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopMonitoring();
    };
  }, [stopMonitoring]);

  return {
    latency,
    averageLatency,
    isHighLatency,
    latencyHistory,
    measureNow,
    resetLatency,
    isMonitoring: intervalRef.current !== null,
    threshold: LATENCY_THRESHOLD,
  };
}
