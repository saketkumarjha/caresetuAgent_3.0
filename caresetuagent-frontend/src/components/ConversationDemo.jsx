// import { useState } from "react";

function ConversationDemo({ onAddSampleData }) {
  const addSampleConversation = () => {
    const sampleMessages = [
      {
        type: "agent",
        text: "Hello! I'm your CareSetu healthcare assistant. How can I help you today?",
        timestamp: "12:00:01 PM",
        isText: true,
      },
      {
        type: "user",
        text: "I'd like to book an appointment",
        timestamp: "12:00:15 PM",
        isText: false,
      },
      {
        type: "agent",
        text: "I'd be happy to help you book an appointment! What type of appointment would you like to schedule?",
        timestamp: "12:00:18 PM",
        isText: true,
      },
      {
        type: "user",
        text: "A general consultation",
        timestamp: "12:00:25 PM",
        isText: false,
      },
      {
        type: "agent",
        text: "Great! For a general consultation, I'll need your email address to send you the appointment confirmation. Could you please provide your email?",
        timestamp: "12:00:28 PM",
        isText: true,
      },
      {
        type: "user",
        text: "john.doe@example.com",
        timestamp: "12:00:35 PM",
        isText: true,
      },
      {
        type: "agent",
        text: "Perfect! I have your email as john.doe@example.com. What date would work best for you?",
        timestamp: "12:00:38 PM",
        isText: true,
      },
    ];

    onAddSampleData(sampleMessages);
  };

  return (
    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium text-blue-900">Demo Mode</h3>
          <p className="text-sm text-blue-700">
            See how the conversation interface works
          </p>
        </div>
        <button
          onClick={addSampleConversation}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Load Sample Conversation
        </button>
      </div>
    </div>
  );
}

export default ConversationDemo;
