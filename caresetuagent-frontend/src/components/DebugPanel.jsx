import React, { useState } from "react";
import { useToken } from "../hooks/useToken";

const DebugPanel = () => {
  const { generateToken, token, error, isLoading } = useToken();
  const [debugInfo, setDebugInfo] = useState("");

  const testTokenGeneration = async () => {
    try {
      setDebugInfo("Generating token...");
      const newToken = await generateToken(
        "test-room",
        "test-user",
        "Test User"
      );
      setDebugInfo(
        `Token generated successfully: ${newToken.substring(0, 50)}...`
      );
    } catch (err) {
      setDebugInfo(`Token generation failed: ${err.message}`);
      console.error("Token generation error:", err);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-300 rounded-lg p-4 shadow-lg max-w-md">
      <h3 className="font-bold mb-2">Debug Panel</h3>

      <div className="mb-2">
        <strong>Environment Variables:</strong>
        <div className="text-sm">
          <div>
            VITE_LIVEKIT_URL:{" "}
            {import.meta.env.VITE_LIVEKIT_URL ? "✅ Set" : "❌ Missing"}
          </div>
          <div>
            VITE_LIVEKIT_API_KEY:{" "}
            {import.meta.env.VITE_LIVEKIT_API_KEY ? "✅ Set" : "❌ Missing"}
          </div>
          <div>
            VITE_LIVEKIT_API_SECRET:{" "}
            {import.meta.env.VITE_LIVEKIT_API_SECRET ? "✅ Set" : "❌ Missing"}
          </div>
        </div>
      </div>

      <div className="mb-2">
        <strong>Token Status:</strong>
        <div className="text-sm">
          <div>Has Token: {token ? "✅ Yes" : "❌ No"}</div>
          <div>Is Loading: {isLoading ? "⏳ Yes" : "✅ No"}</div>
          <div>Error: {error || "None"}</div>
        </div>
      </div>

      <button
        onClick={testTokenGeneration}
        className="bg-blue-500 text-white px-3 py-1 rounded text-sm mb-2"
        disabled={isLoading}
      >
        Test Token Generation
      </button>

      {debugInfo && (
        <div className="text-xs bg-gray-100 p-2 rounded">{debugInfo}</div>
      )}
    </div>
  );
};

export default DebugPanel;
