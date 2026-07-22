import React from 'react';

export default function WWWGlobeIcon({ size = 24, color = 'currentColor', className, style }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width={size} 
      height={size} 
      viewBox="0 0 100 100" 
      className={className}
      style={style}
    >
      <g stroke={color} strokeWidth="4" fill="none" strokeLinecap="round" strokeLinejoin="round">
        {/* Outer circle */}
        <circle cx="50" cy="50" r="44"/>
        
        {/* Vertical line */}
        <line x1="50" y1="6" x2="50" y2="94"/>
        
        {/* Vertical curves */}
        <path d="M 50 6 A 22 44 0 0 0 50 94"/>
        <path d="M 50 6 A 22 44 0 0 1 50 94"/>
        
        {/* Horizontal curves */}
        <path d="M 14 25 A 44 15 0 0 0 86 25"/>
        <path d="M 14 75 A 44 15 0 0 1 86 75"/>
      </g>
      
      {/* WWW Banner */}
      <rect x="8" y="38" width="84" height="24" rx="12" fill="var(--color-bg-card)" stroke={color} strokeWidth="4"/>
      <text x="50" y="55" fontFamily="sans-serif" fontWeight="bold" fontSize="16" fill={color} textAnchor="middle" letterSpacing="1">WWW</text>
    </svg>
  );
}
