import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../../brand';
import {Wordmark} from '../../components/Wordmark';
import {GridPattern} from '../../components/GridPattern';

export const CtaScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phase 1: The ask — staggered reveal (0-10s)
  const pilot = interpolate(frame, [1 * fps, 1.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const suburb = interpolate(frame, [3 * fps, 3.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const households = interpolate(frame, [5 * fps, 5.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const months = interpolate(frame, [7 * fps, 7.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 2: Supporting line (10-14s)
  const supportLine = interpolate(frame, [10 * fps, 11 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 3: "That's the ask." amber bar (14-17s)
  const askBar = interpolate(frame, [14 * fps, 14.8 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const askBarY = interpolate(askBar, [0, 1], [16, 0]);

  // Phase 4: Crossfade to end card (18-30s)
  const ctaFadeOut = interpolate(frame, [18 * fps, 19.5 * fps], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const markOpacity = interpolate(frame, [20 * fps, 21 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const markScale = interpolate(frame, [20 * fps, 21.5 * fps], [0.8, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const wordmarkOpacity = interpolate(frame, [21.5 * fps, 22.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const tagline = interpolate(frame, [23 * fps, 24 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const taglineY = interpolate(frame, [23 * fps, 24 * fps], [16, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const hackathon = interpolate(frame, [26 * fps, 27 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.03} />

      {/* CTA content — fades out for end card */}
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
          opacity: ctaFadeOut,
          zIndex: 1,
        }}
      >
        {/* Staggered ask */}
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 76,
            color: BRAND.white,
            textAlign: 'center',
            letterSpacing: '-0.02em',
            lineHeight: 1.3,
            marginBottom: 40,
          }}
        >
          <span style={{opacity: pilot}}>One pilot.</span>
          {'  '}
          <span style={{opacity: suburb}}>One suburb.</span>
          <br />
          <span style={{opacity: households, color: BRAND.amber}}>
            100 households.
          </span>
          {'  '}
          <span style={{opacity: months}}>Three months.</span>
        </div>

        {/* Supporting line */}
        <div
          style={{
            opacity: supportLine,
            fontFamily: 'Inter, sans-serif',
            fontSize: 28,
            color: BRAND.warmGrey,
            textAlign: 'center',
            lineHeight: 1.6,
            maxWidth: 900,
            marginBottom: 40,
          }}
        >
          We prove the model works — behind the meter, across the network,
          <br />
          with real people earning real value in real places.
        </div>

        {/* "That's the ask" amber bar */}
        <div
          style={{
            opacity: askBar,
            transform: `translateY(${askBarY}px)`,
            backgroundColor: BRAND.amber,
            padding: '18px 48px',
            borderRadius: 6,
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
            That's the ask.
          </span>
        </div>
      </div>

      {/* End card — brand reveal callback */}
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
          zIndex: 2,
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            opacity: markOpacity,
            transform: `scale(${markScale})`,
            marginBottom: 24,
          }}
        >
          <Img
            src={staticFile('citether-mark.png')}
            style={{width: 100, height: 100, borderRadius: 22}}
          />
        </div>
        <div style={{opacity: wordmarkOpacity, marginBottom: 30}}>
          <Wordmark size={64} onDark />
        </div>
        <div
          style={{
            opacity: tagline,
            transform: `translateY(${taglineY}px)`,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 300,
            fontSize: 34,
            color: BRAND.warmGrey,
          }}
        >
          Your energy follows you.
        </div>
        <div
          style={{
            position: 'absolute',
            bottom: 60,
            opacity: hackathon,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 20,
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
