import React from 'react';
import waDoodleBg from '../../assets/wa-chat-bg.svg';

/**
 * WhatsAppDoodleBackground
 * Seamless official WhatsApp doodle pattern:
 * - Rendered at an authentic miniature scale (340px repeating tile)
 * - Hundreds of delicate, high-density vector doodles
 * - Delicate watermark opacity ensuring messages and bubbles stay 100% legible
 */
export const WhatsAppDoodleBackground = React.memo(function WhatsAppDoodleBackground({ className = '', opacity = 0.6 }) {
  return (
    <div
      aria-hidden="true"
      className={`absolute inset-0 pointer-events-none select-none bg-[#efeae2] ${className}`}
      style={{
        contain: 'strict',
        transform: 'translateZ(0)',
        willChange: 'transform',
      }}
    >
      <div
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{
          backgroundImage: `url(${waDoodleBg})`,
          backgroundRepeat: 'repeat',
          backgroundSize: '340px auto',
          opacity,
          transform: 'translateZ(0)',
        }}
      />
    </div>
  );
});
