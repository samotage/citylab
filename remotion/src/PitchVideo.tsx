import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadJetBrainsMono} from '@remotion/google-fonts/JetBrainsMono';
import {BrandRevealPitch} from './scenes/pitch/BrandRevealPitch';
import {ProblemScenePitch} from './scenes/pitch/ProblemScenePitch';
import {AgitateScenePitch} from './scenes/pitch/AgitateScenePitch';
import {AppDemoWalkthroughPitch} from './scenes/pitch/AppDemoWalkthroughPitch';
import {SupportingDataScenePitch} from './scenes/pitch/SupportingDataScenePitch';
import {CtaScenePitch} from './scenes/pitch/CtaScenePitch';

loadInter('normal', {weights: ['300', '400', '600', '700'], subsets: ['latin']});
loadJetBrainsMono('normal', {weights: ['400', '500', '600'], subsets: ['latin']});

export const PitchVideo: React.FC = () => {
  const {fps} = useVideoConfig();

  // 180 seconds total at 30fps = 5400 frames
  // 5 blocks: Problem (30s) | Agitate (30s) | Demo (60s) | Data (30s) | CTA (30s)
  const scenes = [
    {component: BrandRevealPitch, duration: 5},             // 0:00-0:05  ┐
    {component: ProblemScenePitch, duration: 25},            // 0:05-0:30  ┘ PROBLEM
    {component: AgitateScenePitch, duration: 30},            // 0:30-1:00    AGITATE
    {component: AppDemoWalkthroughPitch, duration: 60},      // 1:00-2:00    DEMO
    {component: SupportingDataScenePitch, duration: 30},     // 2:00-2:30    DATA
    {component: CtaScenePitch, duration: 30},                // 2:30-3:00    CTA
  ];

  let currentFrame = 0;

  return (
    <AbsoluteFill>
      {scenes.map((scene, i) => {
        const from = currentFrame;
        const durationInFrames = scene.duration * fps;
        currentFrame += durationInFrames;
        const Scene = scene.component;
        return (
          <Sequence
            key={i}
            from={from}
            durationInFrames={durationInFrames}
            premountFor={fps}
          >
            <Scene />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
