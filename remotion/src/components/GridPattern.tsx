import React from 'react';
import {BRAND} from '../brand';

export const GridPattern: React.FC<{opacity?: number}> = ({opacity = 0.08}) => {
  const gap = 60;
  const lines = [];
  for (let i = 0; i < 40; i++) {
    lines.push(
      <line
        key={`h${i}`}
        x1={0}
        y1={i * gap}
        x2={1080}
        y2={i * gap}
        stroke={BRAND.warmGrey}
        strokeWidth={0.5}
      />,
    );
    lines.push(
      <line
        key={`v${i}`}
        x1={i * gap}
        y1={0}
        x2={i * gap}
        y2={1920}
        stroke={BRAND.warmGrey}
        strokeWidth={0.5}
      />,
    );
  }
  return (
    <svg
      width={1080}
      height={1920}
      style={{position: 'absolute', top: 0, left: 0, opacity}}
    >
      {lines}
    </svg>
  );
};
