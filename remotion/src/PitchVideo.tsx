import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadJetBrainsMono} from '@remotion/google-fonts/JetBrainsMono';
import {BrandRevealPitch} from './scenes/pitch/BrandRevealPitch';
import {ProblemScenePitch} from './scenes/pitch/ProblemScenePitch';
import {AgitateScenePitch} from './scenes/pitch/AgitateScenePitch';
import {FollowMePowerScenePitch} from './scenes/pitch/FollowMePowerScenePitch';
import {AppDemoFollowMe} from './scenes/pitch/AppDemoFollowMe';
import {TierOneScenePitch} from './scenes/pitch/TierOneScenePitch';
import {AppDemoEarnings} from './scenes/pitch/AppDemoEarnings';
import {TierTwoDestinationsScenePitch} from './scenes/pitch/TierTwoDestinationsScenePitch';
import {AutoArbCommunityScenePitch} from './scenes/pitch/AutoArbCommunityScenePitch';
import {AppDemoPod} from './scenes/pitch/AppDemoPod';
import {BusinessModelScenePitch} from './scenes/pitch/BusinessModelScenePitch';
import {EvidenceCtaScenePitch} from './scenes/pitch/EvidenceCtaScenePitch';
import {EndCardScenePitch} from './scenes/pitch/EndCardScenePitch';

loadInter('normal', {weights: ['300', '400', '600', '700'], subsets: ['latin']});
loadJetBrainsMono('normal', {weights: ['400', '500', '600'], subsets: ['latin']});

export const PitchVideo: React.FC = () => {
  const {fps} = useVideoConfig();

  // 180 seconds total at 30fps = 5400 frames
  const scenes = [
    {component: BrandRevealPitch, duration: 5},            // 0:00-0:05
    {component: ProblemScenePitch, duration: 20},           // 0:05-0:25
    {component: AgitateScenePitch, duration: 16},           // 0:25-0:41
    {component: FollowMePowerScenePitch, duration: 18},     // 0:41-0:59
    {component: AppDemoFollowMe, duration: 14},             // 0:59-1:13  APP DEMO
    {component: TierOneScenePitch, duration: 20},           // 1:13-1:33
    {component: AppDemoEarnings, duration: 12},             // 1:33-1:45  APP DEMO
    {component: TierTwoDestinationsScenePitch, duration: 16}, // 1:45-2:01
    {component: AutoArbCommunityScenePitch, duration: 16},  // 2:01-2:17
    {component: AppDemoPod, duration: 12},                  // 2:17-2:29  APP DEMO
    {component: BusinessModelScenePitch, duration: 12},     // 2:29-2:41
    {component: EvidenceCtaScenePitch, duration: 14},       // 2:41-2:55
    {component: EndCardScenePitch, duration: 5},            // 2:55-3:00
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
