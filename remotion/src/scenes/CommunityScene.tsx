import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../brand';
import {EyebrowLabel} from '../components/EyebrowLabel';

export const CommunityScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const statProgress = interpolate(
    frame,
    [2 * fps, 3 * fps],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.offWhite}}>
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
          <EyebrowLabel text="STRONGER TOGETHER" />
        </div>

        <div
          style={{
            marginTop: 30,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 60,
            color: BRAND.charcoal,
            letterSpacing: '-0.02em',
            lineHeight: 1.15,
            opacity: interpolate(frame, [0.3 * fps, 0.8 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          Energy is better when it's local.
        </div>

        {/* Social norming display */}
        <div
          style={{
            marginTop: 100,
            padding: 50,
            backgroundColor: BRAND.charcoal,
            borderRadius: 8,
            opacity: interpolate(frame, [1.5 * fps, 2 * fps], [0, 1], {
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
              marginBottom: 30,
              letterSpacing: '0.08em',
              textTransform: 'uppercase' as const,
            }}
          >
            HOW'S YOUR STREET DOING?
          </div>

          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 26,
              color: BRAND.white,
              marginBottom: 20,
            }}
          >
            Your street averaged{' '}
            <span style={{fontFamily: 'JetBrains Mono, monospace', color: BRAND.amber, fontWeight: 600}}>
              ${Math.round(38 * statProgress)}
            </span>
            /month
          </div>
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 32,
              color: BRAND.white,
              fontWeight: 600,
              marginBottom: 20,
            }}
          >
            You earned{' '}
            <span style={{fontFamily: 'JetBrains Mono, monospace', color: BRAND.amber, fontSize: 40}}>
              ${Math.round(52 * statProgress)}
            </span>
            {' — '}
            <span style={{color: BRAND.tealLight}}>Top 15%</span>
          </div>

          {/* Streak dots */}
          <div style={{display: 'flex', alignItems: 'center', gap: 10, marginTop: 30}}>
            <span
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 18,
                color: BRAND.warmGrey,
              }}
            >
              Grid events responded:
            </span>
            {Array.from({length: 8}).map((_, i) => {
              const dotOpacity = interpolate(
                frame,
                [(2.5 + i * 0.15) * fps, (2.7 + i * 0.15) * fps],
                [0, 1],
                {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
              );
              return (
                <div
                  key={i}
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: 8,
                    backgroundColor: BRAND.amber,
                    opacity: dotOpacity,
                  }}
                />
              );
            })}
          </div>
        </div>

        {/* Features */}
        <div
          style={{
            marginTop: 60,
            display: 'flex',
            flexDirection: 'column',
            gap: 30,
            opacity: interpolate(frame, [4 * fps, 4.5 * fps], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          {[
            {title: 'Grid Events', body: '87% of your street participated — will you?'},
            {title: 'Seasonal Challenges', body: 'Winter Flex: can your street beat last year?'},
          ].map((feat, i) => (
            <div key={i} style={{borderTop: `3px solid ${BRAND.amber}`, paddingTop: 16}}>
              <div style={{fontFamily: 'Inter, sans-serif', fontWeight: 600, fontSize: 26, color: BRAND.charcoal}}>
                {feat.title}
              </div>
              <div style={{fontFamily: 'Inter, sans-serif', fontSize: 22, color: BRAND.bodyText, marginTop: 8}}>
                {feat.body}
              </div>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
