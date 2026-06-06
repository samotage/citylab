import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {BRAND} from '../../brand';
import {GridPattern} from '../../components/GridPattern';

const SD = 12;
const TD = 0.5;
const PHONE_W = 380;
const PHONE_H = 780;
const NUM_SCREENS = 5;

const screens = [
  {
    src: 'app-home.png',
    label: 'HOME',
    labelColor: BRAND.amber,
    panY: [0, 0] as const,
    glowColor: BRAND.amber,
    callouts: [
      {text: '$47.21 earned today', sub: "FiT would've paid $3.80", delay: 2, color: BRAND.amber},
      {text: 'Live transfer in progress', sub: 'Your Home → Job Site, saving $0.35/kWh vs diesel', delay: 6, color: BRAND.teal},
    ],
  },
  {
    src: 'app-follow-me.png',
    label: 'FOLLOW ME',
    labelColor: BRAND.amber,
    panY: [0, 0] as const,
    glowColor: BRAND.amber,
    callouts: [
      {text: 'Real-time NEM price map', sub: '$35 to $80/hr across Melbourne', delay: 14, color: BRAND.amber},
      {text: 'Six Follow Me scenarios', sub: "Job site, parent's flat, EV, uni, holiday, business", delay: 18, color: BRAND.teal},
    ],
  },
  {
    src: 'app-earnings.png',
    label: 'EARNINGS',
    labelColor: BRAND.teal,
    panY: [0, -30] as const,
    glowColor: BRAND.teal,
    callouts: [
      {text: '$216 this month', sub: 'Five revenue streams, +18% vs last period', delay: 26, color: BRAND.amber},
      {text: '12× more than feed-in tariff', sub: 'FiT pays $3.80 — citEther earns $47.24 per day', delay: 30, color: BRAND.teal},
    ],
  },
  {
    src: 'app-settings.png',
    label: 'AUTO-ARB',
    labelColor: BRAND.amber,
    panY: [0, -120] as const,
    glowColor: BRAND.amber,
    callouts: [
      {text: 'Full DER stack connected', sub: 'Solar, Powerwall, EV, HVAC, hot water', delay: 38, color: BRAND.amber},
      {text: 'Set it. Forget it.', sub: 'Comfort floor, battery floor, dispatch aggression', delay: 42, color: BRAND.teal},
    ],
  },
  {
    src: 'app-my-pod.png',
    label: 'MY POD',
    labelColor: BRAND.teal,
    panY: [0, -20] as const,
    glowColor: BRAND.teal,
    callouts: [
      {text: 'Maple Ave Pod — 14 households', sub: '62 kW solar, self-supplied 73% today', delay: 50, color: BRAND.teal},
      {text: 'Social norming leaderboard', sub: "You're #3 at $52 vs Pod average $38", delay: 54, color: BRAND.amber},
    ],
  },
];

