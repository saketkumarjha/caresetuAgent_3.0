# Design Document

## Overview

This design outlines a modern web frontend application that provides instant connection capabilities with the CareSetu Voice Agent backend deployed on Render.com. The frontend will be built using vanilla JavaScript with LiveKit WebRTC for real-time voice communication, featuring comprehensive error reporting and status monitoring.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Web Browser   │    │   LiveKit Cloud  │    │   Render.com        │
│                 │    │                  │    │                     │
│  ┌───────────┐  │    │  ┌─────────────┐ │    │  ┌───────────────┐  │
│  │ Frontend  │◄─┼────┼─►│ WebRTC      │◄┼────┼─►│ Voice Agent   │  │
│  │ App       │  │    │  │ Gateway     │ │    │  │ (LiveKit      │  │
│  └───────────┘  │    │  └─────────────┘ │    │  │  Agents)      │  │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

### Technology Stack

**Frontend Framework:** Vanilla JavaScript (ES6+)

- **Rationale:** Minimal complexity, fast loading, no build process required
- **Alternative considered:** React/Vue.js (rejected due to complexity requirement)

**WebRTC Library:** LiveKit Client SDK

- **Rationale:** Already integrated with backend, proven reliability
- **Version:** Latest stable from CDN

**Styling:** CSS3 with CSS Grid/Flexbox

- **Rationale:** Modern, responsive, no external dependencies

**Build Process:** None (direct HTML/CSS/JS)

- **Rationale:** Simplicity, instant deployment capability

## Components and Interfaces

### Core Components

#### 1. Connection Manager

```javascript
class ConnectionManager {
  constructor(livekitUrl, tokenGenerator) {
    this.livekitUrl = livekitUrl;
    this.tokenGenerator = tokenGenerator;
    this.room = null;
    this.connectionState = "disconnected";
    this.latencyMonitor = new LatencyMonitor();
  }

  async connect() {
    // Establish LiveKit connection
    // Monitor connection health
    // Handle reconnection logic
  }

  disconnect() {
    // Clean disconnect
    // Clear resources
  }
}
```

#### 2. Error Handler

```javascript
class ErrorHandler {
  constructor(statusDisplay) {
    this.statusDisplay = statusDisplay;
    this.errorMappings = {
      CONNECTION_TIMEOUT: "Backend server unavailable",
      TOKEN_EXPIRED: "Token expired - refresh needed",
      HIGH_LATENCY: "High latency - slow response",
      NETWORK_ERROR: "Network error",
      LLM_OVERLOAD: "AI service overloaded",
      CONNECTION_LOST: "Connection lost",
    };
  }

  handleError(errorType, details) {
    // Display user-friendly error message
    // Log technical details for debugging
    // Trigger appropriate recovery actions
  }
}
```

#### 3. Audio Manager

```javascript
class AudioManager {
  constructor() {
    this.localTrack = null;
    this.remoteTrack = null;
    this.isRecording = false;
    this.visualizer = new AudioVisualizer();
  }

  async startRecording() {
    // Request microphone permissions
    // Create local audio track
    // Start audio visualization
  }

  stopRecording() {
    // Stop recording
    // Send audio to backend
  }

  playResponse(audioTrack) {
    // Play agent response
    // Show speaking indicator
  }
}
```

#### 4. Status Monitor

```javascript
class StatusMonitor {
  constructor() {
    this.connectionStatus = "disconnected";
    this.latency = 0;
    this.lastHeartbeat = null;
  }

  updateStatus(status) {
    // Update connection status
    // Trigger UI updates
    // Check for error conditions
  }

  monitorLatency() {
    // Measure round-trip time
    // Detect high latency conditions
    // Trigger warnings
  }
}
```

### User Interface Components

#### Main Interface Layout

```html
<div class="app-container">
  <header class="app-header">
    <h1>CareSetu Voice Assistant</h1>
    <div class="status-indicator" id="connectionStatus">Disconnected</div>
  </header>

  <main class="voice-interface">
    <div class="audio-visualizer" id="audioVisualizer"></div>
    <div class="controls">
      <button id="connectButton" class="primary-button">Connect</button>
      <button id="micButton" class="mic-button" disabled>🎤</button>
    </div>
    <div class="transcript" id="transcript"></div>
  </main>

  <div class="error-display" id="errorDisplay"></div>
</div>
```

## Data Models

### Connection State Model

```javascript
const ConnectionState = {
  DISCONNECTED: "disconnected",
  CONNECTING: "connecting",
  CONNECTED: "connected",
  RECONNECTING: "reconnecting",
  ERROR: "error",
};
```

### Error Types Model

```javascript
const ErrorTypes = {
  CONNECTION_TIMEOUT: "CONNECTION_TIMEOUT",
  TOKEN_EXPIRED: "TOKEN_EXPIRED",
  HIGH_LATENCY: "HIGH_LATENCY",
  NETWORK_ERROR: "NETWORK_ERROR",
  LLM_OVERLOAD: "LLM_OVERLOAD",
  CONNECTION_LOST: "CONNECTION_LOST",
  MICROPHONE_DENIED: "MICROPHONE_DENIED",
};
```

### Configuration Model

