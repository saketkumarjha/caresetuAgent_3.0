import { useState } from "react";
import StatusDisplay from "./StatusDisplay";
import ConnectionButton from "./ConnectionButton";
import MicrophoneButton from "./MicrophoneButton";
import ConnectionProgress from "./ConnectionProgress";
import ConversationDemo from "./ConversationDemo";

function VoiceInterface({
  // Connection props
  connectionStatus,
  connectionState,
  isConnected,
  isConnecting,
  onConnect,
  onDisconnect,

  // Reconnection props
  isAutoReconnecting,
  reconnectAttempts,
  maxAttempts,
  manualReconnectAvailable,
  onManualReconnect,
  onStopAutoReconnection,

  // Audio props
  isRecording,
  isPlaying,
  audioLevel,
  onStartRecording,
  onStopRecording,

  // Transcript props
  transcript,
  setTranscript,

  // Latency props
  latency,

  // Error handlers
  errorHandlers,

  // Room reference
  room,
}) {
  const [textInput, setTextInput] = useState("");

  // Send text message to agent
  const handleSendText = () => {
    if (!textInput.trim() || !isConnected || !room) return;

    try {
      // Send text message via LiveKit data channel
      const encoder = new TextEncoder();
      const data = encoder.encode(
        JSON.stringify({
          type: "text_message",
          text: textInput.trim(),
          timestamp: Date.now(),
        })
      );

      room.localParticipant.publishData(data);

      // Add to transcript
      const timestamp = new Date().toLocaleTimeString();
      setTranscript((prev) => [
        ...prev,
        {
          type: "user",
          text: textInput.trim(),
          timestamp,
          isText: true,
        },
      ]);

      setTextInput("");
    } catch (error) {
      console.error("Failed to send text message:", error);
      errorHandlers.showError("TEXT_SEND_FAILED", "Failed to send message");
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  // Add sample conversation data
  const handleAddSampleData = (sampleMessages) => {
    setTranscript(sampleMessages);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-lg font-medium text-white">
              Live Chat Session
            </h1>
            <div className="flex items-center space-x-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected
                    ? "bg-green-500"
                    : isConnecting
                    ? "bg-yellow-500 animate-pulse"
                    : "bg-red-500"
                }`}
              ></div>
              <span className="text-sm text-gray-300">{connectionStatus}</span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-400">Session: 01:08</span>
            <button className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm flex items-center space-x-1">
              <span>✕</span>
              <span>End Call</span>
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-80px)] px-6">
        {/* Main Connection Card */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 w-full max-w-md mb-6">
          <div className="text-center">
            <h2 className="text-xl font-medium text-white mb-6">
              Connect with AI Agent
            </h2>

            {/* Connection Buttons */}
            <div className="flex space-x-3 mb-8">
              <button
                onClick={isConnected ? onDisconnect : onConnect}
                disabled={isConnecting}
                className={`px-4 py-2 rounded flex items-center space-x-2 flex-1 transition-colors ${
                  isConnected
                    ? "bg-red-600 hover:bg-red-700"
                    : "bg-blue-600 hover:bg-blue-700"
                } text-white disabled:bg-gray-600`}
              >
                <span>{isConnected ? "📞" : "📞"}</span>
                <span>
                  {isConnected
                    ? "Disconnect"
                    : isConnecting
                    ? "Connecting..."
                    : "Connect to Agent"}
                </span>
              </button>
              <button
                onClick={isRecording ? onStopRecording : onStartRecording}
                disabled={!isConnected}
                className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-700 text-white px-4 py-2 rounded flex items-center space-x-2 flex-1 transition-colors"
              >
                <span>{isRecording ? "🔴" : "💬"}</span>
                <span>
                  {isRecording ? "Stop Recording" : "Start Conversation"}
                </span>
              </button>
            </div>

            {/* Audio Visualizer Circle */}
            <div className="relative mb-8">
              <div className="w-20 h-20 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-white"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                </svg>
              </div>

              {/* Audio Waveform */}
              <div className="flex items-center justify-center space-x-1 mb-6">
                {[...Array(20)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-1 bg-gradient-to-t from-blue-500 to-purple-500 rounded-full animate-pulse`}
                    style={{
                      height: `${Math.random() * 40 + 10}px`,
                      animationDelay: `${i * 0.1}s`,
                    }}
                  />
                ))}
              </div>
            </div>

            {/* Status Indicators */}
            <div className="flex justify-between items-center mb-6">
              <div className="text-center">
                <div className="text-sm text-gray-400 mb-1">
                  Connection Quality
                </div>
                <div className="flex space-x-1 justify-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <div className="w-2 h-2 bg-gray-600 rounded-full"></div>
                </div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-400 mb-1">AI Status</div>
                <div className="text-green-400 text-sm font-medium">
                  Listening
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Correction Card */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 w-full max-w-md">
          <div className="flex items-center space-x-2 mb-4">
            <svg
              className="w-5 h-5 text-gray-400"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
            </svg>
            <h3 className="text-white font-medium">Quick Correction</h3>
          </div>

          <div className="flex space-x-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type correction here..."
              className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={handleSendText}
              disabled={!textInput.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </button>
          </div>

          <div className="text-xs text-gray-400 mt-2 flex items-center space-x-1">
            <span>0/50 characters</span>
          </div>

          <div className="text-xs text-gray-500 mt-3 flex items-center space-x-1">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
            </svg>
            <span>
              Use this to correct misunderstood words during the conversation
            </span>
          </div>
        </div>

        {/* Hidden original components for functionality */}
        <div className="hidden">
          <ConnectionButton
            connectionState={connectionState}
            isConnected={isConnected}
            isConnecting={isConnecting}
            onConnect={onConnect}
            onDisconnect={onDisconnect}
            errorHandlers={errorHandlers}
            isAutoReconnecting={isAutoReconnecting}
            reconnectAttempts={reconnectAttempts}
            maxAttempts={maxAttempts}
            manualReconnectAvailable={manualReconnectAvailable}
            onManualReconnect={onManualReconnect}
            onStopAutoReconnection={onStopAutoReconnection}
          />

          <MicrophoneButton
            isConnected={isConnected}
            isRecording={isRecording}
            onStartRecording={onStartRecording}
            onStopRecording={onStopRecording}
            setTranscript={setTranscript}
            errorHandlers={errorHandlers}
            room={room}
          />
        </div>
      </div>
    </div>
  );
}

export default VoiceInterface;
