import React from 'react';
import type { RiskLevel } from '../../types';

interface Props {
  score: number;
  level: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
}

const COLORS: Record<RiskLevel, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
};

export const RiskScore: React.FC<Props> = ({ score, level, size = 'md' }) => {
  const color = COLORS[level];
  const radius = size === 'lg' ? 36 : size === 'md' ? 28 : 20;
  const stroke = size === 'lg' ? 5 : 4;
  const circumference = 2 * Math.PI * (radius - stroke);
  const offset = circumference - (score / 100) * circumference;
  const fontSize = size === 'lg' ? 18 : size === 'md' ? 14 : 11;

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <div style={{ position: 'relative', width: radius * 2, height: radius * 2 }}>
        <svg width={radius * 2} height={radius * 2} style={{ transform: 'rotate(-90deg)' }}>
          <circle
            cx={radius} cy={radius} r={radius - stroke}
            fill="none" stroke="#334155" strokeWidth={stroke}
          />
          <circle
            cx={radius} cy={radius} r={radius - stroke}
            fill="none" stroke={color} strokeWidth={stroke}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize, fontWeight: 700, color,
        }}>
          {Math.round(score)}
        </div>
      </div>
      <span style={{
        fontSize: size === 'lg' ? 12 : 10,
        fontWeight: 600,
        color,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
      }}>
        {level}
      </span>
    </div>
  );
};
