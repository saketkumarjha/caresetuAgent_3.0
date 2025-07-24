import { useEffect, useRef } from "react";

function AudioVisualizer({
  isRecording,
  isPlaying,
  audioLevel = 0,
  audioTrack = null,
}) {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);

  // Initialize Web Audio API for real-time visualization
  useEffect(() => {
    if (
      audioTrack &&
      audioTrack.mediaStreamTrack &&
      (isRecording || isPlaying)
    ) {
      try {
        const audioContext = new (window.AudioContext ||
          window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(
          new MediaStream([audioTrack.mediaStreamTrack])
        );

        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.8;
        source.connect(analyser);

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
        dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);
      } catch (error) {
        console.error("Failed to initialize Web Audio API:", error);
      }
    }

    return () => {
      if (
        audioContextRef.current &&
        audioContextRef.current.state !== "closed"
      ) {
        audioContextRef.current.close();
      }
    };
  }, [audioTrack, isRecording, isPlaying]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const barCount = 32;
    const barWidth = width / barCount;

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      if (isRecording || isPlaying) {
        let frequencyData = null;

        // Get real audio frequency data if available
        if (analyserRef.current && dataArrayRef.current) {
          analyserRef.current.getByteFrequencyData(dataArrayRef.current);
          frequencyData = dataArrayRef.current;
        }

        // Create animated bars based on real audio data or fallback to audioLevel
        for (let i = 0; i < barCount; i++) {
          let barHeight;

          if (frequencyData && i < frequencyData.length) {
            // Use real frequency data
            barHeight = (frequencyData[i] / 255) * height * 0.8 + height * 0.1;
          } else {
            // Fallback to audioLevel with some randomization for visual appeal
            const levelVariation = audioLevel + (Math.random() - 0.5) * 0.3;
            barHeight = Math.max(
              levelVariation * height * 0.8 + height * 0.1,
              height * 0.1
            );
          }

          const x = i * barWidth;
          const y = (height - barHeight) / 2;

          // Color based on state and intensity
          let color;
          if (isRecording) {
            const intensity = barHeight / height;
            color = `hsl(${10 + intensity * 50}, 70%, ${50 + intensity * 20}%)`; // Red to orange gradient
          } else if (isPlaying) {
            const intensity = barHeight / height;
            color = `hsl(${200 + intensity * 60}, 70%, ${
              50 + intensity * 20
            }%)`; // Blue to cyan gradient
          } else {
            color = "#d1d5db"; // Gray for idle
          }

          ctx.fillStyle = color;
          ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        }
      } else {
        // Static bars for idle state
        for (let i = 0; i < barCount; i++) {
          const barHeight = height * 0.15;
          const x = i * barWidth;
          const y = (height - barHeight) / 2;

          ctx.fillStyle = "#e5e7eb";
          ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        }
      }

      if (isRecording || isPlaying) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRecording, isPlaying, audioLevel]);

  return (
    <div className="bg-gray-50 rounded-lg h-20 mb-4 flex items-center justify-center border-2 border-gray-200">
      <div className="relative w-full h-full p-2">
        <canvas
          ref={canvasRef}
          width={800}
          height={80}
          className="w-full h-full rounded"
        />

        {/* Status indicator */}
        <div className="absolute top-2 right-2 text-xs font-medium">
          {isRecording && (
            <span className="text-red-600 flex items-center gap-1">
              <span className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></span>
              Recording
            </span>
          )}
          {isPlaying && !isRecording && (
            <span className="text-blue-600 flex items-center gap-1">
              <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
              Playing
            </span>
          )}
          {!isRecording && !isPlaying && (
            <span className="text-gray-500">Ready</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default AudioVisualizer;
