import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../brand';
import {EyebrowLabel} from '../components/EyebrowLabel';

const FlowBlock: React.FC<{
  label: string;
  subtitle: string;
  bg: string;
  textColor: string;
  delay: number;
}> = ({label, subtitle, bg, textColor, delay}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = interpolate(
    frame,
    [delay * fps, (delay + 0.4) * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const scale = interpolate(
    frame,
    [delay * fps, (delay + 0.4) * fps],
    [0.9, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  return (
    <div
      style={{
        opacity,
        transform: `scale(${scale})`,
        backgroundColor: bg,
        padding: '30px 40px',
        borderRadius: 6,
        textAlign: 'center',
        flex: 1,
      }}
    >
      <div
        style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: 14,
          letterSpacing: '0.1em',
          textTransform: 'uppercase' as const,
          color: textColor,
          opacity: 0.7,
          marginBottom: 8,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: 'Inter, sans-serif',
          fontSize: 20,
          fontWeight: 500,
          color: textColor,
        }}
      >
        {subtitle}
      </div>
    </div>
  );
};

export const EconomicsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <div
        style={{
          position: 'absolute',
          top: 200,
          left: 80,
          right: 80,
        }}
      >
        <div
          style={{
            opacity: interpolate(frame, [0, 0.4 * fps], [0, 1], {
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <EyebrowLabel text="THE MODEL" color={BRAND.amber} />
        </div>
        <div
          style={{
            marginTop: 30,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 48,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            opacity: interpolate(frame, [0.3 * fps, 0.8 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          The grid pays. You earn. citEther takes a margin.
        </div>

        {/* Flow diagram - vertical for 9:16 */}
        <div
          style={{
            marginTop: 80,
            display: 'flex',
            flexDirection: 'column',
            gap: 0,
            alignItems: 'stretch',
          }}
        >
          <FlowBlock
            label="Grid Operator"
            subtitle="Pays for coordinated DER"
            bg={BRAND.charcoalLight}
            textColor={BRAND.white}
            delay={1.2}
          />
          <div
            style={{
              textAlign: 'center',
              padding: '8px 0',
              opacity: interpolate(frame, [1.5 * fps, 1.8 * fps], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
            }}
          >
            <span style={{color: BRAND.warmGrey, fontSize: 28}}>↓</span>
          </div>
          <FlowBlock
            label="citEther"
            subtitle="Optimises, coordinates, settles"
            bg={BRAND.amber}
            textColor={BRAND.charcoal}
            delay={1.8}
          />
          <div
            style={{
              textAlign: 'center',
              padding: '8px 0',
              opacity: interpolate(frame, [2.1 * fps, 2.4 * fps], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
            }}
          >
            <span style={{color: BRAND.warmGrey, fontSize: 28}}>↓</span>
          </div>
          <FlowBlock
            label="You"
            subtitle="Net positive. Always."
            bg={BRAND.teal}
            textColor={BRAND.white}
            delay={2.4}
          />
        </div>

        {/* Three value props */}
        <div
          style={{
            marginTop: 80,
            display: 'flex',
            flexDirection: 'column',
            gap: 30,
          }}
        >
          {[
            {label: 'FOR YOU', text: 'Direct payments. Savings-share model. Always net positive.', color: BRAND.amber},
            {label: 'FOR THE GRID', text: 'Cheaper than $2B gas peakers. 100K batteries beat one plant.', color: BRAND.teal},
            {label: 'FOR THE PLANET', text: 'Every kWh of flexibility = a kWh of fossil fuel that doesn\'t fire.', color: BRAND.white},
          ].map((item, i) => {
            const delay = 3 + i * 0.5;
            const opacity = interpolate(
              frame,
              [delay * fps, (delay + 0.4) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            return (
              <div key={i} style={{opacity}}>
                <div
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 16,
                    color: item.color,
                    letterSpacing: '0.08em',
                    marginBottom: 6,
                  }}
                >
                  {item.label}
                </div>
                <div
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontSize: 22,
                    color: BRAND.warmGrey,
                    lineHeight: 1.5,
                  }}
                >
                  {item.text}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
