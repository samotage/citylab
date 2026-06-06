import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../brand';
import {Wordmark} from '../components/Wordmark';
import {GridPattern} from '../components/GridPattern';

export const CtaScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

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
          padding: 80,
          zIndex: 1,
        }}
      >
        <div
          style={{
            opacity: interpolate(frame, [0, 0.6 * fps], [0, 1], {
              extrapolateRight: 'clamp',
            }),
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 56,
            color: BRAND.white,
            textAlign: 'center',
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: 30,
          }}
        >
          Borrow a cup of power from your neighbour.
        </div>

        <div
          style={{
            opacity: interpolate(frame, [0.8 * fps, 1.3 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            fontFamily: 'Inter, sans-serif',
            fontSize: 24,
            color: BRAND.warmGrey,
            textAlign: 'center',
            lineHeight: 1.6,
            marginBottom: 60,
            maxWidth: 800,
          }}
        >
          In the old days, you'd reach over the fence for a cup of sugar.
          citEther makes energy just as simple.
        </div>

        {/* CTA button */}
        <div
          style={{
            opacity: interpolate(frame, [2 * fps, 2.5 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            transform: `translateY(${interpolate(
              frame,
              [2 * fps, 2.5 * fps],
              [15, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            )}px)`,
            backgroundColor: BRAND.amber,
            padding: '24px 60px',
            borderRadius: 6,
            marginBottom: 20,
          }}
        >
          <span
            style={{
              fontFamily: 'Inter, sans-serif',
              fontWeight: 600,
              fontSize: 26,
              color: BRAND.charcoal,
            }}
          >
            Get early access
          </span>
        </div>

        <div
          style={{
            opacity: interpolate(frame, [3 * fps, 3.5 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 18,
            color: BRAND.warmGrey,
            marginBottom: 100,
          }}
        >
          No lock-in · No contracts · Just value
        </div>

        {/* Mark + wordmark */}
        <div
          style={{
            opacity: interpolate(frame, [4 * fps, 4.5 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
          }}
        >
          <Img
            src={staticFile('citether-mark.png')}
            style={{width: 80, height: 80}}
          />
          <Wordmark size={40} onDark />
        </div>

        {/* Hackathon badge */}
        <div
          style={{
            position: 'absolute',
            bottom: 80,
            opacity: interpolate(frame, [5 * fps, 5.5 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
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
