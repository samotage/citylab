import React from 'react';
import {Composition} from 'remotion';
import {CitEtherFlyover} from './CitEtherFlyover';
import {PitchVideo} from './PitchVideo';
import {FPS, WIDTH, HEIGHT, TOTAL_FRAMES, PITCH_WIDTH, PITCH_HEIGHT, PITCH_TOTAL_FRAMES} from './brand';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CitEtherFlyover"
        component={CitEtherFlyover}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
      <Composition
        id="CitEtherPitch"
        component={PitchVideo}
        durationInFrames={PITCH_TOTAL_FRAMES}
        fps={FPS}
        width={PITCH_WIDTH}
        height={PITCH_HEIGHT}
      />
    </>
  );
};
