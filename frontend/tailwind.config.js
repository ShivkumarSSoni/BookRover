/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        // Barlow SemiBold/Bold — closest freely available match to Siemens Sans.
        // Used exclusively for the "BookRover" brand wordmark across all pages.
        brand: ['Barlow', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

