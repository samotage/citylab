import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

const techStack = [
  {label: 'Live NEM Data', desc: '5-min price + demand ingestion', color: BRAND.amber},
  {label: 'Arbitrage Engine', desc: 'Battery charge/discharge optimiser', color: BRAND.teal},
  {label: 'Settlement Layer', desc: 'Location-independent credits', color: BRAND.amber},
  {label: 'Grid Inertia', desc: 'RoCoF + frequency tracking', color: BRAND.teal},
];

const builtItems = [
  'Real-time price signals across VIC1',
  'Grid inertia + demand response engine',
  'Auto-Arb orchestration layer',
  'Follow Me Power settlement infrastructure',
];

export const EvidenceCtaScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phase 1: Evidence (0-7s)
  const evidenceEyebrow = interpolate(frame, [0, 0.4 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const evidenceHeadline = interpolate(frame, [0.5 * fps, 1.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const whitespaceCall = interpolate(frame, [4.5 * fps, 5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const evidenceFade = interpolate(frame, [6.5 * fps, 7.5 * fps], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 2: CTA (7-14s)
  const ctaOpacity = interpolate(frame, [7 * fps, 8 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaPilot = interpolate(frame, [8 * fps, 8.4 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaSuburb = interpolate(frame, [8.8 * fps, 9.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaHouseholds = interpolate(frame, [9.6 * fps, 10 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaMonths = interpolate(frame, [10.4 * fps, 10.8 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaSupportLine = interpolate(frame, [11.2 * fps, 12 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaAsk = interpolate(frame, [12.5 * fps, 13 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const appsOpacity = interpolate(frame, [3 * fps, 3.8 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.03} />

      {/* Phase 1: Evidence — left side */}
      <div
        style={{
          position: 'absolute',
          top: 60,
          left: 100,
          width: 850,
          zIndex: 1,
          opacity: evidenceFade,
        }}
      >
        <div style={{opacity: evidenceEyebrow}}>
          <div
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 18,
              fontWeight: 500,
              letterSpacing: '0.12em',
              textTransform: 'uppercase' as const,
              color: BRAND.amber,
              marginBottom: 16,
            }}
          >
            BUILT AT THIS HACKATHON
          </div>
        </div>
        <div
          style={{
            opacity: evidenceHeadline,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 44,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: 28,
          }}
        >
          The intelligence layer is{' '}
          <span style={{color: BRAND.amber}}>working.</span>
        </div>

        {/* Tech stack cards — 2x2 */}
        <div style={{display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24}}>
          {techStack.map((item, i) => {
            const delay = 1.2 + i * 0.4;
            const cardOpacity = interpolate(
              frame,
              [delay * fps, (delay + 0.35) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            return (
              <div
                key={i}
                style={{
                  opacity: cardOpacity,
                  border: `1px solid ${item.color}50`,
                  borderLeft: `3px solid ${item.color}`,
                  borderRadius: 6,
                  padding: '14px 20px',
                  flex: '1 1 180px',
                  maxWidth: '48%',
                  backgroundColor: `${BRAND.charcoalLight}40`,
                }}
              >
                <div
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 13,
                    color: item.color,
                    letterSpacing: '0.08em',
                    marginBottom: 4,
                  }}
                >
                  {item.label}
                </div>
                <div
                  style={{
                    fontFamily: 'Inter, sans-serif',
                    fontSize: 15,
                    color: BRAND.warmGrey,
                  }}
                >
                  {item.desc}
                </div>
              </div>
            );
          })}
        </div>

        {/* Built items checklist */}
        <div style={{marginBottom: 24}}>
          {builtItems.map((item, i) => {
            const delay = 2.8 + i * 0.3;
            const itemOpacity = interpolate(
              frame,
              [delay * fps, (delay + 0.3) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            return (
              <div
                key={i}
                style={{
                  opacity: itemOpacity,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  marginBottom: 8,
                }}
              >
                <div
                  style={{
                    width: 20,
                    height: 20,
                    borderRadius: 4,
                    backgroundColor: BRAND.teal,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 13,
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
                    fontSize: 16,
                    color: BRAND.white,
                    fontWeight: 400,
                  }}
                >
                  {item}
                </span>
              </div>
            );
          })}
        </div>

        <div
          style={{
            opacity: whitespaceCall,
            fontFamily: 'Inter, sans-serif',
            fontSize: 22,
            color: BRAND.white,
            fontWeight: 600,
            lineHeight: 1.5,
          }}
        >
          No one else in this market is doing
          <br />
          <span style={{color: BRAND.teal}}>
            location-independent consumer settlement.
          </span>
        </div>
      </div>

      {/* App screenshots strip (evidence phase) */}
      <div
        style={{
          position: 'absolute',
          right: 60,
          top: '50%',
          transform: 'translateY(-50%)',
          opacity: appsOpacity * evidenceFade,
          display: 'flex',
          gap: 14,
          zIndex: 1,
        }}
      >
        {['app-home.png', 'app-follow-me.png', 'app-earnings.png'].map((img, i) => (
          <div
            key={i}
            style={{
              width: 150,
              height: 320,
              borderRadius: 20,
              border: `2px solid ${BRAND.charcoalLight}`,
              overflow: 'hidden',
              opacity: interpolate(
                frame,
                [(3.2 + i * 0.4) * fps, (3.6 + i * 0.4) * fps],
                [0, 1],
                {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
              ),
            }}
          >
            <Img
              src={staticFile(img)}
              style={{width: '100%', height: 'auto'}}
            />
          </div>
        ))}
      </div>

      {/* Phase 2: CTA — centered */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          opacity: ctaOpacity,
          zIndex: 2,
        }}
      >
        {/* Pilot ask — staggered reveal */}
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 60,
            color: BRAND.white,
            textAlign: 'center',
            letterSpacing: '-0.02em',
            lineHeight: 1.3,
            marginBottom: 40,
          }}
        >
          <span style={{opacity: ctaPilot}}>One pilot.</span>
          {'  '}
          <span style={{opacity: ctaSuburb}}>One suburb.</span>
          <br />
          <span style={{opacity: ctaHouseholds, color: BRAND.amber}}>
            100 households.
          </span>
          {'  '}
          <span style={{opacity: ctaMonths}}>Three months.</span>
        </div>

        {/* Supporting evidence line */}
        <div
          style={{
            opacity: ctaSupportLine,
            fontFamily: 'Inter, sans-serif',
            fontSize: 24,
            color: BRAND.warmGrey,
            textAlign: 'center',
            lineHeight: 1.6,
            maxWidth: 900,
            marginBottom: 40,
          }}
        >
          We prove the model works — behind the meter, across the network,
          <br />
          with real people earning real value in real places.
        </div>

        {/* The ask — amber bar */}
        <div
          style={{
            opacity: ctaAsk,
            transform: `translateY(${interpolate(ctaAsk, [0, 1], [12, 0])}px)`,
            backgroundColor: BRAND.amber,
            padding: '18px 48px',
            borderRadius: 6,
            marginBottom: 12,
          }}
        >
          <span
            style={{
              fontFamily: 'Inter, sans-serif',
              fontWeight: 600,
              fontSize: 22,
              color: BRAND.charcoal,
            }}
          >
            That's the ask.
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
