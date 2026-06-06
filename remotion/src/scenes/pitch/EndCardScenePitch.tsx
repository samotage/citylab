import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../../brand';
import {Wordmark} from '../../components/Wordmark';
import {GridPattern} from '../../components/GridPattern';

export const EndCardScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const markOpacity = interpolate(frame, [0, 0.5 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const wordmarkOpacity = interpolate(frame, [0.6 * fps, 1.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const taglineOpacity = interpolate(frame, [1.5 * fps, 2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const hackathonOpacity = interpolate(frame, [3 * fps, 3.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.03} />
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1,
        }}
      >
        <div style={{opacity: markOpacity, marginBottom: 24}}>
          <Img
            src={staticFile('citether-mark.png')}
            style={{width: 100, height: 100}}
          />
        </div>
        <div style={{opacity: wordmarkOpacity, marginBottom: 30}}>
          <Wordmark size={56} onDark />
        </div>
        <div
          style={{
            opacity: taglineOpacity,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 300,
            fontSize: 28,
            color: BRAND.warmGrey,
          }}
        >
          Your energy follows you.
        </div>
        <div
          style={{
            position: 'absolute',
            bottom: 60,
            opacity: hackathonOpacity,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 16,
            color: BRAND.charcoalLight,
            letterSpacing: '0.08em',
          }}
        >
          WATT THE HACK 2026
        </div>
      </div>
    </AbsoluteFill>
  );
};
