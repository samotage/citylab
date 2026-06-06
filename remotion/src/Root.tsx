import React from 'react';
import {Composition} from 'remotion';
import {CitEtherFlyover} from './CitEtherFlyover';
import {FPS, WIDTH, HEIGHT, TOTAL_FRAMES} from './brand';

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
    </>
  );
};
