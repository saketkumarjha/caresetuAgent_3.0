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
    <div className="max-w-4xl mx-auto">
      {/* Demo Component */}
      {!isConnected && transcript.length === 0 && (
        <ConversationDemo onAddSampleData={handleAddSampleData} />
      )}

      {/* Header */}
      <div className="bg-white rounded-t-lg shadow-sm p-4 border-b">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-800">
            CareSetu Voice Assistant
          </h1>
          <div className="flex items-center gap-4">
            <StatusDisplay
              connectionStatus={connectionStatus}
              latency={latency}
            />
            {transcript.length > 0 && (
              <button
                onClick={() => setTranscript([])}
                className="text-sm text-gray-500 hover:text-gray-700 underline"
              >
                Clear Chat
              </button>
            )}
          </div>
        </div>

        <ConnectionProgress
          isConnecting={isConnecting || isAutoReconnecting}
          connectionState={connectionState}
        />
      </div>

      {/* Conversation Area */}
      <div className="bg-gray-50 h-96 overflow-y-auto p-4 border-l border-r border-gray-200">
        {transcript.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-4xl mb-2">🎤</div>
              <p>Connect to start your conversation with CareSetu Assistant</p>
              <p className="text-sm mt-1">
                I can help with appointments, health questions, and more!
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {transcript.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.type === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.type === "user"
                      ? "bg-blue-500 text-white"
                      : message.type === "agent"
                      ? "bg-white text-gray-800 shadow-sm border"
                      : "bg-gray-200 text-gray-600 text-sm"
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.type === "agent" && (
                      <div className="text-lg">🤖</div>
                    )}
                    {message.type === "user" && (
                      <div className="text-lg">
                        {message.isText ? "💬" : "🎤"}
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="text-sm">{message.text}</p>
                      <p
                        className={`text-xs mt-1 ${
                          message.type === "user"
                            ? "text-blue-100"
                            : "text-gray-400"
                        }`}
                      >
                        {message.timestamp}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* Audio Level Indicator */}
            {isRecording && (
              <div className="flex justify-end">
                <div className="bg-red-100 border border-red-200 rounded-lg px-3 py-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-sm text-red-700">Recording...</span>
                    <div className="flex space-x-1">
                      {[...Array(5)].map((_, i) => (
                        <div
                          key={i}
                          className={`w-1 h-4 rounded ${
                            audioLevel * 5 > i ? "bg-red-500" : "bg-red-200"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Agent Speaking Indicator */}
            {isPlaying && (
              <div className="flex justify-start">
                <div className="bg-blue-100 border border-blue-200 rounded-lg px-3 py-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    <span className="text-sm text-blue-700">
                      Agent is speaking...
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white rounded-b-lg shadow-sm p-4 border-t">
        {/* Text Input */}
        <div className="flex space-x-2 mb-3">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              isConnected
                ? "Type your message (email, name, etc.)..."
                : "Connect first to send messages"
            }
            disabled={!isConnected}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleSendText}
            disabled={!isConnected || !textInput.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>

        {/* Control Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <ConnectionButton
            connectionState={connectionState}
            isConnected={isConnected}
            isConnecting={isConnecting}
            onConnect={onConnect}
            onDisconnect={onDisconnect}
            errorHandlers={errorHandlers}
            // Reconnection props
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
