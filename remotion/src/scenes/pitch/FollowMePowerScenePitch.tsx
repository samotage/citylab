import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';
import {Wordmark} from '../../components/Wordmark';

export const FollowMePowerScenePitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phase 1: Follow Me Power intro (0-10s)
  const eyebrowOpacity = interpolate(frame, [0, 0.5 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const headlineOpacity = interpolate(frame, [0.6 * fps, 1.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const subheadOpacity = interpolate(frame, [1.5 * fps, 2.2 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 2: The applause line (10-16s)
  const punchlineOpacity = interpolate(frame, [8 * fps, 9 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const punchlineScale = interpolate(frame, [8 * fps, 9.5 * fps], [0.95, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const dividerWidth = interpolate(frame, [9 * fps, 10 * fps], [0, 500], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 3: Account visual (14-22s)
  const accountOpacity = interpolate(frame, [14 * fps, 15 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Map flow lines animation
  const flowProgress = interpolate(frame, [15 * fps, 20 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.03} />

      {/* Left: text content */}
      <div
        style={{
          position: 'absolute',
          top: 120,
          left: 120,
          width: 800,
          zIndex: 1,
        }}
      >
        <div style={{opacity: eyebrowOpacity}}>
          <div
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 20,
              fontWeight: 600,
              letterSpacing: '0.12em',
              textTransform: 'uppercase' as const,
              color: BRAND.amber,
            }}
          >
            FOLLOW ME POWER
          </div>
        </div>

        <div
          style={{
            marginTop: 40,
            opacity: headlineOpacity,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 64,
            color: BRAND.white,
            letterSpacing: '-0.03em',
            lineHeight: 1.15,
          }}
        >
          Your energy follows you.
        </div>

        <div
          style={{
            marginTop: 20,
            opacity: subheadOpacity,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 300,
            fontSize: 28,
            color: BRAND.warmGrey,
            lineHeight: 1.5,
          }}
        >
          Wherever you plug in, wherever you consume,
          <br />
          wherever you need power.
        </div>

        {/* The applause line */}
        <div
          style={{
            marginTop: 80,
            opacity: punchlineOpacity,
            transform: `scale(${punchlineScale})`,
          }}
        >
          <div
            style={{
              width: dividerWidth,
              height: 2,
              backgroundColor: BRAND.amber,
              marginBottom: 30,
            }}
          />
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontWeight: 700,
              fontSize: 42,
              color: BRAND.white,
              lineHeight: 1.4,
            }}
          >
            The grid is the wire.
            <br />
            <span style={{color: BRAND.teal}}>citEther is the settlement.</span>
          </div>
          <div
            style={{
              marginTop: 24,
              fontFamily: 'Inter, sans-serif',
              fontSize: 22,
              color: BRAND.warmGrey,
              lineHeight: 1.5,
            }}
          >
            Your energy account is no longer tied to your meter. It's tied to{' '}
            <span style={{color: BRAND.amber, fontWeight: 600}}>you</span>.
          </div>
        </div>
      </div>

      {/* Right: simplified map with flow lines */}
      <div
        style={{
          position: 'absolute',
          right: 80,
          top: '50%',
          transform: 'translateY(-50%)',
          opacity: accountOpacity,
          zIndex: 1,
        }}
      >
        <svg width={600} height={500} viewBox="0 0 600 500">
          {/* Central account node */}
          <circle
            cx={300}
            cy={250}
            r={40}
            fill={BRAND.amber}
            opacity={0.9}
          />
          <text
            x={300}
            y={255}
            textAnchor="middle"
            fill={BRAND.charcoal}
            fontFamily="JetBrains Mono, monospace"
            fontSize={12}
            fontWeight={600}
          >
            YOU
          </text>

          {/* Destination nodes with animated connections */}
          {[
            {x: 100, y: 80, label: 'HOME', color: BRAND.teal},
            {x: 500, y: 80, label: 'JOB SITE', color: BRAND.teal},
            {x: 80, y: 400, label: "MUM'S", color: BRAND.teal},
            {x: 520, y: 400, label: 'EV', color: BRAND.teal},
            {x: 300, y: 60, label: 'UNI', color: BRAND.tealLight},
            {x: 300, y: 440, label: 'HOLIDAY', color: BRAND.tealLight},
          ].map((node, i) => {
            const nodeDelay = 0.3 * i;
            const nodeProgress = interpolate(
              flowProgress,
              [nodeDelay / 2, (nodeDelay + 0.5) / 2],
              [0, 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const dashOffset = interpolate(nodeProgress, [0, 1], [200, 0]);
            return (
              <React.Fragment key={i}>
                <line
                  x1={300}
                  y1={250}
                  x2={node.x}
                  y2={node.y}
                  stroke={BRAND.amber}
                  strokeWidth={2}
                  strokeDasharray="8 4"
                  strokeDashoffset={dashOffset}
                  opacity={nodeProgress * 0.6}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={28}
                  fill={node.color}
                  opacity={nodeProgress}
                />
                <text
                  x={node.x}
                  y={node.y + 4}
                  textAnchor="middle"
                  fill={BRAND.white}
                  fontFamily="JetBrains Mono, monospace"
                  fontSize={9}
                  fontWeight={500}
                >
                  {node.label}
                </text>
              </React.Fragment>
            );
          })}
        </svg>
      </div>
    </AbsoluteFill>
  );
};
