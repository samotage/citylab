import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

const CostCard: React.FC<{
  leftLabel: string;
  leftValue: string;
  leftColor: string;
  rightLabel: string;
  rightValue: string;
  rightColor: string;
  caption: string;
  delay: number;
}> = ({leftLabel, leftValue, leftColor, rightLabel, rightValue, rightColor, caption, delay}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const opacity = interpolate(frame, [delay * fps, (delay + 0.5) * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slideX = interpolate(frame, [delay * fps, (delay + 0.5) * fps], [40, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const dividerWidth = interpolate(
    frame,
    [(delay + 0.5) * fps, (delay + 1) * fps],
    [0, 4],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  return (
    <div
      style={{
        opacity,
        transform: `translateX(${slideX}px)`,
        display: 'flex',
        alignItems: 'stretch',
        backgroundColor: BRAND.charcoalLight,
        borderRadius: 8,
        overflow: 'hidden',
        marginBottom: 30,
      }}
    >
      {/* Left side — what you have */}
      <div
        style={{
          flex: 1,
          padding: '36px 40px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 14,
            color: BRAND.warmGrey,
            letterSpacing: '0.1em',
            textTransform: 'uppercase' as const,
            marginBottom: 12,
          }}
        >
          {leftLabel}
        </div>
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 32,
            color: leftColor,
          }}
        >
          {leftValue}
        </div>
      </div>

      {/* Amber divider */}
      <div
        style={{
          width: dividerWidth,
          backgroundColor: BRAND.amber,
          alignSelf: 'stretch',
        }}
      />

      {/* Right side — what you pay */}
      <div
        style={{
          flex: 1,
          padding: '36px 40px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 14,
            color: BRAND.warmGrey,
            letterSpacing: '0.1em',
            textTransform: 'uppercase' as const,
            marginBottom: 12,
          }}
        >
          {rightLabel}
        </div>
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 32,
            color: rightColor,
          }}
        >
          {rightValue}
        </div>
      </div>

      {/* Caption */}
      <div
        style={{
          position: 'absolute',
          bottom: -24,
          right: 0,
          fontFamily: 'Inter, sans-serif',
          fontSize: 18,
          color: BRAND.warmGrey,
          fontStyle: 'italic',
          opacity: interpolate(
            frame,
            [(delay + 1.5) * fps, (delay + 2) * fps],
            [0, 0.7],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
          ),
        }}
      >
        {caption}
      </div>
    </div>
  );
};

export const AgitateScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const eyebrowOpacity = interpolate(frame, [0, 0.4 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const punchlineOpacity = interpolate(
    frame,
    [28 * fps, 29 * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

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
        <div
          style={{
            opacity: eyebrowOpacity,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 18,
            fontWeight: 500,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color: BRAND.amber,
            marginBottom: 40,
          }}
        >
          THE COST OF BEING LOCKED
        </div>

        <div style={{position: 'relative'}}>
          <CostCard
            leftLabel="HOME BATTERY"
            leftValue="Full in the garage"
            leftColor={BRAND.teal}
            rightLabel="JOB SITE"
            rightValue="Diesel: $0.50/kWh"
            rightColor={BRAND.amber}
            caption="The tradie's dilemma"
            delay={2}
          />
          <CostCard
            leftLabel="HOME PANELS"
            leftValue="Exporting for 8c/kWh"
            leftColor={BRAND.teal}
            rightLabel="HIGHWAY CHARGER"
            rightValue="Paying 80c/kWh"
            rightColor={BRAND.amber}
            caption="The family road trip"
            delay={12}
          />
          <CostCard
            leftLabel="YOUR ROOF"
            leftValue="Overproducing daily"
            leftColor={BRAND.teal}
            rightLabel="MUM'S FLAT"
            rightValue="Struggling with bills"
            rightColor={BRAND.amber}
            caption="Across town, no connection"
            delay={22}
          />
        </div>

        <div
          style={{
            marginTop: 50,
            opacity: punchlineOpacity,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 600,
            fontSize: 36,
            color: BRAND.white,
            textAlign: 'center',
          }}
        >
          The value is there.{' '}
          <span style={{color: BRAND.amber}}>The connection isn't.</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
