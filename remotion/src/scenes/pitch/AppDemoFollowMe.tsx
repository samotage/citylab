import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

export const AppDemoFollowMe: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phone slides in from right
  const phoneX = interpolate(frame, [0, 1 * fps], [200, 0], {
    extrapolateRight: 'clamp',
  });
  const phoneOpacity = interpolate(frame, [0, 0.8 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Zoom into the app — start showing full phone, then pan/zoom to the map
  const appScale = interpolate(frame, [3 * fps, 7 * fps], [1, 1.3], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const appY = interpolate(frame, [3 * fps, 7 * fps], [0, 50], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Text callouts (left side)
  const eyebrowOpacity = interpolate(frame, [0.5 * fps, 1 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const callout1 = interpolate(frame, [2 * fps, 2.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const callout2 = interpolate(frame, [5 * fps, 5.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const callout3 = interpolate(frame, [8 * fps, 8.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const callout4 = interpolate(frame, [10 * fps, 10.5 * fps], [0, 1], {
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
            color: BRAND.amber,
            marginBottom: 16,
          }}
        >
          LIVE APP DEMO
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
          Follow Me Power
          <br />
          <span style={{color: BRAND.amber}}>in action.</span>
        </div>

        {/* Callout cards */}
        {[
          {opacity: callout1, icon: '📍', text: 'Real-time price map — $35 to $80/hr across Melbourne', color: BRAND.amber},
          {opacity: callout2, icon: '⚡', text: 'Live transfer: Your Home → Job Site, saving $0.35/kWh vs diesel', color: BRAND.teal},
          {opacity: callout3, icon: '💰', text: 'Currently earning $80/hr at Springvale — $140 earned this session', color: BRAND.amber},
          {opacity: callout4, icon: '🔧', text: 'Six scenarios: job site, parent\'s flat, EV road trip, uni, holiday, business', color: BRAND.teal},
        ].map((item, i) => (
          <div
            key={i}
            style={{
              opacity: item.opacity,
              transform: `translateX(${interpolate(item.opacity, [0, 1], [20, 0])}px)`,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              marginBottom: 24,
              padding: '16px 20px',
              backgroundColor: `${BRAND.charcoalLight}80`,
              borderRadius: 8,
              borderLeft: `3px solid ${item.color}`,
            }}
          >
            <span style={{fontSize: 24}}>{item.icon}</span>
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

      {/* Right: phone mockup with app screenshot */}
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
        {/* Phone frame */}
        <div
          style={{
            width: 380,
            height: 780,
            borderRadius: 40,
            border: `3px solid ${BRAND.charcoalLight}`,
            overflow: 'hidden',
            backgroundColor: '#1a1a1a',
            boxShadow: `0 20px 60px rgba(0,0,0,0.5), 0 0 40px ${BRAND.amber}10`,
            position: 'relative',
          }}
        >
          {/* Notch */}
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
          {/* App screenshot */}
          <div
            style={{
              width: '100%',
              height: '100%',
              overflow: 'hidden',
            }}
          >
            <Img
              src={staticFile('app-follow-me.png')}
              style={{
                width: '100%',
                height: 'auto',
                transform: `scale(${appScale}) translateY(-${appY}px)`,
                transformOrigin: 'top center',
              }}
            />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
