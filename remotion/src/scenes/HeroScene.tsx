import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../brand';
import {GridPattern} from '../components/GridPattern';
import {EyebrowLabel} from '../components/EyebrowLabel';

const CountUp: React.FC<{value: number; suffix: string; startFrame: number}> = ({
  value,
  suffix,
  startFrame,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = interpolate(
    frame,
    [startFrame, startFrame + 1 * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const current = Math.round(value * progress * 10) / 10;
  return (
    <span
      style={{
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 56,
        fontWeight: 600,
        color: BRAND.amber,
      }}
    >
      {current % 1 === 0 ? current.toFixed(0) : current.toFixed(1)}
      {suffix}
    </span>
  );
};

export const HeroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const lines = [
    {text: 'Your energy.', color: BRAND.white},
    {text: 'Your value.', color: BRAND.white},
    {text: 'Your community.', color: BRAND.amber},
  ];

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.05} />
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 80,
          right: 80,
          zIndex: 1,
        }}
      >
        <div
          style={{
            opacity: interpolate(frame, [0, 0.5 * fps], [0, 1], {
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <EyebrowLabel text="DISTRIBUTED ENERGY · REAL-TIME VALUE" color={BRAND.amber} />
        </div>

        <div style={{marginTop: 50}}>
          {lines.map((line, i) => {
            const delay = 0.4 + i * 0.5;
            const opacity = interpolate(
              frame,
              [delay * fps, (delay + 0.5) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const y = interpolate(
              frame,
              [delay * fps, (delay + 0.5) * fps],
              [40, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            return (
              <div
                key={i}
                style={{
                  opacity,
                  transform: `translateY(${y}px)`,
                  fontFamily: 'Inter, sans-serif',
                  fontWeight: 700,
                  fontSize: 88,
                  color: line.color,
                  letterSpacing: '-0.03em',
                  lineHeight: 1.1,
                }}
              >
                {line.text}
              </div>
            );
          })}
        </div>

        <div
          style={{
            marginTop: 50,
            opacity: interpolate(frame, [2.5 * fps, 3 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            fontFamily: 'Inter, sans-serif',
            fontWeight: 400,
            fontSize: 28,
            color: BRAND.warmGrey,
            lineHeight: 1.6,
            maxWidth: 800,
          }}
        >
          citEther connects your solar, battery, and EV to the grid — and puts
          real money in your pocket for doing it.
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          bottom: 200,
          left: 80,
          right: 80,
          display: 'flex',
          justifyContent: 'space-between',
          zIndex: 1,
        }}
      >
        {[
          {val: 4.3, suf: 'M', label: 'solar households', delay: 3.5},
          {val: 7, suf: ' TWh', label: 'clean energy curtailed', delay: 3.8},
          {val: 31, suf: '%', label: 'negative price intervals', delay: 4.1},
        ].map((stat, i) => {
          const opacity = interpolate(
            frame,
            [stat.delay * fps, (stat.delay + 0.5) * fps],
            [0, 1],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
          );
          return (
            <div
              key={i}
              style={{
                opacity,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}
            >
              <CountUp
                value={stat.val}
                suffix={stat.suf}
                startFrame={stat.delay * fps}
              />
              <span
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: 18,
                  color: BRAND.warmGrey,
                  marginTop: 8,
                }}
              >
                {stat.label}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
