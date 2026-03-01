/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        /* Dark palette */
        base: '#0F0F12',
        'base-2': '#16161A',
        'base-3': '#1E1E24',
        surface: '#24242C',
        'surface-2': '#2C2C36',
        border: '#333340',
        /* Accent palette from user spec */
        sage: '#BACDB0',
        teal: '#729B79',
        'teal-bright': '#8BC49A',
        slate: '#475B63',
        ink: '#F3E8EE',
        muted: '#8B8B9E',
        primary: '#729B79',
        secondary: '#475B63',
        card: '#1E1E24',
        danger: '#E05252',
        warning: '#E5A93D',
        success: '#729B79',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      boxShadow: {
        soft: '0 2px 20px rgba(0,0,0,0.25)',
        card: '0 4px 24px rgba(0,0,0,0.35)',
        glow: '0 0 40px rgba(114,155,121,0.15)',
        'glow-lg': '0 0 60px rgba(114,155,121,0.20)',
        'glow-teal': '0 0 30px rgba(114,155,121,0.25), 0 0 60px rgba(114,155,121,0.10)',
        glass: '0 8px 32px rgba(0,0,0,0.40)',
        'inner-glow': 'inset 0 1px 0 rgba(255,255,255,0.05)',
        neon: '0 0 5px rgba(114,155,121,0.4), 0 0 20px rgba(114,155,121,0.2), 0 0 40px rgba(114,155,121,0.1)',
      },
      letterSpacing: {
        title: '0.02em',
        wide: '0.08em',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'slide-right': 'slideRight 0.4s ease-out forwards',
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-dot': 'pulseDot 2s ease-in-out infinite',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
        'gradient-x': 'gradientX 6s ease infinite',
        'float': 'float 6s ease-in-out infinite',
        'border-rotate': 'borderRotate 4s linear infinite',
        'scale-in': 'scaleIn 0.3s ease-out forwards',
        'count-up': 'fadeIn 0.6s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideRight: {
          '0%': { opacity: '0', transform: 'translateX(-16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        pulseDot: {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.8)', opacity: '0.3' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(114,155,121,0.15)' },
          '50%': { boxShadow: '0 0 40px rgba(114,155,121,0.30)' },
        },
        gradientX: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        borderRotate: {
          '0%': { '--angle': '0deg' },
          '100%': { '--angle': '360deg' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.9)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
