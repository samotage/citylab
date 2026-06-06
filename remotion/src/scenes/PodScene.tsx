import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../brand';
import {EyebrowLabel} from '../components/EyebrowLabel';

const House: React.FC<{
  x: number;
  y: number;
  label: string;
  delay: number;
}> = ({x, y, label, delay}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = interpolate(
    frame,
    [delay * fps, (delay + 0.4) * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  return (
    <g opacity={opacity}>
      {/* House shape */}
      <rect x={x - 25} y={y - 15} width={50} height={35} rx={3} fill={BRAND.charcoalLight} stroke={BRAND.warmGrey} strokeWidth={1} />
      <polygon points={`${x - 30},${y - 15} ${x},${y - 40} ${x + 30},${y - 15}`} fill={BRAND.charcoalLight} stroke={BRAND.warmGrey} strokeWidth={1} />
      {/* Solar panel indicator */}
      <rect x={x - 12} y={y - 35} width={24} height={12} rx={2} fill={BRAND.amber} opacity={0.7} />
      <text x={x} y={y + 50} fill={BRAND.warmGrey} fontSize={14} fontFamily="Inter, sans-serif" textAnchor="middle">
        {label}
      </text>
    </g>
  );
};

export const PodScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const flowOpacity = interpolate(
    frame,
    [2 * fps, 2.5 * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  const pulse = Math.sin(frame / 8) * 0.3 + 0.7;

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.offWhite}}>
      <div
        style={{
          position: 'absolute',
          top: 160,
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
          <EyebrowLabel text="CITETHER POD" />
        </div>
        <div
          style={{
            marginTop: 30,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 54,
            color: BRAND.charcoal,
            letterSpacing: '-0.02em',
            lineHeight: 1.15,
            opacity: interpolate(frame, [0.3 * fps, 0.8 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          Your street.{'\n'}Your microgrid.{'\n'}Your rules.
        </div>
      </div>

      {/* Pod diagram */}
      <svg
        width={920}
        height={650}
        viewBox="0 0 920 650"
        style={{
          position: 'absolute',
          top: 650,
          left: 80,
        }}
      >
        {/* Pod boundary */}
        <rect
          x={40}
          y={40}
          width={840}
          height={450}
          rx={12}
          fill="none"
          stroke={BRAND.amber}
          strokeWidth={2}
          strokeDasharray="12 6"
          opacity={interpolate(frame, [1.5 * fps, 2 * fps], [0, 0.6], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })}
        />

        {/* Houses */}
        <House x={150} y={150} label="House A" delay={1} />
        <House x={380} y={120} label="House B" delay={1.2} />
        <House x={600} y={160} label="House C" delay={1.4} />
        <House x={780} y={140} label="House D" delay={1.6} />
        <House x={250} y={350} label="House E" delay={1.8} />
        <House x={500} y={370} label="House F" delay={2} />

        {/* Energy flow lines */}
        <g opacity={flowOpacity}>
          <line x1={175} y1={150} x2={355} y2={130} stroke={BRAND.amber} strokeWidth={2} opacity={pulse} />
          <line x1={405} y1={130} x2={575} y2={160} stroke={BRAND.teal} strokeWidth={2} opacity={pulse * 0.8} />
          <line x1={625} y1={165} x2={755} y2={145} stroke={BRAND.amber} strokeWidth={2} opacity={pulse * 0.9} />
          <line x1={275} y1={340} x2={475} y2={360} stroke={BRAND.teal} strokeWidth={2} opacity={pulse * 0.7} />
          <line x1={380} y1={145} x2={280} y2={330} stroke={BRAND.amber} strokeWidth={2} opacity={pulse * 0.85} />
        </g>

        {/* Grid connection */}
        <line x1={460} y1={490} x2={460} y2={580} stroke={BRAND.warmGrey} strokeWidth={1} opacity={0.5} />
        <text x={460} y={610} fill={BRAND.warmGrey} fontSize={16} fontFamily="JetBrains Mono, monospace" textAnchor="middle" opacity={0.6}>
          THE GRID
        </text>

        {/* Pod label */}
        <text x={460} y={30} fill={BRAND.amber} fontSize={16} fontFamily="JetBrains Mono, monospace" textAnchor="middle" fontWeight={600}>
          CITETHER POD
        </text>
      </svg>

      {/* Benefits */}
      <div
        style={{
          position: 'absolute',
          bottom: 100,
          left: 80,
          right: 80,
          opacity: interpolate(frame, [4 * fps, 4.5 * fps], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
          fontFamily: 'Inter, sans-serif',
          fontSize: 22,
          color: BRAND.bodyText,
          lineHeight: 1.8,
        }}
      >
        <div style={{borderLeft: `3px solid ${BRAND.amber}`, paddingLeft: 16, marginBottom: 16}}>
          Reduced losses · Lower cost · Grid relief · Community resilience
        </div>
      </div>
    </AbsoluteFill>
  );
};
