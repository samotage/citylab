import React from 'react';
import {BRAND} from '../brand';

export const Wordmark: React.FC<{
  size?: number;
  onDark?: boolean;
}> = ({size = 48, onDark = false}) => {
  return (
    <div style={{display: 'flex', alignItems: 'baseline', gap: 0}}>
      <span
        style={{
          fontFamily: 'Inter, sans-serif',
          fontWeight: 700,
          fontSize: size,
          color: BRAND.amber,
          letterSpacing: '-0.03em',
        }}
      >
        cit
      </span>
      <span
        style={{
          fontFamily: 'Inter, sans-serif',
          fontWeight: 700,
          fontSize: size,
          color: onDark ? BRAND.white : BRAND.teal,
          letterSpacing: '-0.03em',
        }}
      >
        Ether
      </span>
    </div>
  );
};
