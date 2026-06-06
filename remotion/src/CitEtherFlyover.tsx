import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadJetBrainsMono} from '@remotion/google-fonts/JetBrainsMono';
import {BrandReveal} from './scenes/BrandReveal';
import {HeroScene} from './scenes/HeroScene';
import {ProblemScene} from './scenes/ProblemScene';
import {HowItWorksScene} from './scenes/HowItWorksScene';
import {FollowMePowerScene} from './scenes/FollowMePowerScene';
import {PodScene} from './scenes/PodScene';
import {CommunityScene} from './scenes/CommunityScene';
import {EconomicsScene} from './scenes/EconomicsScene';
import {CtaScene} from './scenes/CtaScene';

loadInter('normal', {weights: ['300', '400', '600', '700'], subsets: ['latin']});
loadJetBrainsMono('normal', {weights: ['400', '500', '600'], subsets: ['latin']});

export const CitEtherFlyover: React.FC = () => {
  const {fps} = useVideoConfig();

  // 60 seconds total at 30fps = 1800 frames
  // Scene durations in seconds:
  const scenes = [
    {component: BrandReveal, duration: 5},      // 0-5s
    {component: HeroScene, duration: 8},         // 5-13s
    {component: ProblemScene, duration: 9},       // 13-22s
    {component: HowItWorksScene, duration: 8},   // 22-30s
    {component: FollowMePowerScene, duration: 7}, // 30-37s
    {component: PodScene, duration: 6},           // 37-43s
    {component: CommunityScene, duration: 6},     // 43-49s
    {component: EconomicsScene, duration: 5},     // 49-54s
    {component: CtaScene, duration: 6},           // 54-60s
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
