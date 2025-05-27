/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      colors: {
        loginfo: '#93c5fd',   // light blue
        logwarn: '#facc15',   // yellow
        logerr: '#f87171'     // red
      },
      maxHeight: {
        'logbox': '24rem'
      },
    },
  },
  plugins: [],
}
