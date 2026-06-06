import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../../brand';
import {EyebrowLabel} from '../../components/EyebrowLabel';
import {GridPattern} from '../../components/GridPattern';

export const ProblemScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const line1 = interpolate(frame, [0, 0.5 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const line2 = interpolate(frame, [0.6 * fps, 1.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const line3 = interpolate(frame, [1.4 * fps, 2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 2 — stats and "nobody" line (from ~12s)
  const statsDelay = 10;
  const stat1 = interpolate(frame, [statsDelay * fps, (statsDelay + 0.6) * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stat1Y = interpolate(frame, [statsDelay * fps, (statsDelay + 0.6) * fps], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stat2 = interpolate(frame, [(statsDelay + 2) * fps, (statsDelay + 2.6) * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stat2Y = interpolate(frame, [(statsDelay + 2) * fps, (statsDelay + 2.6) * fps], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stat3 = interpolate(frame, [(statsDelay + 4) * fps, (statsDelay + 4.6) * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stat3Y = interpolate(frame, [(statsDelay + 4) * fps, (statsDelay + 4.6) * fps], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Meter boundary animation — amber line that "blocks" energy
  const meterLineHeight = interpolate(frame, [3 * fps, 4.5 * fps], [0, 600], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const meterOpacity = interpolate(frame, [3 * fps, 4 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const meterGlow = interpolate(frame, [4.5 * fps, 6 * fps, 8 * fps, 9 * fps], [0, 8, 8, 4], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.03} />

      {/* Left: headline text */}
      <div
        style={{
          position: 'absolute',
          top: 120,
          left: 120,
          width: 900,
          zIndex: 1,
        }}
      >
        <div style={{opacity: line1}}>
          <EyebrowLabel text="THE PROBLEM" color={BRAND.amber} />
        </div>
        <div
          style={{
            marginTop: 40,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 72,
            color: BRAND.white,
            letterSpacing: '-0.03em',
            lineHeight: 1.15,
          }}
        >
          <span style={{opacity: line1}}>Your energy is</span>
          <br />
          <span style={{opacity: line2, color: BRAND.amber}}>trapped</span>
          <span style={{opacity: line2}}> at</span>
          <br />
          <span style={{opacity: line3}}>your meter.</span>
        </div>

        {/* Phase 2 stats */}
        <div style={{marginTop: 80}}>
          <div
            style={{
              opacity: stat1,
              transform: `translateY(${stat1Y}px)`,
              display: 'flex',
              alignItems: 'baseline',
              gap: 16,
              marginBottom: 24,
            }}
          >
            <span
              style={{
                fontFamily: 'Inter, sans-serif',
                fontWeight: 700,
                fontSize: 48,
                color: BRAND.amber,
              }}
            >
              4.3M
            </span>
            <span
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 24,
                color: BRAND.warmGrey,
              }}
            >
              solar households generating energy locked to one address
            </span>
          </div>
          <div
            style={{
              opacity: stat2,
              transform: `translateY(${stat2Y}px)`,
              display: 'flex',
              alignItems: 'baseline',
              gap: 16,
              marginBottom: 24,
            }}
          >
            <span
              style={{
                fontFamily: 'Inter, sans-serif',
                fontWeight: 700,
                fontSize: 48,
                color: BRAND.teal,
              }}
            >
              2.4M+
            </span>
            <span
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 24,
                color: BRAND.warmGrey,
              }}
            >
              sole traders with home solar and remote work sites
            </span>
          </div>
          <div
            style={{
              opacity: stat3,
              transform: `translateY(${stat3Y}px)`,
              fontFamily: 'Inter, sans-serif',
              fontWeight: 600,
              fontSize: 28,
              color: BRAND.white,
              lineHeight: 1.5,
            }}
          >
            Every platform optimises at the meter.
            <br />
            <span style={{color: BRAND.amber}}>
              Nobody has broken energy free from the address.
            </span>
          </div>
        </div>
      </div>

      {/* Right: meter boundary visual */}
      <div
        style={{
          position: 'absolute',
          right: 160,
          top: '50%',
          transform: 'translateY(-50%)',
          opacity: meterOpacity,
          zIndex: 1,
        }}
      >
        <svg width={200} height={600} viewBox="0 0 200 600">
          {/* Meter boundary line */}
          <line
            x1={100}
            y1={300 - meterLineHeight / 2}
            x2={100}
            y2={300 + meterLineHeight / 2}
            stroke={BRAND.amber}
            strokeWidth={4}
            filter={meterGlow > 0 ? `drop-shadow(0 0 ${meterGlow}px ${BRAND.amber})` : undefined}
          />
          {/* Energy arrows bouncing off the barrier */}
          {[0, 1, 2, 3].map((i) => {
            const arrowDelay = 5 + i * 0.8;
            const arrowX = interpolate(
              frame,
              [arrowDelay * fps, (arrowDelay + 0.5) * fps],
              [0, 80],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const arrowOpacity = interpolate(
              frame,
              [arrowDelay * fps, (arrowDelay + 0.3) * fps, (arrowDelay + 0.5) * fps, (arrowDelay + 0.8) * fps],
              [0, 1, 1, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const yPos = 150 + i * 100;
            return (
              <circle
                key={i}
                cx={arrowX}
                cy={yPos}
                r={8}
                fill={BRAND.teal}
                opacity={arrowOpacity}
              />
            );
          })}
          {/* Meter label */}
          <text
            x={100}
            y={590}
            textAnchor="middle"
            fill={BRAND.warmGrey}
            fontFamily="JetBrains Mono, monospace"
            fontSize={14}
            letterSpacing="0.1em"
          >
            YOUR METER
          </text>
        </svg>
      </div>
    </AbsoluteFill>
  );
};
