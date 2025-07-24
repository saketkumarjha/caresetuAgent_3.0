import { useState, useRef, useCallback, useEffect } from "react";
import { createLocalAudioTrack } from "livekit-client";

export function useAudio() {
  const [isRecording, setIsRecording] = useState(false);
  const [hasPermission, setHasPermission] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const localTrackRef = useRef(null);
  const remoteTrackRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Request microphone permission
  const requestPermission = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setHasPermission(true);
      // Stop the test stream
      stream.getTracks().forEach((track) => track.stop());
      return true;
    } catch (error) {
      console.error("Microphone permission denied:", error);
      setHasPermission(false);
      return false;
    }
  }, []);

  // Create local audio track for LiveKit
  const createAudioTrack = useCallback(async () => {
    try {
      if (localTrackRef.current) {
        localTrackRef.current.stop();
        localTrackRef.current = null;
      }

      console.log("🎤 Creating LiveKit audio track...");

      // Try LiveKit's createLocalAudioTrack first
      try {
        const track = await createLocalAudioTrack({
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000,
          channelCount: 1,
        });

        console.log("🎤 LiveKit audio track created successfully:", {
          kind: track.kind,
          enabled: track.enabled,
          muted: track.isMuted,
          source: track.source,
        });

        localTrackRef.current = track;
        return track;
      } catch (livekitError) {
        console.warn(
          "🎤 LiveKit createLocalAudioTrack failed, trying fallback:",
          livekitError
        );

        // Fallback to basic getUserMedia + manual LiveKit track creation
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 48000,
            channelCount: 1,
          },
        });

        console.log(
          "🎤 Fallback: Got MediaStream, creating LiveKit track manually"
        );

        // Import LocalAudioTrack class for manual creation
        const { LocalAudioTrack } = await import("livekit-client");
        const audioTrack = stream.getAudioTracks()[0];
        const track = new LocalAudioTrack(audioTrack);

        console.log("🎤 Fallback track created successfully");
        localTrackRef.current = track;
        return track;
      }
    } catch (error) {
      console.error("🎤 All audio track creation methods failed:", error);
      throw new Error(`Audio track creation failed: ${error.message}`);
    }
  }, []);

  // Start audio level monitoring
  const startAudioLevelMonitoring = useCallback(
    (track) => {
      if (!track || !track.mediaStreamTrack) return;

      try {
        const audioContext = new (window.AudioContext ||
          window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(
          new MediaStream([track.mediaStreamTrack])
        );

        analyser.fftSize = 256;
        source.connect(analyser);

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        const updateAudioLevel = () => {
          if (!analyserRef.current) return;

          analyserRef.current.getByteFrequencyData(dataArray);
          const average =
            dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
          const normalizedLevel = Math.min(average / 128, 1);

          setAudioLevel(normalizedLevel);

          if (isRecording) {
            animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
          }
        };

        updateAudioLevel();
      } catch (error) {
        console.error("Failed to start audio level monitoring:", error);
      }
    },
    [isRecording]
  );

  // Stop audio level monitoring
  const stopAudioLevelMonitoring = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    setAudioLevel(0);
  }, []);

  // Start recording
  const startRecording = useCallback(async () => {
    console.log("🎤 Starting recording process...");

    try {
      // Stop any existing recording first
      if (localTrackRef.current) {
        console.log("🎤 Stopping existing recording...");
        localTrackRef.current.stop();
        localTrackRef.current = null;
      }

      // Always request permission to ensure we have access
      console.log("🎤 Requesting microphone permission...");
      const granted = await requestPermission();
      if (!granted) {
        throw new Error(
          "Microphone permission denied. Please allow microphone access and try again."
        );
      }
      console.log("🎤 Permission granted successfully");

      // Create audio track
      console.log("🎤 Creating LiveKit audio track...");
      const track = await createAudioTrack();

      if (!track) {
        throw new Error("Failed to create audio track - track is null");
      }

      if (!track.mediaStreamTrack) {
        throw new Error("Failed to create audio track - no mediaStreamTrack");
      }

      if (track.mediaStreamTrack.readyState !== "live") {
        throw new Error(
          `Audio track not ready - state: ${track.mediaStreamTrack.readyState}`
        );
      }

      console.log("🎤 Audio track created successfully:", {
        kind: track.kind,
        enabled: track.enabled,
        muted: track.isMuted,
        readyState: track.mediaStreamTrack.readyState,
      });

      // Start monitoring audio levels
      console.log("🎤 Starting audio level monitoring...");
      startAudioLevelMonitoring(track);

      setIsRecording(true);
      console.log("🎤 Recording started successfully");
      return track;
    } catch (error) {
      console.error("🎤 Recording failed with error:", error);
      setIsRecording(false);

      // Clean up on error
      if (localTrackRef.current) {
        localTrackRef.current.stop();
        localTrackRef.current = null;
      }

      // Re-throw with more context
      throw new Error(`Recording failed: ${error.message}`);
    }
  }, [requestPermission, createAudioTrack, startAudioLevelMonitoring]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (localTrackRef.current) {
      localTrackRef.current.stop();
      localTrackRef.current = null;
    }

    stopAudioLevelMonitoring();
    setIsRecording(false);
  }, [stopAudioLevelMonitoring]);

  // Play remote audio track
  const playRemoteAudio = useCallback((track) => {
    try {
      if (!track || !track.mediaStreamTrack) {
        console.error("🔊 Invalid remote audio track");
        return;
      }

      console.log("🔊 Playing remote audio track:", {
        kind: track.kind,
        enabled: track.enabled,
        readyState: track.mediaStreamTrack.readyState,
      });

      // Create audio element for playback with proper settings
      const audioElement = new Audio();
      audioElement.srcObject = new MediaStream([track.mediaStreamTrack]);
      audioElement.autoplay = true;
      audioElement.volume = 0.9; // Slightly lower volume to prevent feedback

      // Prevent echo by ensuring this is output only
      audioElement.muted = false;

      // Set audio element properties for better quality
      audioElement.preload = "auto";

      // Add audio processing to prevent echo
      if (audioElement.setSinkId) {
        // Use default audio output device
        audioElement.setSinkId("default").catch((err) => {
          console.warn("🔊 Could not set audio output device:", err);
        });
      }

      remoteTrackRef.current = track;
      setIsPlaying(true);

      // Handle playback events
      audioElement.onloadeddata = () => {
        console.log("🔊 Remote audio loaded and ready to play");
      };

      audioElement.onplay = () => {
        console.log("🔊 Remote audio started playing");
      };

      audioElement.onended = () => {
        console.log("🔊 Remote audio ended");
        setIsPlaying(false);
      };

      audioElement.onerror = (error) => {
        console.error("🔊 Audio playback error:", error);
        setIsPlaying(false);
      };

      audioElement.onpause = () => {
        console.log("🔊 Remote audio paused");
        setIsPlaying(false);
      };

      // Attach to DOM to ensure proper playback (but hidden)
      audioElement.style.display = "none";
      document.body.appendChild(audioElement);

      // Clean up when track ends
      track.on("ended", () => {
        console.log("🔊 Remote track ended, cleaning up");
        if (audioElement.parentNode) {
          audioElement.parentNode.removeChild(audioElement);
        }
        setIsPlaying(false);
      });

      return audioElement;
    } catch (error) {
      console.error("🔊 Failed to play remote audio:", error);
      setIsPlaying(false);
    }
  }, []);

  // Stop remote audio playback
  const stopRemoteAudio = useCallback(() => {
    if (remoteTrackRef.current) {
      remoteTrackRef.current = null;
    }
    setIsPlaying(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (localTrackRef.current) {
        localTrackRef.current.stop();
      }
      stopAudioLevelMonitoring();
    };
  }, [stopAudioLevelMonitoring]);

  return {
    // State
    isRecording,
    hasPermission,
    audioLevel,
    isPlaying,

    // Actions
    requestPermission,
    startRecording,
    stopRecording,
    playRemoteAudio,
    stopRemoteAudio,

    // Refs for external access
    localTrack: localTrackRef.current,
    remoteTrack: remoteTrackRef.current,
  };
}
