import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

const marketCards = [
  {stat: '4.3M', label: 'SOLAR HOMES', desc: 'Generating value locked to one meter', color: BRAND.amber},
  {stat: '$0', label: 'FEED-IN TARIFF', desc: 'Retailers paying nothing for your export', color: BRAND.amber},
  {stat: 'ZERO', label: 'COMPETITORS', desc: 'No one does location-independent settlement', color: BRAND.teal},
  {stat: 'BUILT', label: 'NOT A SLIDE DECK', desc: 'Working intelligence layer, built at this hackathon', color: BRAND.teal},
];

export const SupportingDataScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const eyebrow = interpolate(frame, [0, 0.4 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const headline = interpolate(frame, [0.5 * fps, 1.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Sankey flow (12-22s)
  const sankeyEyebrow = interpolate(frame, [12 * fps, 12.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const solarBlock = interpolate(frame, [13 * fps, 13.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const arrow1 = interpolate(frame, [14 * fps, 14.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const citBlock = interpolate(frame, [14.5 * fps, 15 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const arrow2 = interpolate(frame, [15.5 * fps, 16 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const destBlock = interpolate(frame, [16 * fps, 16.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const feeLabel = interpolate(frame, [17 * fps, 17.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Punchline (22-30s)
  const punchline = interpolate(frame, [22 * fps, 23 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const builtItems = [
    'Real-time NEM price signals across VIC1',
    'Grid inertia + demand response engine',
    'Auto-Arb asset orchestration',
    'Follow Me Power settlement layer',
  ];

  const builtSection = interpolate(frame, [24 * fps, 25 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.03} />

      <div
        style={{
          position: 'absolute',
          top: 60,
          left: 120,
          right: 120,
          zIndex: 1,
        }}
      >
        {/* Eyebrow + headline */}
        <div
          style={{
            opacity: eyebrow,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 18,
            fontWeight: 500,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color: BRAND.amber,
            marginBottom: 16,
          }}
        >
          THE EVIDENCE
        </div>
        <div
          style={{
            opacity: headline,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 44,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: 40,
          }}
        >
          The market is waiting.{' '}
          <span style={{color: BRAND.amber}}>We built the answer.</span>
        </div>

        {/* Market data cards — 2×2 */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 20,
            marginBottom: 50,
          }}
        >
          {marketCards.map((card, i) => {
            const delay = 2 + i * 2.5;
            const cardOpacity = interpolate(
              frame,
              [delay * fps, (delay + 0.5) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const cardScale = interpolate(
              frame,
              [delay * fps, (delay + 0.5) * fps],
              [0.95, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            return (
              <div
                key={i}
                style={{
                  opacity: cardOpacity,
                  transform: `scale(${cardScale})`,
                  flex: '1 1 calc(50% - 10px)',
                  maxWidth: 'calc(50% - 10px)',
                  backgroundColor: `${BRAND.charcoalLight}60`,
                  borderRadius: 8,
                  padding: '28px 32px',
                  borderLeft: `4px solid ${card.color}`,
                }}
              >
                <div
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 700,
                    fontSize: 42,
                    color: card.color,
                    letterSpacing: '-0.02em',
                    marginBottom: 4,
                  }}
                >
                  {card.stat}
                </div>
                <div
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 12,
                    fontWeight: 500,
                    letterSpacing: '0.1em',
                    color: BRAND.warmGrey,
                    marginBottom: 8,
                  }}
                >
                  {card.label}
                </div>
                <div
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontSize: 16,
                    color: BRAND.white,
                    lineHeight: 1.4,
                  }}
                >
                  {card.desc}
                </div>
              </div>
            );
          })}
        </div>

        {/* Business model — Sankey flow */}
        <div
          style={{
            opacity: sankeyEyebrow,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 14,
            fontWeight: 500,
            letterSpacing: '0.1em',
            color: BRAND.teal,
            marginBottom: 20,
          }}
        >
          THE MODEL
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 0,
            marginBottom: 30,
          }}
        >
          <div
            style={{
              opacity: solarBlock,
              transform: `scale(${interpolate(solarBlock, [0, 1], [0.9, 1])})`,
              backgroundColor: BRAND.amber,
              borderRadius: 8,
              padding: '20px 28px',
              textAlign: 'center',
              minWidth: 180,
            }}
          >
            <div
              style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: 11,
                color: BRAND.charcoal,
                letterSpacing: '0.1em',
                marginBottom: 4,
              }}
            >
              YOUR SOLAR
            </div>
            <div
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 18,
                fontWeight: 600,
                color: BRAND.charcoal,
              }}
            >
              Generates credits
            </div>
          </div>

          <div style={{opacity: arrow1, padding: '0 12px'}}>
            <span style={{fontSize: 28, color: BRAND.charcoalLight}}>→</span>
          </div>

          <div
            style={{
              opacity: citBlock,
              transform: `scale(${interpolate(citBlock, [0, 1], [0.9, 1])})`,
              backgroundColor: BRAND.charcoalLight,
              borderRadius: 8,
              padding: '20px 28px',
              textAlign: 'center',
              minWidth: 220,
              position: 'relative',
            }}
          >
            <div
              style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: 11,
                color: BRAND.amber,
                letterSpacing: '0.1em',
                marginBottom: 4,
              }}
            >
              CITETHER
            </div>
            <div
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 18,
                fontWeight: 600,
                color: BRAND.white,
              }}
            >
              Settles across the grid
            </div>
            <div
              style={{
                position: 'absolute',
                bottom: -24,
                left: '10%',
                right: '10%',
                opacity: feeLabel,
                backgroundColor: BRAND.warmGrey,
                borderRadius: 4,
                padding: '4px 10px',
                textAlign: 'center',
              }}
            >
              <span
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: 10,
                  color: BRAND.white,
                  letterSpacing: '0.08em',
                }}
              >
                T&D NETWORK FEES DEDUCTED
              </span>
            </div>
          </div>

          <div style={{opacity: arrow2, padding: '0 12px'}}>
            <span style={{fontSize: 28, color: BRAND.charcoalLight}}>→</span>
          </div>

          <div
            style={{
              opacity: destBlock,
              transform: `scale(${interpolate(destBlock, [0, 1], [0.9, 1])})`,
              backgroundColor: BRAND.teal,
              borderRadius: 8,
              padding: '20px 28px',
              textAlign: 'center',
              minWidth: 180,
            }}
          >
            <div
              style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: 11,
                color: BRAND.white,
                letterSpacing: '0.1em',
                opacity: 0.8,
                marginBottom: 4,
              }}
            >
              NET VALUE
            </div>
            <div
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 18,
                fontWeight: 600,
                color: BRAND.white,
              }}
            >
              Delivered to you
            </div>
          </div>
        </div>

        {/* Punchline + built proof */}
        <div
          style={{
            marginTop: 50,
            opacity: punchline,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 28,
            color: BRAND.white,
            textAlign: 'center',
            marginBottom: 30,
          }}
        >
          Net value after network costs{' '}
          <span style={{color: BRAND.amber}}>still beats zero FiT.</span>
        </div>

        {/* Built at hackathon checklist */}
        <div style={{opacity: builtSection, display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center'}}>
          {builtItems.map((item, i) => {
            const itemDelay = 25 + i * 0.4;
            const itemOp = interpolate(
              frame,
              [itemDelay * fps, (itemDelay + 0.3) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            return (
              <div
                key={i}
                style={{
                  opacity: itemOp,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 16px',
                  backgroundColor: `${BRAND.teal}20`,
                  borderRadius: 6,
                }}
              >
                <div
                  style={{
                    width: 18,
                    height: 18,
                    borderRadius: 4,
                    backgroundColor: BRAND.teal,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 11,
                    color: BRAND.white,
                    fontWeight: 700,
                    flexShrink: 0,
                  }}
                >
                  ✓
                </div>
                <span
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontSize: 14,
                    color: BRAND.white,
                  }}
                >
                  {item}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
