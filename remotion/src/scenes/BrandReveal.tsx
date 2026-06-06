import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../brand';
import {Wordmark} from '../components/Wordmark';
import {GridPattern} from '../components/GridPattern';

export const BrandReveal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const markScale = interpolate(frame, [0, 1 * fps], [0.7, 1], {
    extrapolateRight: 'clamp',
  });
  const markOpacity = interpolate(frame, [0, 0.8 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const wordmarkOpacity = interpolate(
    frame,
    [1.2 * fps, 2 * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const taglineOpacity = interpolate(
    frame,
    [2.5 * fps, 3.5 * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const taglineY = interpolate(
    frame,
    [2.5 * fps, 3.5 * fps],
    [20, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: BRAND.charcoal,
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <GridPattern opacity={0.06} />
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 40,
          zIndex: 1,
        }}
      >
        <Img
          src={staticFile('citether-mark.png')}
          style={{
            width: 200,
            height: 200,
            transform: `scale(${markScale})`,
            opacity: markOpacity,
          }}
        />
        <div style={{opacity: wordmarkOpacity}}>
          <Wordmark size={64} onDark />
        </div>
        <div
          style={{
            opacity: taglineOpacity,
            transform: `translateY(${taglineY}px)`,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 24,
            color: BRAND.warmGrey,
            letterSpacing: '0.05em',
          }}
        >
          Tether to the grid. Get paid.
        </div>
      </div>
    </AbsoluteFill>
  );
};
