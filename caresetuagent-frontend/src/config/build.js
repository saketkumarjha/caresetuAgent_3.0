// Build-time configuration and optimization settings

export const buildConfig = {
  // Build information (injected at build time)
  version: __APP_VERSION__ || "1.0.0",
  buildTime: __BUILD_TIME__ || new Date().toISOString(),

  // Performance optimization settings
  performance: {
    // Lazy loading thresholds
    lazyLoadThreshold: 100,

    // Audio buffer settings
    audioBufferSize: 4096,
    audioSampleRate: 16000,

    // Connection timeouts
    connectionTimeout: 3000, // 3 seconds as per requirements
    reconnectionDelay: 2000,
    maxReconnectionAttempts: 3,

    // Latency monitoring
    latencyThreshold: 1000, // 1 second as per requirements
    latencyCheckInterval: 5000,

    // UI update intervals
    statusUpdateInterval: 1000,
    visualizerUpdateInterval: 16, // ~60fps
  },

  // Feature flags for different builds
  features: {
    // Audio visualization
    enableAudioVisualization: true,

    // Advanced error reporting
    enableDetailedErrors: true,

    // Performance monitoring
    enablePerformanceMonitoring: true,

    // Keyboard shortcuts
    enableKeyboardShortcuts: true,

    // Auto-reconnection
    enableAutoReconnection: true,
  },

  // Asset optimization
  assets: {
    // Image optimization
    imageFormats: ["webp", "avif", "png", "jpg"],
    imageSizes: [320, 640, 960, 1280, 1920],

    // Font optimization
    fontDisplay: "swap",
    fontPreload: ["Inter-Regular.woff2", "Inter-Medium.woff2"],

    // Icon optimization
    iconFormat: "svg",
    iconSizes: [16, 24, 32, 48, 64],
  },

  // Security settings
  security: {
    // Content Security Policy
    csp: {
      defaultSrc: ["'self'"],
      connectSrc: ["'self'", "wss:", "https:"],
      mediaSrc: ["'self'", "blob:"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "blob:"],
    },

    // HTTPS enforcement
    enforceHttps: true,

    // Token security
    tokenStorage: "memory", // Never use localStorage for tokens
    tokenRefreshBuffer: 300000, // 5 minutes before expiry
  },

  // Analytics and monitoring
  monitoring: {
    // Error tracking
    enableErrorTracking: true,
    errorSampleRate: 1.0,

    // Performance tracking
    enablePerformanceTracking: true,
    performanceSampleRate: 0.1,

    // User analytics
    enableUserAnalytics: false, // Disabled by default for privacy

    // Custom metrics
    customMetrics: [
      "connection_time",
      "audio_latency",
      "error_rate",
      "session_duration",
    ],
  },
};

// Environment-specific overrides
const environmentOverrides = {
  development: {
    features: {
      enableDetailedErrors: true,
      enablePerformanceMonitoring: true,
    },
    monitoring: {
      enableErrorTracking: true,
      enablePerformanceTracking: true,
      enableUserAnalytics: false,
    },
  },

  staging: {
    features: {
      enableDetailedErrors: true,
      enablePerformanceMonitoring: true,
    },
    monitoring: {
      enableErrorTracking: true,
      enablePerformanceTracking: true,
      enableUserAnalytics: false,
    },
  },

  production: {
    features: {
      enableDetailedErrors: false,
      enablePerformanceMonitoring: false,
    },
    monitoring: {
      enableErrorTracking: true,
      enablePerformanceTracking: true,
      enableUserAnalytics: true,
      errorSampleRate: 0.1,
      performanceSampleRate: 0.01,
    },
  },
};

// Apply environment-specific overrides
const currentEnv =
  import.meta.env.VITE_APP_ENV || import.meta.env.MODE || "development";
const overrides = environmentOverrides[currentEnv] || {};

// Deep merge function
const deepMerge = (target, source) => {
  const result = { ...target };

  for (const key in source) {
    if (
      source[key] &&
      typeof source[key] === "object" &&
      !Array.isArray(source[key])
    ) {
      result[key] = deepMerge(result[key] || {}, source[key]);
    } else {
      result[key] = source[key];
    }
  }

  return result;
};

// Export the final configuration
export const finalBuildConfig = deepMerge(buildConfig, overrides);

// Export utility functions
export const getBuildInfo = () => ({
  version: finalBuildConfig.version,
  buildTime: finalBuildConfig.buildTime,
  environment: currentEnv,
});

export const isFeatureEnabled = (feature) => {
  return finalBuildConfig.features[feature] || false;
};

export const getPerformanceSetting = (setting) => {
  return finalBuildConfig.performance[setting];
};
