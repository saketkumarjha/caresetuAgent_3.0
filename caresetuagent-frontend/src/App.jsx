import { useState, useEffect, useCallback, useRef } from "react";

import VoiceInterface from "./components/VoiceInterface";
import ErrorDisplay from "./components/ErrorDisplay";
import DebugPanel from "./components/DebugPanel";
import { useConnection } from "./hooks/useConnection";
import { useAudio } from "./hooks/useAudio";
import { useError } from "./hooks/useError";
import { useToken } from "./hooks/useToken";
import { useLatency } from "./hooks/useLatency";
import { useReconnection } from "./hooks/useReconnection";

function App() {
  const [transcript, setTranscript] = useState([]);
  const disconnectionMessageAdded = useRef(false);

  // Initialize all custom hooks with error boundaries
  const {
    error,
    errorType,
    clearError,
    detectConnectionError,
    ...errorHandlers
  } = useError();

  const { token, generateToken, isTokenValid, refreshToken } = useToken();

  const {
    connectionState,
    room,
    connect,
    disconnect,
    isConnected,
    isConnecting,
    error: connectionError,
  } = useConnection();
  const {
    isRecording,
    isPlaying,
    audioLevel,
    startRecording,
    stopRecording,
    playRemoteAudio,
    localTrack,
    hasPermission,
    requestPermission,
  } = useAudio();
  const { latency, isHighLatency, measureNow, resetLatency } = useLatency(
    room,
    isConnected
  );

  // Initialize reconnection hook
  const {
    isAutoReconnecting,
    reconnectAttempts,
    maxAttempts,
    manualReconnectAvailable,
    manualReconnect,
    stopAutoReconnection,
    resetReconnectionState,
  } = useReconnection(connectionState, connect, disconnect, token);

  // Handle connection errors
  useEffect(() => {
    if (connectionError) {
      detectConnectionError({ message: connectionError });
    }
  }, [connectionError, detectConnectionError]);

  // Show high latency error when detected
  useEffect(() => {
    if (isHighLatency) {
      errorHandlers.showLatencyError();
    }
  }, [isHighLatency, errorHandlers]);

  // LiveKit room event handling with React effects
  useEffect(() => {
    if (!room) return;

    // Handle participant connected
    const handleParticipantConnected = (participant) => {
      console.log("Participant connected:", participant.identity);

      // Add system message to transcript
      const timestamp = new Date().toLocaleTimeString();
      setTranscript((prev) => [
        ...prev,
        {
          type: "system",
          text: `${participant.identity} joined the conversation`,
          timestamp,
        },
      ]);
    };

    // Handle participant disconnected
    const handleParticipantDisconnected = (participant) => {
      console.log("Participant disconnected:", participant.identity);

      // Add system message to transcript
      const timestamp = new Date().toLocaleTimeString();
      setTranscript((prev) => [
        ...prev,
        {
          type: "system",
          text: `${participant.identity} left the conversation`,
          timestamp,
        },
      ]);
    };

    // Handle track subscribed (incoming audio from agent)
    const handleTrackSubscribed = (track, publication, participant) => {
      console.log(
        "Track subscribed:",
        track.kind,
        "from",
        participant.identity
      );

      if (track.kind === "audio") {
        // Only play audio from other participants (not our own) to prevent echo
        if (participant.identity !== room.localParticipant.identity) {
          console.log("🔊 Playing audio from agent:", participant.identity);
          playRemoteAudio(track);

          // Add agent response to transcript
          const timestamp = new Date().toLocaleTimeString();
          setTranscript((prev) => [
            ...prev,
            {
              type: "agent",
              text: "🔊 Agent is responding...",
              timestamp,
              isText: false,
            },
          ]);
        } else {
          console.log(
            "🔇 Ignoring own audio to prevent echo from:",
            participant.identity
          );
        }
      }
    };

    // Handle track unsubscribed
    const handleTrackUnsubscribed = (track, publication, participant) => {
      console.log(
        "Track unsubscribed:",
        track.kind,
        "from",
        participant.identity
      );

      if (track.kind === "audio") {
        // Update transcript when agent stops speaking
        const timestamp = new Date().toLocaleTimeString();
        setTranscript((prev) => [
          ...prev,
          {
            type: "agent",
            text: "Agent finished speaking",
            timestamp,
          },
        ]);
      }
    };

    // Handle data received (for text responses or metadata)
    const handleDataReceived = (payload, participant) => {
      try {
        const data = JSON.parse(new TextDecoder().decode(payload));
        console.log("Data received from", participant?.identity, ":", data);

        // Handle different types of data messages
        switch (data.type) {
          case "transcript":
            // Agent sent a transcript of what it heard
            const timestamp = new Date().toLocaleTimeString();
            setTranscript((prev) => [
              ...prev,
              {
                type: "agent",
                text: `Agent heard: "${data.text}"`,
                timestamp,
              },
            ]);
            break;

          case "response":
            // Agent sent a text response
            const responseTimestamp = new Date().toLocaleTimeString();
            setTranscript((prev) => [
              ...prev,
              {
                type: "agent",
                text: data.text,
                timestamp: responseTimestamp,
                isText: true,
              },
            ]);
            break;

          case "user_speech":
            // User speech transcription from agent
            const userTimestamp = new Date().toLocaleTimeString();
            setTranscript((prev) => {
              // Replace the last "Speaking..." message with actual transcription
              const newTranscript = [...prev];
              const lastUserIndex = newTranscript
                .map((m) => m.type)
                .lastIndexOf("user");
              if (
                lastUserIndex !== -1 &&
                newTranscript[lastUserIndex].text.includes("Speaking")
              ) {
                newTranscript[lastUserIndex] = {
                  type: "user",
                  text: data.text,
                  timestamp: userTimestamp,
                  isText: false,
                };
              } else {
                newTranscript.push({
                  type: "user",
                  text: data.text,
                  timestamp: userTimestamp,
                  isText: false,
                });
              }
              return newTranscript;
            });
            break;

          case "agent_speech":
            // Agent speech transcription
            const agentTimestamp = new Date().toLocaleTimeString();
            setTranscript((prev) => {
              // Replace the last "Agent is responding..." message with actual transcription
              const newTranscript = [...prev];
              const lastAgentIndex = newTranscript
                .map((m) => m.type)
                .lastIndexOf("agent");
              if (
                lastAgentIndex !== -1 &&
                (newTranscript[lastAgentIndex].text.includes("responding") ||
                  newTranscript[lastAgentIndex].text.includes("🔊"))
              ) {
                newTranscript[lastAgentIndex] = {
                  type: "agent",
                  text: data.text,
                  timestamp: agentTimestamp,
                  isText: false,
                };
              } else {
                newTranscript.push({
                  type: "agent",
                  text: data.text,
                  timestamp: agentTimestamp,
                  isText: false,
                });
              }
              return newTranscript;
            });
            break;

          case "error":
            // Agent sent an error message
            errorHandlers.showError(
              "AGENT_ERROR",
              data.message || "Agent error occurred"
            );
            break;

          case "status":
            // Agent sent status update
            console.log("Agent status:", data.status);
            break;

          default:
            console.log("Unknown data type:", data.type);
        }
      } catch (error) {
        // Handle non-JSON data or parsing errors
        console.log(
          "Received non-JSON data:",
          new TextDecoder().decode(payload)
        );
      }
    };

    // Handle connection quality changes
    const handleConnectionQualityChanged = (quality, participant) => {
      console.log(
        "Connection quality changed:",
        quality,
        "for",
        participant?.identity
      );

      // Show warning for poor connection quality
      if (quality === "poor") {
        errorHandlers.showError(
          "POOR_CONNECTION",
          "Poor connection quality detected"
        );
      }
    };

    // Handle room metadata changes (for server-side error reporting)
    const handleRoomMetadataChanged = (metadata) => {
      try {
        const data = JSON.parse(metadata);
        console.log("Room metadata changed:", data);

        // Handle server-side errors
        if (data.error) {
          switch (data.error) {
            case "LLM_OVERLOAD":
              errorHandlers.showLLMOverloadError();
              break;
            case "HIGH_LATENCY":
              errorHandlers.showLatencyError();
              break;
            case "TOKEN_EXPIRED":
              errorHandlers.showTokenExpiredError();
              break;
            default:
              errorHandlers.showError(
                "SERVER_ERROR",
                data.message || "Server error occurred"
              );
          }
        }

        // Handle server status updates
        if (data.status) {
          console.log("Server status:", data.status);
        }
      } catch (error) {
        // Ignore non-JSON metadata
      }
    };

    // Handle track muted/unmuted
    const handleTrackMuted = (publication, participant) => {
      console.log(
        "Track muted:",
        publication.trackSid,
        "from",
        participant.identity
      );
    };

    const handleTrackUnmuted = (publication, participant) => {
      console.log(
        "Track unmuted:",
        publication.trackSid,
        "from",
        participant.identity
      );
    };

    // Add event listeners
    room.on("participantConnected", handleParticipantConnected);
    room.on("participantDisconnected", handleParticipantDisconnected);
    room.on("trackSubscribed", handleTrackSubscribed);
    room.on("trackUnsubscribed", handleTrackUnsubscribed);
    room.on("dataReceived", handleDataReceived);
    room.on("connectionQualityChanged", handleConnectionQualityChanged);
    room.on("roomMetadataChanged", handleRoomMetadataChanged);
    room.on("trackMuted", handleTrackMuted);
    room.on("trackUnmuted", handleTrackUnmuted);

    // Cleanup event listeners
    return () => {
      room.off("participantConnected", handleParticipantConnected);
      room.off("participantDisconnected", handleParticipantDisconnected);
      room.off("trackSubscribed", handleTrackSubscribed);
      room.off("trackUnsubscribed", handleTrackUnsubscribed);
      room.off("dataReceived", handleDataReceived);
      room.off("connectionQualityChanged", handleConnectionQualityChanged);
      room.off("roomMetadataChanged", handleRoomMetadataChanged);
      room.off("trackMuted", handleTrackMuted);
      room.off("trackUnmuted", handleTrackUnmuted);
    };
  }, [room, playRemoteAudio, setTranscript, errorHandlers]);

  // Handle existing participants and tracks when joining a room
  useEffect(() => {
    if (!room || !isConnected) return;

    // Process existing participants and their tracks
    if (room.participants) {
      room.participants.forEach((participant) => {
        console.log("Processing existing participant:", participant.identity);

        // Subscribe to existing audio tracks
        if (participant.audioTracks) {
          participant.audioTracks.forEach((publication) => {
            if (publication.track) {
              console.log(
                "Found existing audio track from",
                participant.identity
              );
              playRemoteAudio(publication.track);
            }
          });
        }

        // Subscribe to track events for this participant
        participant.on("trackSubscribed", (track, publication) => {
          if (track.kind === "audio") {
            console.log(
              "Subscribed to audio track from existing participant:",
              participant.identity
            );
            playRemoteAudio(track);
          }
        });
      });
    }

    // Add welcome message when successfully connected
    const timestamp = new Date().toLocaleTimeString();
    setTranscript((prev) => [
      ...prev,
      {
        type: "system",
        text: "Connected to CareSetu Voice Agent. You can start speaking!",
        timestamp,
      },
    ]);
  }, [room, isConnected, playRemoteAudio, setTranscript]);

  // Handle cleanup when disconnecting
  useEffect(() => {
    if (
      !isConnected &&
      transcript.length > 0 &&
      !disconnectionMessageAdded.current
    ) {
      // Add disconnection message only once
      const timestamp = new Date().toLocaleTimeString();
      setTranscript((prev) => [
        ...prev,
        {
          type: "system",
          text: "Disconnected from voice agent",
          timestamp,
        },
      ]);
      disconnectionMessageAdded.current = true;
    } else if (isConnected) {
      // Reset the flag when connected
      disconnectionMessageAdded.current = false;
    }
  }, [isConnected, transcript.length]);

  // Handle connection establishment
  const handleConnect = useCallback(async () => {
    console.log("🔗 Starting connection process...");
    try {
      clearError();
      console.log("🔗 Cleared previous errors");

      // Generate token if not available or expired
      let currentToken = token;
      console.log("🔗 Current token status:", {
        hasToken: !!currentToken,
        isValid: isTokenValid(),
      });

      if (!currentToken || !isTokenValid()) {
        console.log("🔗 Generating new token...");
        currentToken = await generateToken();
        console.log("🔗 Token generated successfully");
      }

      // Connect to LiveKit room
      console.log("🔗 Connecting to LiveKit room...");
      await connect(currentToken);
      console.log("🔗 Connection successful!");
    } catch (err) {
      console.error("🔗 Connection failed:", err);
      console.error("🔗 Error details:", {
        message: err.message,
        stack: err.stack,
        name: err.name,
      });
      detectConnectionError(err);
    }
  }, [
    token,
    isTokenValid,
    generateToken,
    connect,
    clearError,
    detectConnectionError,
  ]);

  // Handle stopping recording (defined before handleDisconnect to avoid reference error)
  const handleStopRecording = useCallback(async () => {
    try {
      console.log("🎤 Stopping recording...");
      stopRecording();

      // Unpublish audio track from room
      if (room && localTrack) {
        await room.localParticipant.unpublishTrack(localTrack);
        console.log("🎤 Audio track unpublished from room");
      }

      // Add user message to transcript
      const timestamp = new Date().toLocaleTimeString();
      setTranscript((prev) => [
        ...prev,
        {
          type: "user",
          text: "🎤 Finished speaking",
          timestamp,
          isText: false,
        },
      ]);
    } catch (err) {
      console.error("🎤 Failed to stop recording:", err);
    }
  }, [stopRecording, room, localTrack, setTranscript]);

  // Handle disconnection
  const handleDisconnect = useCallback(async () => {
    try {
      console.log("🔌 Manual disconnect initiated");

      // Stop recording first if active
      if (isRecording) {
        console.log("🔌 Stopping recording before disconnect");
        handleStopRecording();
      }

      // Stop auto-reconnection when manually disconnecting
      stopAutoReconnection();

      // Disconnect from room
      await disconnect();

      // Clear any errors
      clearError();

      console.log("🔌 Manual disconnect completed");
    } catch (err) {
      console.error("🔌 Error during disconnect:", err);
      // Still clear error even if disconnect fails
      clearError();
    }
  }, [
    disconnect,
    clearError,
    stopAutoReconnection,
    isRecording,
    handleStopRecording,
  ]);

  // Handle manual reconnection
  const handleManualReconnect = useCallback(async () => {
    try {
      clearError();
      await manualReconnect();
    } catch (err) {
      console.error("Manual reconnection failed:", err);
      detectConnectionError(err);
    }
  }, [manualReconnect, clearError, detectConnectionError]);

  // Handle microphone recording
  const handleStartRecording = useCallback(async () => {
    console.log("🎤 APP: handleStartRecording called");
    try {
      console.log("🎤 Handle start recording called");

      if (!isConnected) {
        errorHandlers.showError(
          "CONNECTION_REQUIRED",
          "Please connect to the agent first"
        );
        return;
      }

      if (!room) {
        errorHandlers.showError(
          "ROOM_NOT_AVAILABLE",
          "Room connection not available"
        );
        return;
      }

      // Check microphone permission first
      if (hasPermission === false) {
        errorHandlers.showError(
          "MICROPHONE_DENIED",
          "Microphone access denied. Please allow microphone access in your browser settings and refresh the page."
        );
        return;
      }

      if (hasPermission === null) {
        console.log("🎤 Requesting microphone permission...");
        const granted = await requestPermission();
        if (!granted) {
          errorHandlers.showError(
            "MICROPHONE_DENIED",
            "Microphone access is required for voice conversation. Please allow microphone access and try again."
          );
          return;
        }
      }

      console.log("🎤 Starting recording...");
      // Start recording and publish to room
      const audioTrack = await startRecording();

      if (audioTrack) {
        console.log("🎤 Publishing audio track to room...");
        await room.localParticipant.publishTrack(audioTrack);
        console.log("🎤 Audio track published successfully");

        // Add user message to transcript
        const timestamp = new Date().toLocaleTimeString();
        setTranscript((prev) => [
          ...prev,
          {
            type: "user",
            text: "🎤 Speaking...",
            timestamp,
            isText: false,
          },
        ]);
      } else {
        throw new Error("Failed to create audio track");
      }
    } catch (err) {
      console.error("🎤 Failed to start recording:", err);
      console.error("🎤 Full error details:", {
        name: err.name,
        message: err.message,
        stack: err.stack,
        cause: err.cause,
      });

      // Provide specific error messages based on error type
      let errorMessage = "Failed to start recording. ";
      if (
        err.name === "NotAllowedError" ||
        err.message.includes("permission")
      ) {
        errorMessage +=
          "Please allow microphone access in your browser settings.";
      } else if (err.name === "NotFoundError") {
        errorMessage +=
          "No microphone found. Please connect a microphone and try again.";
      } else if (err.name === "NotReadableError") {
        errorMessage += "Microphone is being used by another application.";
      } else {
        errorMessage +=
          err.message || "Please check your microphone and try again.";
      }

      errorHandlers.showError("RECORDING_FAILED", errorMessage);
    }
  }, [
    isConnected,
    hasPermission,
    requestPermission,
    startRecording,
    room,
    errorHandlers,
    setTranscript,
  ]);

  // Get connection status for display
  const getConnectionStatus = () => {
    switch (connectionState) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      case "reconnecting":
        return "Reconnecting...";
      case "error":
        return "Connection Error";
      default:
        return "Disconnected";
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <main className="min-h-screen">
        <VoiceInterface
          // Connection props
          connectionStatus={getConnectionStatus()}
          connectionState={connectionState}
          isConnected={isConnected}
          isConnecting={isConnecting}
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
          // Reconnection props
          isAutoReconnecting={isAutoReconnecting}
          reconnectAttempts={reconnectAttempts}
          maxAttempts={maxAttempts}
          manualReconnectAvailable={manualReconnectAvailable}
          onManualReconnect={handleManualReconnect}
          onStopAutoReconnection={stopAutoReconnection}
          // Audio props
          isRecording={isRecording}
          isPlaying={isPlaying}
          audioLevel={audioLevel}
          onStartRecording={handleStartRecording}
          onStopRecording={handleStopRecording}
          // Transcript props
          transcript={transcript}
          setTranscript={setTranscript}
          // Latency props
          latency={latency}
          // Error handlers
          errorHandlers={errorHandlers}
          // Room reference for child components
          room={room}
        />

        <ErrorDisplay
          error={error}
          errorType={errorType}
          onClear={clearError}
        />
      </main>
    </div>
  );
}

export default App;
