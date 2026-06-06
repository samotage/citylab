import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

export const AppDemoPod: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phone on right
  const phoneX = interpolate(frame, [0, 1 * fps], [200, 0], {
    extrapolateRight: 'clamp',
  });
  const phoneOpacity = interpolate(frame, [0, 0.8 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const eyebrowOpacity = interpolate(frame, [0.5 * fps, 1 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const callout1 = interpolate(frame, [2 * fps, 2.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const callout2 = interpolate(frame, [4.5 * fps, 5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const callout3 = interpolate(frame, [7 * fps, 7.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const callout4 = interpolate(frame, [9 * fps, 9.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.02} />

      {/* Left: callouts */}
      <div
        style={{
          position: 'absolute',
          top: 100,
          left: 120,
          width: 700,
          zIndex: 2,
        }}
      >
        <div
          style={{
            opacity: eyebrowOpacity,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 16,
            fontWeight: 500,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color: BRAND.teal,
            marginBottom: 16,
          }}
        >
          COMMUNITY PODS
        </div>
        <div
          style={{
            opacity: eyebrowOpacity,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 44,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: 50,
          }}
        >
          Your street as a
          <br />
          <span style={{color: BRAND.teal}}>local energy co-op.</span>
        </div>

        {[
          {opacity: callout1, text: 'Maple Ave Pod — 14 households, 62 kW solar, self-supplied 73% today', color: BRAND.amber},
          {opacity: callout2, text: 'Leaderboard with social norming — you\'re #3, earning $52 vs Pod average $38', color: BRAND.teal},
          {opacity: callout3, text: 'Live Pod energy flow — House 3\'s solar charges your battery, you supply House 7', color: BRAND.amber},
          {opacity: callout4, text: 'Community battery share: 5 kWh earning $12.40/month, no hardware needed', color: BRAND.teal},
        ].map((item, i) => (
          <div
            key={i}
            style={{
              opacity: item.opacity,
              transform: `translateX(${interpolate(item.opacity, [0, 1], [20, 0])}px)`,
              display: 'flex',
              alignItems: 'flex-start',
              gap: 16,
              marginBottom: 24,
              padding: '16px 20px',
              backgroundColor: `${BRAND.charcoalLight}80`,
              borderRadius: 8,
              borderLeft: `3px solid ${item.color}`,
            }}
          >
            <span
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 20,
                color: BRAND.white,
                lineHeight: 1.4,
              }}
            >
              {item.text}
            </span>
          </div>
        ))}
      </div>

      {/* Right: phone */}
      <div
        style={{
          position: 'absolute',
          right: 80,
          top: '50%',
          transform: `translateY(-50%) translateX(${phoneX}px)`,
          opacity: phoneOpacity,
          zIndex: 1,
        }}
      >
        <div
          style={{
            width: 380,
            height: 780,
            borderRadius: 40,
            border: `3px solid ${BRAND.charcoalLight}`,
            overflow: 'hidden',
            backgroundColor: '#1a1a1a',
            boxShadow: `0 20px 60px rgba(0,0,0,0.5), 0 0 40px ${BRAND.teal}10`,
            position: 'relative',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 140,
              height: 28,
              backgroundColor: '#1a1a1a',
              borderBottomLeftRadius: 16,
              borderBottomRightRadius: 16,
              zIndex: 3,
            }}
          />
          <div style={{width: '100%', height: '100%', overflow: 'hidden'}}>
            <Img
              src={staticFile('app-my-pod.png')}
              style={{width: '100%', height: 'auto'}}
            />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
