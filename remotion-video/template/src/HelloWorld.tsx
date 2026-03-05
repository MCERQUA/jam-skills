import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export const HelloWorld: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  const titleY = spring({
    frame,
    fps,
    config: { damping: 200, stiffness: 100 },
  });

  const subtitleOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Arial, Helvetica, sans-serif",
      }}
    >
      <div
        style={{
          opacity: titleOpacity,
          transform: `translateY(${interpolate(titleY, [0, 1], [50, 0])}px)`,
          textAlign: "center",
        }}
      >
        <h1
          style={{
            color: "white",
            fontSize: 80,
            fontWeight: "bold",
            margin: 0,
            textShadow: "0 4px 30px rgba(100, 100, 255, 0.5)",
          }}
        >
          Hello World
        </h1>
        <p
          style={{
            color: "#a0a0ff",
            fontSize: 32,
            marginTop: 20,
            opacity: subtitleOpacity,
          }}
        >
          Made with Remotion
        </p>
      </div>
    </AbsoluteFill>
  );
};
