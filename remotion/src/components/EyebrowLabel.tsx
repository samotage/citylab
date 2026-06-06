import React from 'react';
import {BRAND} from '../brand';

export const EyebrowLabel: React.FC<{
  text: string;
  color?: string;
}> = ({text, color = BRAND.teal}) => {
  return (
    <div
      style={{
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 22,
        fontWeight: 500,
        letterSpacing: '0.12em',
        textTransform: 'uppercase' as const,
        color,
      }}
    >
      {text}
    </div>
  );
};
