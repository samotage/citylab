import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

const examples = [
  {
    icon: '⌂',
    title: "Power Mum's Flat",
    description: 'Your rooftop solar offsets her bill at a separate address.',
    stat: 'Your roof → her bill',
    color: BRAND.amber,
  },
  {
    icon: '⚒',
    title: 'Tradie on Site',
    description: 'Home solar credits power tools and compressors across town.',
    stat: 'Replaces diesel at $0.50/kWh',
    color: BRAND.teal,
  },
  {
    icon: '⚡',
    title: 'EV Road Trip',
    description: 'Fast charger costs offset by home solar credits.',
    stat: 'Net charging: near zero',
    color: BRAND.amber,
  },
  {
    icon: '⚕',
    title: 'Nurse at Hospital',
    description: 'EV supplies the constrained node for a 12-hour shift.',
    stat: 'Earns $40–60 while they work',
    color: BRAND.teal,
  },
];

export const TierOneScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const eyebrowOpacity = interpolate(frame, [0, 0.4 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.offWhite}}>
      <GridPattern opacity={0.04} />
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 120,
          right: 120,
          zIndex: 1,
        }}
      >
        <div
          style={{
            opacity: eyebrowOpacity,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 18,
            fontWeight: 500,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color: BRAND.teal,
            marginBottom: 16,
          }}
        >
          FOLLOW ME POWER IN ACTION
        </div>
        <div
          style={{
            opacity: eyebrowOpacity,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 48,
            color: BRAND.charcoal,
            letterSpacing: '-0.02em',
            marginBottom: 50,
          }}
        >
          Four ways your energy travels.
        </div>

        {/* 2x2 grid of examples */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 30,
          }}
        >
          {examples.map((ex, i) => {
            const delay = 2 + i * 5;
            const cardOpacity = interpolate(
              frame,
              [delay * fps, (delay + 0.6) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const cardY = interpolate(
              frame,
              [delay * fps, (delay + 0.6) * fps],
              [20, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const statOpacity = interpolate(
              frame,
              [(delay + 1.5) * fps, (delay + 2) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const borderProgress = interpolate(
              frame,
              [(delay + 0.3) * fps, (delay + 1) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );

            return (
              <div
                key={i}
                style={{
                  opacity: cardOpacity,
                  transform: `translateY(${cardY}px)`,
                  width: 'calc(50% - 15px)',
                  backgroundColor: BRAND.white,
                  borderRadius: 8,
                  padding: '36px 40px',
                  borderLeft: `4px solid ${ex.color}`,
                  borderLeftWidth: 4 * borderProgress,
                  boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
                }}
              >
                <div
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 700,
                    fontSize: 28,
                    color: BRAND.charcoal,
                    marginBottom: 12,
                  }}
                >
                  {ex.title}
                </div>
                <div
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontSize: 20,
                    color: BRAND.bodyText,
                    lineHeight: 1.5,
                    marginBottom: 20,
                  }}
                >
                  {ex.description}
                </div>
                <div
                  style={{
                    opacity: statOpacity,
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 18,
                    fontWeight: 600,
                    color: ex.color,
                  }}
                >
                  {ex.stat}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
