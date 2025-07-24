import { useEffect, useRef } from "react";

function Transcript({ transcript }) {
  const transcriptRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom when new messages are added
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcript]);

  return (
    <div
      ref={transcriptRef}
      className="bg-gray-50 rounded-lg p-4 h-48 mb-4 overflow-y-auto"
    >
      {transcript.length === 0 ? (
        <span className="text-gray-500">
          Conversation transcript will appear here...
        </span>
      ) : (
        <div className="space-y-2">
          {transcript.map((message, index) => (
            <div
              key={index}
              className={`p-2 rounded ${
                message.type === "user"
                  ? "bg-blue-100 text-blue-900 ml-4"
                  : "bg-green-100 text-green-900 mr-4"
              }`}
            >
              <div className="text-xs text-gray-600 mb-1">
                {message.type === "user" ? "You" : "Assistant"} -{" "}
                {message.timestamp}
              </div>
              <div>{message.text}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Transcript;
