import { useState, useEffect } from "react";

function ConnectionProgress({ isConnecting, connectionState }) {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [currentMessage, setCurrentMessage] = useState("");

  // Progress messages based on elapsed time
  const progressMessages = [
    { time: 0, message: "Connecting to CareSetu Voice Agent..." },
    { time: 3000, message: "Establishing secure connection..." },
    {
      time: 8000,
      message: "Server is starting up (this may take a moment)...",
    },
    { time: 15000, message: "Render.com is waking up the service..." },
    { time: 20000, message: "Almost ready, finalizing startup..." },
    { time: 25000, message: "Connection should be ready soon..." },
  ];

  // Track elapsed time during connection
  useEffect(() => {
    let interval = null;

    if (isConnecting) {
      setElapsedTime(0);
      interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1000);
      }, 1000);
    } else {
      setElapsedTime(0);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isConnecting]);

  // Update message based on elapsed time
  useEffect(() => {
    if (!isConnecting) {
      setCurrentMessage("");
      return;
    }

    // Find the most recent message based on elapsed time
    const applicableMessages = progressMessages.filter(
      (msg) => elapsedTime >= msg.time
    );
    const latestMessage = applicableMessages[applicableMessages.length - 1];

    if (latestMessage) {
      setCurrentMessage(latestMessage.message);
    }
  }, [elapsedTime, isConnecting]);

  // Don't render if not connecting
  if (!isConnecting) {
    return null;
  }

  const seconds = Math.floor(elapsedTime / 1000);

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center space-x-3">
        {/* Animated spinner */}
        <div className="flex-shrink-0">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>

        <div className="flex-1">
          <p className="text-blue-800 font-medium">{currentMessage}</p>
          <div className="flex items-center justify-between mt-2">
            <p className="text-blue-600 text-sm">Elapsed time: {seconds}s</p>
            {seconds > 10 && (
              <p className="text-blue-500 text-xs">
                Render.com cold starts can take 20-30 seconds
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-3">
        <div className="bg-blue-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-1000 ease-out"
            style={{
              width: `${Math.min((elapsedTime / 30000) * 100, 95)}%`,
            }}
          ></div>
        </div>
        <div className="flex justify-between text-xs text-blue-500 mt-1">
          <span>0s</span>
          <span>~30s</span>
        </div>
      </div>

      {/* Render.com explanation */}
      {seconds > 15 && (
        <div className="mt-3 p-2 bg-blue-100 rounded text-xs text-blue-700">
          <strong>Why the wait?</strong> The voice agent is hosted on
          Render.com's free tier, which puts services to sleep after inactivity.
          The first connection triggers a "cold start" that takes 20-30 seconds
          to fully initialize.
        </div>
      )}
    </div>
  );
}

export default ConnectionProgress;
