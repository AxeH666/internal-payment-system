/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base: {
          950: '#020617',
          900: '#f8fafc',   // app background
          800: '#e5e7eb',
          700: '#cbd5f5',
          600: '#94a3b8',
        },
        surface: {
          DEFAULT: '#ffffff',
          raised: '#f8fafc',
          overlay: '#e5e7eb',
          border: '#e2e8f0',
          muted: '#f1f5f9',
        },
        accent: {
          DEFAULT: '#2563eb',     // blue-600
          hover: '#1d4ed8',       // blue-700
          muted: '#bfdbfe',       // blue-200
          subtle: '#eff6ff',      // blue-50
        },
        success: { DEFAULT: '#10b981', muted: '#064e3b', text: '#6ee7b7' },
        warning: { DEFAULT: '#f59e0b', muted: '#451a03', text: '#fcd34d' },
        danger: { DEFAULT: '#ef4444', muted: '#450a0a', text: '#fca5a5' },
        info: { DEFAULT: '#3b82f6', muted: '#1e3a5f', text: '#93c5fd' },
        text: {
          primary: '#0f172a',   // slate-900
          secondary: '#64748b', // slate-500
          muted: '#94a3b8',     // slate-400
          inverse: '#ffffff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0,0,0,0.4), 0 1px 2px -1px rgba(0,0,0,0.4)',
        elevated: '0 4px 6px -1px rgba(0,0,0,0.5), 0 2px 4px -2px rgba(0,0,0,0.5)',
        glow: '0 0 0 1px rgba(99,102,241,0.3), 0 4px 16px rgba(99,102,241,0.15)',
        'glow-sm': '0 0 0 1px rgba(99,102,241,0.2)',
      },
      borderRadius: { xl: '0.75rem', '2xl': '1rem' },
      animation: {
        'fade-in': 'fadeIn 0.15s ease-out',
        'slide-in': 'slideIn 0.2s ease-out',
        pulse: 'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
        slideIn: { '0%': { opacity: 0, transform: 'translateY(-4px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
}
