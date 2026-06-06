import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../brand';
import {EyebrowLabel} from '../components/EyebrowLabel';

const MapDot: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const cycle = (frame % (6 * fps)) / (6 * fps);
  const x = interpolate(cycle, [0, 0.4, 0.6, 1], [300, 650, 800, 300], {
    extrapolateRight: 'clamp',
  });
  const y = interpolate(cycle, [0, 0.4, 0.6, 1], [700, 500, 350, 700], {
    extrapolateRight: 'clamp',
  });
  return (
    <>
      <circle cx={x} cy={y} r={24} fill={BRAND.amber} opacity={0.2} />
      <circle cx={x} cy={y} r={12} fill={BRAND.amber} />
    </>
  );
};

export const FollowMePowerScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 80,
          right: 80,
          zIndex: 2,
        }}
      >
        <div
          style={{
            opacity: interpolate(frame, [0, 0.4 * fps], [0, 1], {
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <EyebrowLabel text="FOLLOW ME POWER" color={BRAND.amber} />
        </div>
        <div
          style={{
            marginTop: 30,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 56,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.15,
            opacity: interpolate(frame, [0.3 * fps, 0.8 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          Your EV earns money wherever you park.
        </div>
      </div>

      {/* Stylised map */}
      <svg
        width={1080}
        height={900}
        viewBox="0 0 1080 900"
        style={{
          position: 'absolute',
          top: 550,
          left: 0,
          opacity: interpolate(frame, [0.5 * fps, 1 * fps], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
        }}
      >
        {/* Road grid */}
        <line x1={100} y1={200} x2={900} y2={200} stroke={BRAND.charcoalLight} strokeWidth={1} />
        <line x1={100} y1={400} x2={900} y2={400} stroke={BRAND.charcoalLight} strokeWidth={1} />
        <line x1={100} y1={600} x2={900} y2={600} stroke={BRAND.charcoalLight} strokeWidth={1} />
        <line x1={250} y1={100} x2={250} y2={800} stroke={BRAND.charcoalLight} strokeWidth={1} />
        <line x1={550} y1={100} x2={550} y2={800} stroke={BRAND.charcoalLight} strokeWidth={1} />
        <line x1={800} y1={100} x2={800} y2={800} stroke={BRAND.charcoalLight} strokeWidth={1} />

        {/* Dotted route */}
        <path
          d="M 300 700 Q 500 550 650 500 Q 750 450 800 350"
          fill="none"
          stroke={BRAND.amber}
          strokeWidth={2}
          strokeDasharray="8 8"
          opacity={0.5}
        />

        {/* Suburb labels */}
        <text x={250} y={730} fill={BRAND.warmGrey} fontSize={20} fontFamily="Inter, sans-serif">
          Dandenong
        </text>
        <text x={520} y={530} fill={BRAND.warmGrey} fontSize={20} fontFamily="Inter, sans-serif">
          Clayton
        </text>
        <text x={720} y={330} fill={BRAND.warmGrey} fontSize={20} fontFamily="Inter, sans-serif">
          Springvale
        </text>

        {/* Price badges */}
        <rect x={220} y={640} width={130} height={45} rx={4} fill={BRAND.charcoal} stroke={BRAND.amber} strokeWidth={2} />
        <text x={250} y={670} fill={BRAND.amber} fontSize={22} fontFamily="JetBrains Mono, monospace" fontWeight={600}>
          $50/hr
        </text>

        <rect x={730} y={250} width={140} height={45} rx={4} fill={BRAND.charcoal} stroke={BRAND.amber} strokeWidth={2} />
        <text x={755} y={280} fill={BRAND.amber} fontSize={22} fontFamily="JetBrains Mono, monospace" fontWeight={600}>
          $80/hr ↑
        </text>

        <MapDot frame={frame} fps={fps} />
      </svg>

      {/* Pull quote */}
      <div
        style={{
          position: 'absolute',
          bottom: 180,
          left: 80,
          right: 80,
          opacity: interpolate(frame, [3 * fps, 3.5 * fps], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
          borderLeft: `4px solid ${BRAND.amber}`,
          paddingLeft: 24,
          zIndex: 2,
        }}
      >
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontWeight: 400,
            fontStyle: 'italic',
            fontSize: 30,
            color: BRAND.amber,
            lineHeight: 1.4,
          }}
        >
          "It's not vehicle-to-grid.{'\n'}It's vehicle-to-value."
        </div>
      </div>
    </AbsoluteFill>
  );
};
