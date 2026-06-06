import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

export const BusinessModelScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const eyebrowOpacity = interpolate(frame, [0, 0.4 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const headlineOpacity = interpolate(frame, [0.5 * fps, 1 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Sankey flow blocks
  const solarBlock = interpolate(frame, [2 * fps, 2.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const arrowOne = interpolate(frame, [3 * fps, 3.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const citEtherBlock = interpolate(frame, [3.5 * fps, 4 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const arrowTwo = interpolate(frame, [4.5 * fps, 5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const destBlock = interpolate(frame, [5 * fps, 5.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // T&D fee layer
  const feeOpacity = interpolate(frame, [6 * fps, 7 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Punchline
  const punchline = interpolate(frame, [8 * fps, 9 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Revenue items
  const rev1 = interpolate(frame, [9.5 * fps, 10 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const rev2 = interpolate(frame, [10.5 * fps, 11 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
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
          THE MODEL
        </div>
        <div
          style={{
            opacity: headlineOpacity,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 48,
            color: BRAND.charcoal,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: 60,
          }}
        >
          We're not pretending the grid is free.
        </div>

        {/* Horizontal Sankey flow */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 0,
            marginBottom: 40,
          }}
        >
          {/* Solar */}
          <div
            style={{
              opacity: solarBlock,
              transform: `scale(${interpolate(solarBlock, [0, 1], [0.9, 1])})`,
              backgroundColor: BRAND.amber,
              borderRadius: 8,
              padding: '28px 36px',
              textAlign: 'center',
              minWidth: 200,
            }}
          >
            <div style={{fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: BRAND.charcoal, letterSpacing: '0.1em', marginBottom: 6}}>
              YOUR SOLAR
            </div>
            <div style={{fontFamily: 'Inter, sans-serif', fontSize: 22, fontWeight: 600, color: BRAND.charcoal}}>
              Generates credits
            </div>
          </div>

          {/* Arrow */}
          <div style={{opacity: arrowOne, padding: '0 16px'}}>
            <span style={{fontSize: 32, color: BRAND.charcoalLight}}>→</span>
          </div>

          {/* citEther */}
          <div
            style={{
              opacity: citEtherBlock,
              transform: `scale(${interpolate(citEtherBlock, [0, 1], [0.9, 1])})`,
              backgroundColor: BRAND.charcoal,
              borderRadius: 8,
              padding: '28px 36px',
              textAlign: 'center',
              minWidth: 240,
              position: 'relative',
            }}
          >
            <div style={{fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: BRAND.amber, letterSpacing: '0.1em', marginBottom: 6}}>
              CITETHER
            </div>
            <div style={{fontFamily: 'Inter, sans-serif', fontSize: 22, fontWeight: 600, color: BRAND.white}}>
              Settles across the grid
            </div>
            {/* T&D fee strip */}
            <div
              style={{
                position: 'absolute',
                bottom: -30,
                left: '10%',
                right: '10%',
                opacity: feeOpacity,
                backgroundColor: BRAND.warmGrey,
                borderRadius: 4,
                padding: '6px 12px',
                textAlign: 'center',
              }}
            >
              <span style={{fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: BRAND.white, letterSpacing: '0.08em'}}>
                T&D NETWORK FEES DEDUCTED
              </span>
            </div>
          </div>

          {/* Arrow */}
          <div style={{opacity: arrowTwo, padding: '0 16px'}}>
            <span style={{fontSize: 32, color: BRAND.charcoalLight}}>→</span>
          </div>

          {/* Destinations */}
          <div
            style={{
              opacity: destBlock,
              transform: `scale(${interpolate(destBlock, [0, 1], [0.9, 1])})`,
              backgroundColor: BRAND.teal,
              borderRadius: 8,
              padding: '28px 36px',
              textAlign: 'center',
              minWidth: 220,
            }}
          >
            <div style={{fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: BRAND.white, letterSpacing: '0.1em', opacity: 0.8, marginBottom: 6}}>
              NET VALUE
            </div>
            <div style={{fontFamily: 'Inter, sans-serif', fontSize: 22, fontWeight: 600, color: BRAND.white}}>
              Delivered to you
            </div>
          </div>
        </div>

        {/* Punchline + revenue */}
        <div style={{marginTop: 70}}>
          <div
            style={{
              opacity: punchline,
              fontFamily: 'Inter, sans-serif',
              fontWeight: 700,
              fontSize: 32,
              color: BRAND.charcoal,
              textAlign: 'center',
              marginBottom: 40,
            }}
          >
            Net value after network costs{' '}
            <span style={{color: BRAND.amber}}>still beats zero FiT.</span>
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 60,
            }}
          >
            <div style={{opacity: rev1, textAlign: 'center'}}>
              <div style={{fontFamily: 'JetBrains Mono, monospace', fontSize: 14, color: BRAND.teal, letterSpacing: '0.08em', marginBottom: 8}}>
                REVENUE
              </div>
              <div style={{fontFamily: 'Inter, sans-serif', fontSize: 20, color: BRAND.bodyText}}>
                Margin on net value created
              </div>
            </div>
            <div style={{opacity: rev2, textAlign: 'center'}}>
              <div style={{fontFamily: 'JetBrains Mono, monospace', fontSize: 14, color: BRAND.teal, letterSpacing: '0.08em', marginBottom: 8}}>
                NETWORK BENEFIT
              </div>
              <div style={{fontFamily: 'Inter, sans-serif', fontSize: 20, color: BRAND.bodyText}}>
                Pod energy = lower T&D charges
              </div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
