import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Цвета из текущего дизайна
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        primary: {
          DEFAULT: '#4A90E2',
          hover: '#357ABD',
        },
      },
      backdropBlur: {
        xs: '2px',
        '3xl': '40px',
        '4xl': '50px',
      },
      backdropSaturate: {
        180: '180%',
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(31, 38, 135, 0.15), 0 1px 0 rgba(255, 255, 255, 0.5) inset',
        'glass-hover': '0 12px 48px rgba(31, 38, 135, 0.2), 0 1px 0 rgba(255, 255, 255, 0.6) inset',
      },
      borderRadius: {
        '4xl': '24px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
  future: {
    hoverOnlyWhenSupported: true,
  },
};

export default config;
