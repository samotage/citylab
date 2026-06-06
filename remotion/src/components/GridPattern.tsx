import React from 'react';
import {useVideoConfig} from 'remotion';
import {BRAND} from '../brand';

export const GridPattern: React.FC<{opacity?: number}> = ({opacity = 0.08}) => {
  const {width, height} = useVideoConfig();
  const gap = 60;
  const cols = Math.ceil(width / gap) + 1;
  const rows = Math.ceil(height / gap) + 1;
  const lines = [];
  for (let i = 0; i < rows; i++) {
    lines.push(
      <line
        key={`h${i}`}
        x1={0}
        y1={i * gap}
        x2={width}
        y2={i * gap}
        stroke={BRAND.warmGrey}
        strokeWidth={0.5}
      />,
    );
  }
  for (let i = 0; i < cols; i++) {
    lines.push(
      <line
        key={`v${i}`}
        x1={i * gap}
        y1={0}
        x2={i * gap}
        y2={height}
        stroke={BRAND.warmGrey}
        strokeWidth={0.5}
      />,
    );
  }
  return (
    <svg
      width={width}
      height={height}
      style={{position: 'absolute', top: 0, left: 0, opacity}}
    >
      {lines}
    </svg>
  );
};
