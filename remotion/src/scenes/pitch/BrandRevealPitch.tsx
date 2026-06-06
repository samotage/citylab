import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../../brand';
import {Wordmark} from '../../components/Wordmark';
import {GridPattern} from '../../components/GridPattern';

export const BrandRevealPitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const markScale = interpolate(frame, [0, fps], [0.6, 1], {
    extrapolateRight: 'clamp',
  });
  const markOpacity = interpolate(frame, [0, 0.6 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const wordmarkOpacity = interpolate(frame, [0.8 * fps, 1.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const taglineOpacity = interpolate(frame, [1.8 * fps, 2.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const taglineY = interpolate(frame, [1.8 * fps, 2.5 * fps], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.04} />
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
        <div
          style={{
            opacity: markOpacity,
            transform: `scale(${markScale})`,
            marginBottom: 30,
          }}
        >
          <Img
            src={staticFile('citether-mark.png')}
            style={{width: 140, height: 140}}
          />
        </div>
        <div style={{opacity: wordmarkOpacity, marginBottom: 40}}>
          <Wordmark size={72} onDark />
        </div>
        <div
          style={{
            opacity: taglineOpacity,
            transform: `translateY(${taglineY}px)`,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 300,
            fontSize: 38,
            color: BRAND.warmGrey,
            letterSpacing: '0.02em',
          }}
        >
          Your energy follows you.
        </div>
      </div>
    </AbsoluteFill>
  );
};
