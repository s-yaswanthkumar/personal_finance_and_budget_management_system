import React from 'react';

/**
 * SpendeeLogo Component
 * Recreates Spendee's iconic multi-colored segmented circle logo
 * Colors: Pink (#FF6FAF), Green (#00BC7C), Coral (#FE5A61), Sky Blue (#40C3F9), Amber (#FFC053)
 */
export default function SpendeeLogo({ className = "h-8", showText = true, textColor = "text-[#283139]", isLight = false }) {
  return (
    <div className={`flex items-center space-x-2.5 ${className}`}>
      {/* Spendee Multi-colored Donut Ring Icon */}
      <svg 
        width="32" 
        height="32" 
        viewBox="0 0 32 32" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0"
      >
        <defs>
          <clipPath id="spendee-ring-clip">
            <path d="M16 32C7.16344 32 0 24.8366 0 16C0 7.16344 7.16344 0 16 0C24.8366 0 32 7.16344 32 16C32 24.8366 24.8366 32 16 32ZM16 23.5C20.1421 23.5 23.5 20.1421 23.5 16C23.5 11.8579 20.1421 8.5 16 8.5C11.8579 8.5 8.5 11.8579 8.5 16C8.5 20.1421 11.8579 23.5 16 23.5Z" />
          </clipPath>
        </defs>

        <g clipPath="url(#spendee-ring-clip)">
          {/* Segment 1: Pink (Top) */}
          <polygon points="16,16 16,0 32,4 32,16" fill="#FF6FAF" />
          {/* Segment 2: Spendee Green (Right) */}
          <polygon points="16,16 32,4 32,24 24,30" fill="#00BC7C" />
          {/* Segment 3: Coral Red (Bottom-Right) */}
          <polygon points="16,16 24,30 16,32 8,30" fill="#FE5A61" />
          {/* Segment 4: Sky Blue (Bottom-Left) */}
          <polygon points="16,16 8,30 0,24 0,16" fill="#40C3F9" />
          {/* Segment 5: Sunny Amber (Left & Top-Left) */}
          <polygon points="16,16 0,16 0,4 16,0" fill="#FFC053" />
        </g>

        {/* Center Circle */}
        <circle cx="16" cy="16" r="7.5" fill={isLight ? "#1E293B" : "#FFFFFF"} />
        
        {/* Currency / Sparkle Emblem in center */}
        <text 
          x="16" 
          y="19" 
          textAnchor="middle" 
          fontSize="9" 
          fontWeight="bold" 
          fill={isLight ? "#34D399" : "#00BC7C"}
          fontFamily="system-ui, -apple-system, sans-serif"
        >
          ₹
        </text>
      </svg>

      {/* Spendee Wordmark */}
      {showText && (
        <div className="flex items-baseline space-x-1">
          <span className={`text-xl font-black tracking-tight ${textColor} font-sans`}>
            spendee
          </span>
          <span className="text-[11px] font-bold text-[#00BC7C] tracking-wide uppercase px-1.5 py-0.2 rounded-full bg-[#00BC7C]/10 border border-[#00BC7C]/20">
            AI
          </span>
        </div>
      )}
    </div>
  );
}
