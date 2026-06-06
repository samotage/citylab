import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../brand';
import {EyebrowLabel} from '../components/EyebrowLabel';

const Step: React.FC<{
  title: string;
  body: string;
  delay: number;
  isLast?: boolean;
}> = ({title, body, delay, isLast = false}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = interpolate(
    frame,
    [delay * fps, (delay + 0.5) * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const y = interpolate(
    frame,
    [delay * fps, (delay + 0.5) * fps],
    [20, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  return (
    <div style={{opacity, transform: `translateY(${y}px)`}}>
      <div
        style={{
          fontFamily: 'Inter, sans-serif',
          fontWeight: 600,
          fontSize: 36,
          color: BRAND.amber,
          marginBottom: 12,
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontFamily: 'Inter, sans-serif',
          fontWeight: 400,
          fontSize: 24,
          color: BRAND.bodyText,
          lineHeight: 1.6,
          maxWidth: 900,
        }}
      >
        {body}
      </div>
      {!isLast && (
        <div
          style={{
            width: 2,
            height: 40,
            backgroundColor: BRAND.warmGrey,
            opacity: 0.4,
            margin: '24px 0 24px 16px',
          }}
        />
      )}
    </div>
  );
};

export const HowItWorksScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.offWhite}}>
      <div
        style={{
          position: 'absolute',
          top: 180,
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
          <EyebrowLabel text="HOW IT WORKS" />
        </div>

        <div
          style={{
            marginTop: 30,
            marginBottom: 80,
            opacity: interpolate(frame, [0.2 * fps, 0.7 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 60,
            color: BRAND.charcoal,
            letterSpacing: '-0.02em',
            lineHeight: 1.15,
          }}
        >
          Set it.{'\n'}Forget it.{'\n'}Get paid.
        </div>

        <Step
          title="Connect"
          body="Link your solar, battery, or EV. Brand-agnostic — Fronius, Enphase, Tesla, GoodWe, Sigenergy. One app, every asset."
          delay={1.5}
        />
        <Step
          title="Optimise"
          body="The Auto-Arb engine charges when power is cheapest, discharges at peak rates. Comfort guardrails protect your household."
          delay={3}
        />
        <Step
          title="Earn"
          body="No babysitting. No watching wholesale prices. Clear reports show what you earned. Always net positive."
          delay={4.5}
          isLast
        />
      </div>

      <div
        style={{
          position: 'absolute',
          bottom: 100,
          left: 80,
          right: 80,
          opacity: interpolate(frame, [6 * fps, 6.5 * fps], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
        }}
      >
        <div
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 16,
            color: BRAND.warmGrey,
            letterSpacing: '0.02em',
            textAlign: 'center',
          }}
        >
          Fronius · Enphase · GoodWe · Sigenergy · Tesla · BYD · Zappi · Wallbox
        </div>
        <div
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 14,
            color: BRAND.warmGrey,
            opacity: 0.6,
            textAlign: 'center',
            marginTop: 8,
          }}
        >
          Modbus TCP · MQTT · Local API — no forced cloud
        </div>
      </div>
    </AbsoluteFill>
  );
};
