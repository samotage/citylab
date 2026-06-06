import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../../brand';
import {Wordmark} from '../../components/Wordmark';
import {GridPattern} from '../../components/GridPattern';

const techStack = [
  {label: 'Live NEM Data', desc: 'Real-time price signals', color: BRAND.amber},
  {label: 'Arbitrage Engine', desc: 'Auto-Arb optimisation', color: BRAND.teal},
  {label: 'Settlement Layer', desc: 'Follow Me Power backbone', color: BRAND.amber},
  {label: 'Grid Inertia', desc: 'Demand response tracking', color: BRAND.teal},
];

export const EvidenceCtaScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phase 1: Evidence (0-8s)
  const evidenceEyebrow = interpolate(frame, [0, 0.4 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const evidenceHeadline = interpolate(frame, [0.5 * fps, 1.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const whitespaceCall = interpolate(frame, [5 * fps, 5.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 2: CTA (8-16s)
  const ctaOpacity = interpolate(frame, [8 * fps, 9 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaLine1 = interpolate(frame, [9 * fps, 9.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaLine2 = interpolate(frame, [10 * fps, 10.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaLine3 = interpolate(frame, [11 * fps, 11.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaButton = interpolate(frame, [13 * fps, 14 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Small app screenshots in a row (evidence)
  const appsOpacity = interpolate(frame, [3 * fps, 4 * fps], [0, 1], {
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
          top: 80,
          left: 120,
          width: 800,
          zIndex: 1,
          opacity: interpolate(frame, [7 * fps, 8.5 * fps], [1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
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
              marginBottom: 20,
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
            fontSize: 48,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: 40,
          }}
        >
          The intelligence layer is{' '}
          <span style={{color: BRAND.amber}}>working.</span>
        </div>

        {/* Tech stack cards */}
        <div style={{display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 40}}>
          {techStack.map((item, i) => {
            const delay = 1.5 + i * 0.5;
            const cardOpacity = interpolate(
              frame,
              [delay * fps, (delay + 0.4) * fps],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            return (
              <div
                key={i}
                style={{
                  opacity: cardOpacity,
                  border: `1px solid ${item.color}40`,
                  borderRadius: 8,
                  padding: '16px 24px',
                  flex: '1 1 200px',
                }}
              >
                <div
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 14,
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
                    fontSize: 16,
                    color: BRAND.warmGrey,
                  }}
                >
                  {item.desc}
                </div>
              </div>
            );
          })}
        </div>

        <div
          style={{
            opacity: whitespaceCall,
            fontFamily: 'Inter, sans-serif',
            fontSize: 24,
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
          right: 80,
          top: '50%',
          transform: 'translateY(-50%)',
          opacity: appsOpacity * interpolate(frame, [7 * fps, 8.5 * fps], [1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
          display: 'flex',
          gap: 16,
          zIndex: 1,
        }}
      >
        {['app-home.png', 'app-follow-me.png', 'app-earnings.png'].map((img, i) => (
          <div
            key={i}
            style={{
              width: 160,
              height: 340,
              borderRadius: 20,
              border: `2px solid ${BRAND.charcoalLight}`,
              overflow: 'hidden',
              opacity: interpolate(
                frame,
                [(3.5 + i * 0.5) * fps, (4 + i * 0.5) * fps],
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
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 56,
            color: BRAND.white,
            textAlign: 'center',
            letterSpacing: '-0.02em',
            lineHeight: 1.4,
            marginBottom: 60,
          }}
        >
          <span style={{opacity: ctaLine1}}>One suburb.</span>
          {'  '}
          <span style={{opacity: ctaLine2, color: BRAND.amber}}>
            100 households.
          </span>
          {'  '}
          <span style={{opacity: ctaLine3}}>Three months.</span>
        </div>

        <div
          style={{
            opacity: ctaButton,
            transform: `translateY(${interpolate(ctaButton, [0, 1], [15, 0])}px)`,
            backgroundColor: BRAND.amber,
            padding: '20px 50px',
            borderRadius: 6,
            marginBottom: 16,
          }}
        >
          <span
            style={{
              fontFamily: 'Inter, sans-serif',
              fontWeight: 600,
              fontSize: 24,
              color: BRAND.charcoal,
            }}
          >
            Follow Me Power — proven in the real world.
          </span>
        </div>

        <div
          style={{
            opacity: ctaButton,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 16,
            color: BRAND.warmGrey,
            marginTop: 12,
          }}
        >
          That's the ask.
        </div>
      </div>
    </AbsoluteFill>
  );
};
