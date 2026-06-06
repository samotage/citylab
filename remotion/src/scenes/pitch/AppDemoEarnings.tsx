import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

export const AppDemoEarnings: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phone on LEFT this time (alternate sides for visual variety)
  const phoneX = interpolate(frame, [0, 1 * fps], [-200, 0], {
    extrapolateRight: 'clamp',
  });
  const phoneOpacity = interpolate(frame, [0, 0.8 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Callouts (right side)
  const eyebrowOpacity = interpolate(frame, [0.5 * fps, 1 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const headlineOpacity = interpolate(frame, [1 * fps, 1.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const earningItems = [
    {label: 'Battery arbitrage', value: '$165', delay: 3},
    {label: 'Follow Me Power', value: '$127', delay: 4.5},
    {label: 'Job site offsets', value: '$89', delay: 6},
    {label: 'HVAC + hot water', value: '$89', delay: 7.5},
  ];

  const fitComparison = interpolate(frame, [9 * fps, 10 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.02} />

      {/* Left: phone mockup */}
      <div
        style={{
          position: 'absolute',
          left: 80,
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
              src={staticFile('app-earnings.png')}
              style={{width: '100%', height: 'auto'}}
            />
          </div>
        </div>
      </div>

      {/* Right: callouts */}
      <div
        style={{
          position: 'absolute',
          top: 120,
          left: 560,
          right: 120,
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
          EARNINGS DASHBOARD
        </div>
        <div
          style={{
            opacity: headlineOpacity,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 52,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.15,
            marginBottom: 16,
          }}
        >
          <span style={{color: BRAND.amber}}>$216</span> this month.
        </div>
        <div
          style={{
            opacity: headlineOpacity,
            fontFamily: 'Inter, sans-serif',
            fontSize: 22,
            color: BRAND.warmGrey,
            marginBottom: 50,
          }}
        >
          +18% vs last period. Five revenue streams, one app.
        </div>

        {/* Earnings breakdown */}
        {earningItems.map((item, i) => {
          const itemOpacity = interpolate(
            frame,
            [item.delay * fps, (item.delay + 0.5) * fps],
            [0, 1],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
          );
          return (
            <div
              key={i}
              style={{
                opacity: itemOpacity,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '16px 0',
                borderBottom: `1px solid ${BRAND.charcoalLight}`,
              }}
            >
              <span
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: 22,
                  color: BRAND.white,
                }}
              >
                {item.label}
              </span>
              <span
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: 28,
                  fontWeight: 600,
                  color: BRAND.amber,
                }}
              >
                {item.value}
              </span>
            </div>
          );
        })}

        {/* FiT comparison */}
        <div
          style={{
            marginTop: 40,
            opacity: fitComparison,
            padding: '24px 30px',
            backgroundColor: `${BRAND.teal}15`,
            borderRadius: 8,
            borderLeft: `3px solid ${BRAND.teal}`,
          }}
        >
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 20,
              color: BRAND.warmGrey,
              marginBottom: 8,
            }}
          >
            FiT would've paid you{' '}
            <span style={{color: BRAND.warmGrey, fontWeight: 600}}>$3.80</span>
          </div>
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 24,
              color: BRAND.white,
              fontWeight: 600,
            }}
          >
            citEther earned you{' '}
            <span style={{color: BRAND.amber}}>$47.24</span>
            <span style={{color: BRAND.teal}}> today</span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