export const AppDemoWalkthroughPitch: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const scrollInput: number[] = [0];
  const scrollOutput: number[] = [0];
  for (let i = 1; i < NUM_SCREENS; i++) {
    scrollInput.push(i * SD * fps);
    scrollOutput.push(i - 1);
    scrollInput.push((i * SD + TD) * fps);
    scrollOutput.push(i);
  }
  scrollInput.push(NUM_SCREENS * SD * fps);
  scrollOutput.push(NUM_SCREENS - 1);

  const scroll = interpolate(frame, scrollInput, scrollOutput, {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const phoneEntrance = interpolate(frame, [0, 1.2 * fps], [80, 0], {
    extrapolateRight: 'clamp',
  });
  const phoneOpacity = interpolate(frame, [0, 0.8 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const textEntrance = interpolate(frame, [0.3 * fps, 1 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const activeIdx = Math.min(Math.round(scroll), NUM_SCREENS - 1);

  return (
    <AbsoluteFill style={{backgroundColor: BRAND.charcoal}}>
      <GridPattern opacity={0.02} />

      {/* Left: eyebrow + label + callouts */}
      <div
        style={{
          position: 'absolute',
          top: 100,
          left: 100,
          width: 700,
          opacity: textEntrance,
          zIndex: 2,
        }}
      >
        <div
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 20,
            fontWeight: 500,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color: BRAND.amber,
            marginBottom: 12,
          }}
        >
          LIVE PRODUCT DEMO
        </div>
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontWeight: 700,
            fontSize: 52,
            color: BRAND.white,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: 60,
          }}
        >
          {screens[activeIdx].label}
          <span style={{color: screens[activeIdx].labelColor}}>.</span>
        </div>

        {/* Callout cards — each screen's group positioned absolutely */}
        <div style={{position: 'relative', height: 280}}>
          {screens.map((screen, sIdx) =>
            screen.callouts.map((c, cIdx) => {
              const fadeIn = interpolate(
                frame,
                [c.delay * fps, (c.delay + 0.4) * fps],
                [0, 1],
                {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
              );
              const fadeOut =
                sIdx === NUM_SCREENS - 1
                  ? 1
                  : interpolate(
                      frame,
                      [((sIdx + 1) * SD - 0.5) * fps, ((sIdx + 1) * SD) * fps],
                      [1, 0],
                      {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
                    );
              const opacity = fadeIn * fadeOut;
              if (opacity < 0.01) return null;

              const slideX = interpolate(fadeIn, [0, 1], [20, 0]);

              return (
                <div
                  key={`${sIdx}-${cIdx}`}
                  style={{
                    position: 'absolute',
                    top: cIdx * 110,
                    left: 0,
                    right: 0,
                    opacity,
                    transform: `translateX(${slideX}px)`,
                    padding: '16px 20px',
                    backgroundColor: `${BRAND.charcoalLight}80`,
                    borderRadius: 8,
                    borderLeft: `3px solid ${c.color}`,
                  }}
                >
                  <div
                    style={{
                      fontFamily: 'Inter, sans-serif',
                      fontSize: 28,
                      fontWeight: 600,
                      color: BRAND.white,
                      lineHeight: 1.3,
                      marginBottom: 4,
                    }}
                  >
                    {c.text}
                  </div>
                  <div
                    style={{
                      fontFamily: 'Inter, sans-serif',
                      fontSize: 20,
                      color: BRAND.warmGrey,
                      lineHeight: 1.4,
                    }}
                  >
                    {c.sub}
                  </div>
                </div>
              );
            }),
          )}
        </div>
      </div>

      {/* Right: phone mockup */}
      <div
        style={{
          position: 'absolute',
          right: 140,
          top: '50%',
          transform: `translateY(calc(-50% + ${phoneEntrance}px))`,
          opacity: phoneOpacity,
          zIndex: 1,
        }}
      >
        <div
          style={{
            width: PHONE_W,
            height: PHONE_H,
            borderRadius: 40,
            border: `3px solid ${BRAND.charcoalLight}`,
            overflow: 'hidden',
            backgroundColor: '#1a1a1a',
            boxShadow: `0 20px 60px rgba(0,0,0,0.5), 0 0 40px ${screens[activeIdx].glowColor}15`,
            position: 'relative',
          }}
        >
          {/* Notch */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 140,
              height: 28,
              backgroundColor: '#1a1a1a',
              borderBottomLeftRadius: 16,
              borderBottomRightRadius: 16,
              zIndex: 10,
            }}
          />

          {/* Notification toast — Home screen only */}
          {(() => {
            const toastY = interpolate(
              frame,
              [4 * fps, 4.5 * fps, 8 * fps, 8.5 * fps],
              [-60, 32, 32, -60],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            const toastOpacity = interpolate(
              frame,
              [4 * fps, 4.3 * fps, 8 * fps, 8.5 * fps],
              [0, 1, 1, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            );
            if (toastOpacity < 0.01) return null;
            return (
              <div
                style={{
                  position: 'absolute',
                  top: toastY,
                  left: 12,
                  right: 12,
                  backgroundColor: 'rgba(60, 60, 60, 0.95)',
                  borderRadius: 12,
                  padding: '10px 14px',
                  zIndex: 5,
                  opacity: toastOpacity,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 6,
                    backgroundColor: BRAND.amber,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 14,
                    flexShrink: 0,
                  }}
                >
                  ⚡
                </div>
                <div>
                  <div
                    style={{
                      fontFamily: 'Inter, sans-serif',
                      fontSize: 14,
                      fontWeight: 600,
                      color: BRAND.white,
                    }}
                  >
                    citEther
                  </div>
                  <div
                    style={{
                      fontFamily: 'Inter, sans-serif',
                      fontSize: 13,
                      color: BRAND.warmGrey,
                    }}
                  >
                    Solar credits applied to Mum's flat — $2.40 saved
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Screen content */}
          <div
            style={{
              width: '100%',
              height: '100%',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            {screens.map((screen, i) => {
              const screenX = (i - scroll) * PHONE_W;
              if (Math.abs(screenX) > PHONE_W * 1.5) return null;

              const progress = interpolate(
                frame,
                [i * SD * fps, (i + 1) * SD * fps],
                [0, 1],
                {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
              );
              const scale = 1 + 0.12 * progress;
              const panY =
                screen.panY[0] + (screen.panY[1] - screen.panY[0]) * progress;

              return (
                <div
                  key={i}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    transform: `translateX(${screenX}px)`,
                    overflow: 'hidden',
                  }}
                >
                  <Img
                    src={staticFile(screen.src)}
                    style={{
                      width: '100%',
                      height: 'auto',
                      transform: `scale(${scale}) translateY(${panY}px)`,
                      transformOrigin: 'top center',
                    }}
                  />
                </div>
              );
            })}
          </div>
        </div>

        {/* Pagination dots */}
        <div
          style={{
            display: 'flex',
            gap: 8,
            justifyContent: 'center',
            marginTop: 16,
          }}
        >
          {screens.map((_, i) => {
            const dist = Math.abs(i - scroll);
            const dotW = interpolate(dist, [0, 0.5, 1], [24, 12, 6], {
              extrapolateRight: 'clamp',
            });
            const dotColor =
              dist < 0.5 ? screens[i].labelColor : BRAND.charcoalLight;
            return (
              <div
                key={i}
                style={{
                  width: dotW,
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: dotColor,
                }}
              />
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
