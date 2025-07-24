import { useState, useEffect, useCallback, useRef } from "react";

// Token expiration buffer (refresh 5 minutes before expiry)
const TOKEN_REFRESH_BUFFER = 5 * 60 * 1000; // 5 minutes in milliseconds

export const useToken = () => {
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expiresAt, setExpiresAt] = useState(null);
  const refreshTimeoutRef = useRef(null);

  // Parse JWT token to get expiration time
  const parseTokenExpiration = useCallback((tokenString) => {
    try {
      const payload = JSON.parse(atob(tokenString.split(".")[1]));
      return payload.exp * 1000; // Convert to milliseconds
    } catch (err) {
      console.error("Error parsing token:", err);
      return null;
    }
  }, []);

  // Check if token is expired or will expire soon
  const isTokenExpired = useCallback((tokenString, expirationTime) => {
    if (!tokenString || !expirationTime) return true;

    const now = Date.now();
    const timeUntilExpiry = expirationTime - now;

    // Consider token expired if it expires within the buffer time
    return timeUntilExpiry <= TOKEN_REFRESH_BUFFER;
  }, []);

  // Schedule automatic token refresh (defined first to avoid reference errors)
  const scheduleTokenRefresh = useCallback(
    (expirationTime, roomName, identity, name) => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }

      if (!expirationTime) return;

      const now = Date.now();
      const timeUntilRefresh = expirationTime - now - TOKEN_REFRESH_BUFFER;

      if (timeUntilRefresh > 0) {
        refreshTimeoutRef.current = setTimeout(() => {
          console.log("Auto-refreshing token...");
          // Use a ref to avoid circular dependency
          generateTokenRef.current?.(roomName, identity, name).catch((err) => {
            console.error("Auto token refresh failed:", err);
            setError("Token expired - refresh needed");
          });
        }, timeUntilRefresh);
      }
    },
    []
  );

  // Create a ref to store the generateToken function to avoid circular dependency
  const generateTokenRef = useRef(null);

  // Generate token from backend
  const generateToken = useCallback(
    async (roomName = "voice_agent_room", identity = null, name = "User") => {
      console.log("🔑 Starting token generation...", {
        roomName,
        identity,
        name,
      });
      setIsLoading(true);
      setError(null);

      try {
        // Generate a unique identity if not provided
        const userIdentity =
          identity ||
          `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        console.log("🔑 Generated user identity:", userIdentity);

        // Use client-side token generation (backend is LiveKit agent only)
        console.log(
          "🔑 Generating token client-side using LiveKit credentials"
        );
        console.log("🔑 Token parameters:", { roomName, userIdentity, name });
        const clientToken = await generateClientSideToken(
          roomName,
          userIdentity,
          name
        );
        console.log("🔑 Token generation completed successfully");
        console.log(
          "🔑 Generated token preview:",
          clientToken.substring(0, 50) + "..."
        );
        return clientToken;
      } catch (err) {
        console.error("🔑 Token generation error:", err);
        setError("Token expired - refresh needed");
        setIsLoading(false);
        throw err;
      }
    },
    [parseTokenExpiration, scheduleTokenRefresh]
  );

  // Update the ref whenever generateToken changes
  useEffect(() => {
    generateTokenRef.current = generateToken;
  }, [generateToken]);

  // Client-side token generation using LiveKit credentials
  const generateClientSideToken = useCallback(
    async (roomName, identity, name) => {
      try {
        const apiKey = import.meta.env.VITE_LIVEKIT_API_KEY;
        const apiSecret = import.meta.env.VITE_LIVEKIT_API_SECRET;

        if (!apiKey || !apiSecret) {
          throw new Error("LiveKit credentials not configured");
        }

        // Create token payload
        const now = Math.floor(Date.now() / 1000);
        const exp = now + 24 * 60 * 60; // 24 hours

        const payload = {
          iss: apiKey,
          sub: identity,
          video: {
            room: roomName,
            roomJoin: true,
            canPublish: true,
            canSubscribe: true,
            canPublishData: true,
          },
          metadata: name,
        };

        // Use proper JWT signing with jose library (browser-compatible)
        const { SignJWT } = await import("jose");
        const secret = new TextEncoder().encode(apiSecret);

        const token = await new SignJWT(payload)
          .setProtectedHeader({ alg: "HS256" })
          .setIssuedAt(now)
          .setExpirationTime(exp)
          .sign(secret);

        const expiration = exp * 1000;

        setToken(token);
        setExpiresAt(expiration);
        setIsLoading(false);

        // Set up automatic refresh
        scheduleTokenRefresh(expiration, roomName, identity, name);

        console.log("Generated LiveKit token for room:", roomName);
        return token;
      } catch (error) {
        console.error("Client-side token generation failed:", error);
        throw error;
      }
    },
    []
  );

  // Refresh token manually
  const refreshToken = useCallback(
    async (roomName = "voice_agent_room", identity = null, name = "User") => {
      return generateToken(roomName, identity, name);
    },
    [generateToken]
  );

  // Clear token
  const clearToken = useCallback(() => {
    if (refreshTimeoutRef.current) {
      clearTimeout(refreshTimeoutRef.current);
      refreshTimeoutRef.current = null;
    }

    setToken(null);
    setExpiresAt(null);
    setError(null);
  }, []);

  // Check if current token is valid
  const isTokenValid = useCallback(() => {
    return token && expiresAt && !isTokenExpired(token, expiresAt);
  }, [token, expiresAt, isTokenExpired]);

  // Get time until token expires
  const getTimeUntilExpiry = useCallback(() => {
    if (!expiresAt) return 0;
    return Math.max(0, expiresAt - Date.now());
  }, [expiresAt]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }
    };
  }, []);

  // Auto-refresh token if it's about to expire
  useEffect(() => {
    if (token && expiresAt && isTokenExpired(token, expiresAt)) {
      setError("Token expired - refresh needed");
    }
  }, [token, expiresAt, isTokenExpired]);

  return {
    token,
    isLoading,
    isGenerating: isLoading, // Alias for compatibility
    error,
    expiresAt,
    generateToken,
    refreshToken,
    clearToken,
    isTokenValid,
    getTimeUntilExpiry,
    isExpired: token && expiresAt ? isTokenExpired(token, expiresAt) : false,
  };
};
