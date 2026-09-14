/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#dbe6fe",
          200: "#bed0fd",
          300: "#93b2fb",
          400: "#618bf7",
          500: "#3d66f0",
          600: "#2848e5",
          700: "#2136c9",
          800: "#212fa2",
          900: "#212b80",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
