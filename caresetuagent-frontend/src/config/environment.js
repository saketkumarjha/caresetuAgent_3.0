// Environment configuration for different deployment environments

const config = {
  development: {
    app: {
      name: import.meta.env.VITE_APP_NAME || "CareSetu Voice Assistant (Dev)",
      version: import.meta.env.VITE_APP_VERSION || "1.0.0",
      environment: "development",
    },
    livekit: {
      url: import.meta.env.VITE_LIVEKIT_URL,
      apiKey: import.meta.env.VITE_LIVEKIT_API_KEY,
      apiSecret: import.meta.env.VITE_LIVEKIT_API_SECRET,
      tokenEndpoint:
        import.meta.env.VITE_TOKEN_ENDPOINT ||
        "http://localhost:8000/api/token",
    },
    features: {
      debugMode: import.meta.env.VITE_DEBUG_MODE === "true",
      devTools: import.meta.env.VITE_ENABLE_DEVTOOLS === "true",
      analytics: false,
    },
    logging: {
      level: import.meta.env.VITE_LOG_LEVEL || "debug",
      enableConsole: true,
    },
  },

  staging: {
    app: {
      name:
        import.meta.env.VITE_APP_NAME || "CareSetu Voice Assistant (Staging)",
      version: import.meta.env.VITE_APP_VERSION || "1.0.0",
      environment: "staging",
    },
    livekit: {
      url: import.meta.env.VITE_LIVEKIT_URL,
      apiKey: import.meta.env.VITE_LIVEKIT_API_KEY,
      apiSecret: import.meta.env.VITE_LIVEKIT_API_SECRET,
      tokenEndpoint:
        import.meta.env.VITE_TOKEN_ENDPOINT ||
        "https://caresetuagent-staging.onrender.com/api/token",
    },
    features: {
      debugMode: import.meta.env.VITE_DEBUG_MODE === "true",
      devTools: import.meta.env.VITE_ENABLE_DEVTOOLS === "true",
      analytics: false,
    },
    logging: {
      level: import.meta.env.VITE_LOG_LEVEL || "info",
      enableConsole: true,
    },
  },

  production: {
    app: {
      name: import.meta.env.VITE_APP_NAME || "CareSetu Voice Assistant",
      version: import.meta.env.VITE_APP_VERSION || "1.0.0",
      environment: "production",
    },
    livekit: {
      url: import.meta.env.VITE_LIVEKIT_URL,
      apiKey: import.meta.env.VITE_LIVEKIT_API_KEY,
      apiSecret: import.meta.env.VITE_LIVEKIT_API_SECRET,
      tokenEndpoint:
        import.meta.env.VITE_TOKEN_ENDPOINT ||
        "https://caresetuagent-3-0-2.onrender.com/api/token",
    },
    features: {
      debugMode: false,
      devTools: false,
      analytics: import.meta.env.VITE_ENABLE_ANALYTICS === "true",
    },
    logging: {
      level: import.meta.env.VITE_LOG_LEVEL || "warn",
      enableConsole: false,
    },
  },
};

// Get current environment from Vite mode or environment variable
const currentEnv =
  import.meta.env.VITE_APP_ENV || import.meta.env.MODE || "development";

// Export the configuration for the current environment
export const appConfig = config[currentEnv] || config.development;

// Export individual configurations for testing
export { config };

// Utility function to check if we're in development
export const isDevelopment = () => currentEnv === "development";

// Utility function to check if we're in production
export const isProduction = () => currentEnv === "production";

// Utility function to check if we're in staging
export const isStaging = () => currentEnv === "staging";

// Validate required environment variables
const validateConfig = () => {
  const required = ["url", "apiKey", "apiSecret"];
  const missing = required.filter((key) => !appConfig.livekit[key]);

  if (missing.length > 0) {
    console.error("Missing required LiveKit configuration:", missing);
    throw new Error(
      `Missing required environment variables: ${missing
        .map((key) => `VITE_LIVEKIT_${key.toUpperCase()}`)
        .join(", ")}`
    );
  }
};

// Validate configuration on import (only in development)
if (isDevelopment()) {
  try {
    validateConfig();
  } catch (error) {
    console.warn("Configuration validation failed:", error.message);
  }
}
