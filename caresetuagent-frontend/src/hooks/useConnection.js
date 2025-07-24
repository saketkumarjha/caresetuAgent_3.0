import { useState, useEffect, useCallback, useRef } from "react";
import { Room, RoomEvent, ConnectionState } from "livekit-client";

const CONNECTION_TIMEOUT = 30000; // 30 seconds for Render.com cold starts

export const useConnection = () => {
  const [connectionState, setConnectionState] = useState("disconnected");
  const [room, setRoom] = useState(null);
  const [error, setError] = useState(null);
  const connectionTimeoutRef = useRef(null);
  const roomRef = useRef(null);

  // Connection state mapping
  const getConnectionStatus = (state) => {
    switch (state) {
      case ConnectionState.Disconnected:
        return "disconnected";
      case ConnectionState.Connecting:
        return "connecting";
      case ConnectionState.Connected:
        return "connected";
      case ConnectionState.Reconnecting:
        return "reconnecting";
      default:
        return "disconnected";
    }
  };

  // Connect to LiveKit room
  const connect = useCallback(
    async (token) => {
      if (roomRef.current) {
        console.log("Already connected or connecting");
        return;
      }

      try {
        setConnectionState("connecting");
        setError(null);

        // Create new room instance
        const newRoom = new Room();
        roomRef.current = newRoom;
        setRoom(newRoom);

        // Set up connection timeout with Render.com-specific messaging
        connectionTimeoutRef.current = setTimeout(() => {
          if (connectionState === "connecting") {
            setError(
              "Connection timeout - Render.com service may need more time to start up. Please try again in a moment."
            );
            setConnectionState("error");
            disconnect();
          }
        }, CONNECTION_TIMEOUT);

        // Set up room event listeners
        newRoom.on(RoomEvent.Connected, () => {
          console.log("Connected to room");
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
          }
          setConnectionState("connected");
          setError(null);
        });

        newRoom.on(RoomEvent.Disconnected, (reason) => {
          console.log("Disconnected from room:", reason);
          setConnectionState("disconnected");
          if (reason && reason !== "CLIENT_INITIATED") {
            setError("Connection lost");
          }
          cleanup();
        });

        newRoom.on(RoomEvent.Reconnecting, () => {
          console.log("Reconnecting to room");
          setConnectionState("reconnecting");
        });

        newRoom.on(RoomEvent.Reconnected, () => {
          console.log("Reconnected to room");
          setConnectionState("connected");
          setError(null);
        });

        newRoom.on(RoomEvent.ConnectionStateChanged, (state) => {
          console.log("Connection state changed:", state);
          const status = getConnectionStatus(state);
          setConnectionState(status);

          if (state === ConnectionState.Disconnected) {
            cleanup();
          }
        });

        // Handle connection errors
        newRoom.on(RoomEvent.RoomMetadataChanged, (metadata) => {
          try {
            const data = JSON.parse(metadata);
            if (data.error) {
              handleServerError(data.error);
            }
          } catch (e) {
            // Ignore non-JSON metadata
          }
        });

        // Connect to the room
        const livekitUrl = import.meta.env.VITE_LIVEKIT_URL;
        if (!livekitUrl) {
          throw new Error("LiveKit URL not configured");
        }

        await newRoom.connect(livekitUrl, token);
      } catch (err) {
        console.error("Connection error:", err);

        // Clear timeout on error
        if (connectionTimeoutRef.current) {
          clearTimeout(connectionTimeoutRef.current);
          connectionTimeoutRef.current = null;
        }

        // Handle specific error types
        if (err.message.includes("token")) {
          setError("Token expired - refresh needed");
        } else if (
          err.message.includes("network") ||
          err.message.includes("fetch")
        ) {
          setError("Network error");
        } else if (err.message.includes("timeout")) {
          setError("Backend server unavailable");
        } else {
          setError("Connection failed");
        }

        setConnectionState("error");
        cleanup();
      }
    },
    [connectionState]
  );

  // Handle server-side errors from room metadata
  const handleServerError = (errorType) => {
    switch (errorType) {
      case "LLM_OVERLOAD":
        setError("AI service overloaded");
        break;
      case "HIGH_LATENCY":
        setError("High latency - slow response");
        break;
      case "TOKEN_EXPIRED":
        setError("Token expired - refresh needed");
        break;
      default:
        setError("Server error occurred");
    }
  };

  // Disconnect from room
  const disconnect = useCallback(async () => {
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }

    if (roomRef.current) {
      try {
        // Properly disconnect and wait for cleanup
        await roomRef.current.disconnect();
      } catch (error) {
        console.warn("Error during disconnect:", error);
      }
    }

    cleanup();
  }, []);

  // Enhanced cleanup function with proper resource management
  const cleanup = useCallback(() => {
    if (roomRef.current) {
      try {
        // Remove all event listeners to prevent memory leaks
        roomRef.current.removeAllListeners();

        // Unpublish all local tracks
        roomRef.current.localParticipant.audioTracks.forEach((publication) => {
          if (publication.track) {
            publication.track.stop();
            roomRef.current.localParticipant.unpublishTrack(publication.track);
          }
        });

        roomRef.current.localParticipant.videoTracks.forEach((publication) => {
          if (publication.track) {
            publication.track.stop();
            roomRef.current.localParticipant.unpublishTrack(publication.track);
          }
        });

        // Clear room reference
        roomRef.current = null;
      } catch (error) {
        console.warn("Error during cleanup:", error);
        roomRef.current = null;
      }
    }

    setRoom(null);
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connectionState,
    room,
    error,
    connect,
    disconnect,
    isConnected: connectionState === "connected",
    isConnecting: connectionState === "connecting",
    isDisconnected: connectionState === "disconnected",
    isReconnecting: connectionState === "reconnecting",
    hasError: connectionState === "error",
  };
};
