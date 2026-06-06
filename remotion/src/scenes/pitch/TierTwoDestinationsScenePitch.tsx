import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

const destinations = [
  {label: 'Use it', desc: 'Job site, EV, second property', color: BRAND.amber},
  {label: 'Share it', desc: "Mum's flat, kid at uni", color: BRAND.amber},
  {label: 'Donate it', desc: 'Local charity, food bank', color: BRAND.teal},
  {label: 'Sell it', desc: 'Business, Pod, or wholesale', color: BRAND.teal},
];

export const TierTwoDestinationsScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phase 1: Tier 2 examples (0-8s)
  const tier2Opacity = interpolate(frame, [0, 0.5 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const tier2Items = [
    {text: 'Kid at uni', delay: 0.8},
    {text: 'Holiday house', delay: 2},
    {text: 'Split-site business', delay: 3.2},
  ];

  // Phase 2: Six destinations (8-16s)
  const destEyebrow = interpolate(frame, [7 * fps, 7.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 3: FiT punchline (16-20s)
  const fitOpacity = interpolate(frame, [15 * fps, 16 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.03} />

      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 120,
          right: 120,
          zIndex: 1,
        }}
      >
        {/* Phase 1: Tier 2 quick examples */}
        <div
          style={{
            opacity: tier2Opacity,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 18,
            fontWeight: 500,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color: BRAND.teal,
            marginBottom: 30,
          }}
        >
          AND IT KEEPS GOING
        </div>

        <div
          style={{
            display: 'flex',
            gap: 30,
            marginBottom: 70,
          }}
        >
          {tier2Items.map((item, i) => {
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
                  backgroundColor: BRAND.charcoalLight,
                  borderRadius: 8,
                  padding: '24px 32px',
                  flex: 1,
                }}
              >
                <div
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 600,
                    fontSize: 24,
                    color: BRAND.white,
                  }}
                >
                  {item.text}
                </div>
              </div>
            );
          })}
        </div>

        {/* Phase 2: Destinations */}
        <div
          style={{
            opacity: destEyebrow,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 18,
            fontWeight: 500,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color: BRAND.amber,
            marginBottom: 20,
          }}
        >
          YOUR ENERGY, YOUR CHOICE
        </div>
        <div
          style={{
            opacity: destEyebrow,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 48,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            marginBottom: 40,
          }}
        >
          Four destinations. Zero waste.
        </div>

        <div
          style={{
            display: 'flex',
            gap: 24,
            marginBottom: 60,
          }}
        >
          {destinations.map((dest, i) => {
            const delay = 8.5 + i * 1.2;
            const cardOpacity = interpolate(
              frame,
              [delay * fps, (delay + 0.5) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const cardScale = interpolate(
              frame,
              [delay * fps, (delay + 0.5) * fps],
              [0.9, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );

            return (
              <div
                key={i}
                style={{
                  opacity: cardOpacity,
                  transform: `scale(${cardScale})`,
                  flex: 1,
                  backgroundColor: 'transparent',
                  border: `2px solid ${dest.color}`,
                  borderRadius: 8,
                  padding: '30px 24px',
                  textAlign: 'center',
                }}
              >
                <div
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 700,
                    fontSize: 26,
                    color: dest.color,
                    marginBottom: 10,
                  }}
                >
                  {dest.label}
                </div>
                <div
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontSize: 16,
                    color: BRAND.warmGrey,
                    lineHeight: 1.4,
                  }}
                >
                  {dest.desc}
                </div>
              </div>
            );
          })}
        </div>

        {/* Phase 3: FiT punchline */}
        <div
          style={{
            opacity: fitOpacity,
            textAlign: 'center',
            padding: '40px 60px',
            backgroundColor: `${BRAND.amber}15`,
            borderRadius: 8,
            borderLeft: `4px solid ${BRAND.amber}`,
          }}
        >
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontWeight: 700,
              fontSize: 36,
              color: BRAND.white,
              lineHeight: 1.4,
            }}
          >
            The feed-in tariff becomes irrelevant.
          </div>
          <div
            style={{
              marginTop: 12,
              fontFamily: 'Inter, sans-serif',
              fontSize: 24,
              color: BRAND.amber,
              fontWeight: 600,
            }}
          >
            You always have a better option.
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
