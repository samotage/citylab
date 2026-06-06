import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../brand';
import {EyebrowLabel} from '../components/EyebrowLabel';

const Quote: React.FC<{
  text: string;
  context: string;
  delay: number;
}> = ({text, context, delay}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = interpolate(
    frame,
    [delay * fps, (delay + 0.6) * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const x = interpolate(
    frame,
    [delay * fps, (delay + 0.6) * fps],
    [-30, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  return (
    <div
      style={{
        opacity,
        transform: `translateX(${x}px)`,
        borderLeft: `4px solid ${BRAND.amber}`,
        paddingLeft: 30,
        marginBottom: 50,
      }}
    >
      <div
        style={{
          fontFamily: 'Inter, sans-serif',
          fontWeight: 400,
          fontStyle: 'italic',
          fontSize: 32,
          color: BRAND.white,
          lineHeight: 1.5,
          marginBottom: 12,
        }}
      >
        "{text}"
      </div>
      <div
        style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: 16,
          color: BRAND.warmGrey,
        }}
      >
        — {context}
      </div>
    </div>
  );
};

export const ProblemScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const headlineOpacity = interpolate(frame, [0, 0.5 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 80,
          right: 80,
        }}
      >
        <div style={{opacity: headlineOpacity}}>
          <EyebrowLabel text="THE TRUST CRISIS" color={BRAND.amber} />
        </div>

        <div
          style={{
            marginTop: 40,
            marginBottom: 80,
            opacity: interpolate(frame, [0.3 * fps, 0.8 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 52,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
          }}
        >
          You invested in solar.{'\n'}The energy companies invested in taking your value.
        </div>

        <Quote
          text="I already have a full time job."
          context="on babysitting wholesale prices"
          delay={1.5}
        />
        <Quote
          text="My family erased the entire year's savings in one day"
          context="one hot day, AC through a price spike"
          delay={2.5}
        />
        <Quote
          text="All of the ones you listed lock you down to the brand's components"
          context="on inverter ecosystem lock-in"
          delay={3.5}
        />
      </div>

      <div
        style={{
          position: 'absolute',
          bottom: 120,
          left: 80,
          right: 80,
          opacity: interpolate(frame, [5 * fps, 5.5 * fps], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: 18,
          color: BRAND.warmGrey,
          letterSpacing: '0.02em',
        }}
      >
        7 TWh curtailed · 31% negative intervals · $0 earned from flexibility
      </div>
    </AbsoluteFill>
  );
};
