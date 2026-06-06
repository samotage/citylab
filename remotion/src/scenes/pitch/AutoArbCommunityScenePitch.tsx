import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

const assets = [
  {name: 'Battery', icon: '🔋'},
  {name: 'HVAC', icon: '❄️'},
  {name: 'Hot Water', icon: '🔥'},
  {name: 'EV', icon: '⚡'},
  {name: 'Pool Pump', icon: '🌊'},
];

export const AutoArbCommunityScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Left panel: Auto-Arb (0-10s)
  const leftEyebrow = interpolate(frame, [0, 0.4 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const leftHeadline = interpolate(frame, [0.5 * fps, 1.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Right panel: Pods (10-20s)
  const rightEyebrow = interpolate(frame, [9 * fps, 9.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const rightHeadline = interpolate(frame, [9.5 * fps, 10.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Divider animation
  const dividerHeight = interpolate(frame, [8 * fps, 9 * fps], [0, 700], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.03} />

      {/* Left: Auto-Arb */}
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 100,
          width: 780,
          zIndex: 1,
        }}
      >
        <div
          style={{
            opacity: leftEyebrow,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 18,
            fontWeight: 500,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color: BRAND.amber,
            marginBottom: 20,
          }}
        >
          AUTO-ARB ENGINE
        </div>
        <div
          style={{
            opacity: leftHeadline,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 52,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: 40,
          }}
        >
          Set it. Forget it.
          <br />
          <span style={{color: BRAND.warmGrey, fontWeight: 300, fontSize: 32}}>
            Every smart asset orchestrated.
          </span>
        </div>

        {/* Asset chips */}
        <div style={{display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 40}}>
          {assets.map((asset, i) => {
            const delay = 2 + i * 0.6;
            const chipOpacity = interpolate(
              frame,
              [delay * fps, (delay + 0.4) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const chipScale = interpolate(
              frame,
              [delay * fps, (delay + 0.4) * fps],
              [0.8, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            return (
              <div
                key={i}
                style={{
                  opacity: chipOpacity,
                  transform: `scale(${chipScale})`,
                  backgroundColor: BRAND.charcoalLight,
                  borderRadius: 8,
                  padding: '16px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span style={{fontSize: 24}}>{asset.icon}</span>
                <span
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontSize: 18,
                    color: BRAND.white,
                    fontWeight: 500,
                  }}
                >
                  {asset.name}
                </span>
              </div>
            );
          })}
        </div>

        {/* Rules tagline */}
        <div
          style={{
            opacity: interpolate(frame, [5 * fps, 5.5 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            fontFamily: 'Inter, sans-serif',
            fontSize: 24,
            color: BRAND.warmGrey,
            lineHeight: 1.6,
            borderLeft: `3px solid ${BRAND.amber}`,
            paddingLeft: 24,
          }}
        >
          Charges when power is cheap. Discharges when it's valuable.
          <br />
          Pre-cools before a price spike. Never sacrifices your comfort.
          <br />
          <span style={{color: BRAND.amber, fontWeight: 600}}>
            You set the rules. Auto-Arb follows them.
          </span>
        </div>
      </div>

      {/* Center divider */}
      <div
        style={{
          position: 'absolute',
          left: 940,
          top: '50%',
          transform: 'translateY(-50%)',
          width: 2,
          height: dividerHeight,
          backgroundColor: BRAND.charcoalLight,
          zIndex: 1,
        }}
      />

      {/* Right: Pods + Community */}
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 1000,
          right: 100,
          zIndex: 1,
        }}
      >
        <div
          style={{
            opacity: rightEyebrow,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 18,
            fontWeight: 500,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color: BRAND.teal,
            marginBottom: 20,
          }}
        >
          CITETHER PODS
        </div>
        <div
          style={{
            opacity: rightHeadline,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 40,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: 40,
          }}
        >
          Your street.
          <br />
          Your microgrid.
        </div>

        {/* Pod diagram */}
        <div
          style={{
            opacity: interpolate(frame, [11 * fps, 12 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <svg width={400} height={300} viewBox="0 0 400 300">
            {/* Houses in a cluster */}
            {[
              {x: 80, y: 60},
              {x: 200, y: 40},
              {x: 320, y: 60},
              {x: 80, y: 180},
              {x: 200, y: 200},
              {x: 320, y: 180},
            ].map((pos, i) => {
              const houseDelay = 11.5 + i * 0.3;
              const houseOpacity = interpolate(
                frame,
                [houseDelay * fps, (houseDelay + 0.3) * fps],
                [0, 1],
                {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
              );
              return (
                <React.Fragment key={i}>
                  <rect
                    x={pos.x - 18}
                    y={pos.y - 10}
                    width={36}
                    height={28}
                    fill={BRAND.charcoalLight}
                    rx={3}
                    opacity={houseOpacity}
                  />
                  <polygon
                    points={`${pos.x - 22},${pos.y - 10} ${pos.x},${pos.y - 28} ${pos.x + 22},${pos.y - 10}`}
                    fill={BRAND.charcoalLight}
                    opacity={houseOpacity}
                  />
                  <rect
                    x={pos.x - 6}
                    y={pos.y - 6}
                    width={12}
                    height={8}
                    fill={BRAND.amber}
                    rx={1}
                    opacity={houseOpacity * 0.8}
                  />
                </React.Fragment>
              );
            })}
            {/* Connection lines */}
            {[
              [80, 60, 200, 40],
              [200, 40, 320, 60],
              [80, 60, 80, 180],
              [80, 180, 200, 200],
              [200, 200, 320, 180],
              [320, 60, 320, 180],
              [200, 40, 200, 200],
            ].map(([x1, y1, x2, y2], i) => {
              const lineDelay = 13 + i * 0.2;
              const lineOpacity = interpolate(
                frame,
                [lineDelay * fps, (lineDelay + 0.3) * fps],
                [0, 0.4],
                {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
              );
              return (
                <line
                  key={`l${i}`}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={BRAND.teal}
                  strokeWidth={1.5}
                  opacity={lineOpacity}
                  strokeDasharray="4 3"
                />
              );
            })}
            {/* Pod boundary */}
            <rect
              x={30}
              y={0}
              width={340}
              height={240}
              fill="none"
              stroke={BRAND.amber}
              strokeWidth={1.5}
              strokeDasharray="8 4"
              rx={8}
              opacity={interpolate(frame, [14 * fps, 15 * fps], [0, 0.5], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              })}
            />
            <text
              x={200}
              y={270}
              textAnchor="middle"
              fill={BRAND.warmGrey}
              fontFamily="JetBrains Mono, monospace"
              fontSize={11}
              letterSpacing="0.1em"
            >
              SAME TRANSFORMER · SAME FEEDER
            </text>
          </svg>
        </div>

        {/* Community features */}
        <div
          style={{
            marginTop: 20,
            opacity: interpolate(frame, [15 * fps, 16 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            fontFamily: 'Inter, sans-serif',
            fontSize: 18,
            color: BRAND.warmGrey,
            lineHeight: 1.6,
          }}
        >
          Community battery shares.
          <br />
          Social norming from Opower trials.
          <br />
          <span style={{color: BRAND.teal}}>Local energy stays local.</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