```javascript
const AppConfig = {
  livekit: {
    url: "wss://your-project.livekit.cloud",
    tokenEndpoint: "/api/token", // If using server-side token generation
    reconnectAttempts: 3,
    reconnectDelay: 2000,
  },
  audio: {
    sampleRate: 16000,
    channels: 1,
    bitrate: 64000,
  },
  monitoring: {
    latencyThreshold: 1000, // 1 second
    heartbeatInterval: 5000, // 5 seconds
  },
};
```

## Error Handling

### Error Detection Strategy

#### 1. Connection Errors

- **Detection:** Monitor LiveKit connection events
- **Triggers:** Connection timeout, network failures, server unavailable
- **Response:** Display specific error message, attempt reconnection

#### 2. Latency Monitoring

- **Detection:** Measure time between audio send and response
- **Threshold:** 1 second (as per requirements)
- **Response:** Display "High latency - slow response" warning

#### 3. Token Expiration

- **Detection:** Monitor JWT token expiration time
- **Triggers:** Token expires or authentication fails
- **Response:** Display "Token expired - refresh needed", redirect to token refresh

#### 4. Service Overload

- **Detection:** Monitor response patterns and error codes
- **Triggers:** Repeated timeouts, specific error responses
- **Response:** Display "AI service overloaded", implement backoff

### Error Recovery Mechanisms

```javascript
class ErrorRecovery {
  async handleConnectionLost() {
    // Wait 2 seconds
    // Attempt reconnection
    // If fails, show manual reconnect option
  }

  async handleTokenExpired() {
    // Clear current session
    // Request new token
    // Attempt reconnection
  }

  async handleHighLatency() {
    // Show warning but continue
    // Monitor for improvement
    // Suggest network check if persistent
  }
}
```

## Testing Strategy

### Unit Testing

- **Connection Manager:** Test connection establishment, error handling
- **Audio Manager:** Test recording, playback, permissions
- **Error Handler:** Test error detection and message display

### Integration Testing

- **LiveKit Integration:** Test with actual LiveKit server
- **End-to-End:** Test complete user workflow
- **Error Scenarios:** Test each error condition

### Browser Compatibility Testing

- **Chrome:** Primary target (latest 2 versions)
- **Firefox:** Secondary target (latest 2 versions)
- **Safari:** Mobile compatibility (latest 2 versions)
- **Edge:** Windows compatibility (latest 2 versions)

### Performance Testing

- **Connection Speed:** Measure time to establish connection
- **Audio Latency:** Measure end-to-end audio delay
- **Memory Usage:** Monitor for memory leaks during long sessions

## Deployment Architecture

### File Structure

```
frontend/
├── index.html          # Main application page
├── css/
│   ├── main.css       # Main styles
│   └── responsive.css # Mobile responsiveness
├── js/
│   ├── app.js         # Main application logic
│   ├── connection.js  # Connection management
│   ├── audio.js       # Audio handling
│   ├── errors.js      # Error handling
│   └── config.js      # Configuration
└── assets/
    ├── icons/         # UI icons
    └── sounds/        # UI sound effects
```

### Hosting Options

1. **Static Hosting:** Netlify, Vercel, GitHub Pages
2. **CDN Distribution:** CloudFlare, AWS CloudFront
3. **Simple HTTP Server:** For development and testing

### Configuration Management

```javascript
// config.js
const Config = {
  development: {
    livekit: {
      url: "ws://localhost:7880",
      logLevel: "debug",
    },
  },
  production: {
    livekit: {
      url: "wss://your-project.livekit.cloud",
      logLevel: "warn",
    },
  },
};
```

## Security Considerations

### Token Management

- **Client-Side:** Store tokens in memory only (no localStorage)
- **Expiration:** Implement automatic token refresh
- **Validation:** Validate token before each connection attempt

### Audio Privacy

- **Permissions:** Request microphone access only when needed
- **Data:** No local audio storage, stream-only processing
- **Encryption:** All audio transmitted via encrypted WebRTC

### Error Information

- **User Messages:** Show user-friendly messages only
- **Debug Info:** Log technical details to console (development only)
- **Sensitive Data:** Never expose API keys or internal URLs

## Performance Optimization

### Connection Optimization

- **Preconnection:** Establish WebRTC connection on page load
- **Keep-Alive:** Maintain connection with periodic heartbeats
- **Reconnection:** Implement exponential backoff for reconnection attempts

### Audio Optimization

- **Compression:** Use appropriate audio codecs for bandwidth
- **Buffering:** Implement audio buffering for smooth playback
- **Quality Adaptation:** Adjust quality based on network conditions

### UI Optimization

- **Lazy Loading:** Load components as needed
- **Debouncing:** Debounce user interactions to prevent spam
- **Efficient Rendering:** Minimize DOM updates during audio visualization

## Monitoring and Analytics

### Connection Metrics

- Connection establishment time
- Connection success/failure rates
- Reconnection frequency
- Average session duration

### Error Tracking

- Error frequency by type
- Error resolution success rates
- User abandonment after errors

### Performance Metrics

- Audio latency measurements
- Page load times
- Memory usage patterns
- Browser compatibility issues

This design provides a solid foundation for building a simple yet robust web frontend that meets all the specified requirements while maintaining optimal performance and user experience.
