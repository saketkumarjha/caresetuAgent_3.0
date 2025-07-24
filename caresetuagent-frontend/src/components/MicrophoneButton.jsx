function MicrophoneButton({
  isConnected,
  isRecording,
  onStartRecording,
  onStopRecording,
  setTranscript,
  errorHandlers,
  room,
}) {
  const handleMicrophoneClick = async () => {
    console.log("🎤 BUTTON: Microphone button clicked!", {
      isConnected,
      isRecording,
    });

    if (!isConnected) {
      console.log("🎤 BUTTON: Not connected, showing error");
      errorHandlers.showError(
        "CONNECTION_REQUIRED",
        "Please connect to the agent first"
      );
      return;
    }

    if (isRecording) {
      // Stop recording
      try {
        await onStopRecording();

        // Add a user message to transcript
        const timestamp = new Date().toLocaleTimeString();
        setTranscript((prev) => [
          ...prev,
          {
            type: "user",
            text: "Audio message recorded and sent to agent",
            timestamp,
          },
        ]);
      } catch (error) {
        console.error("Failed to stop recording:", error);
        errorHandlers.showError("RECORDING_ERROR", "Failed to stop recording");
      }
    } else {
      // Start recording - let App component handle errors
      console.log("🎤 MicrophoneButton: Starting recording...");
      await onStartRecording();
      errorHandlers.clearError();
    }
  };

  const isDisabled = !isConnected;

  // Show button text based on state
  const getButtonText = () => {
    return isRecording ? "Stop Recording" : "Start Conversation";
  };

  const getButtonIcon = () => {
    return isRecording ? "🔴" : "🎤";
  };

  return (
    <button
      className={`${
        isRecording
          ? "bg-red-600 hover:bg-red-700"
          : "bg-green-600 hover:bg-green-700"
      } text-white px-6 py-3 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
      onClick={handleMicrophoneClick}
      disabled={isDisabled}
    >
      <span className="text-xl">{getButtonIcon()}</span>
      {getButtonText()}
    </button>
  );
}

export default MicrophoneButton;
