/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 🎨 Paleta institucional del asistente I+D
        primary: {
          DEFAULT: "#005EB8", // Azul institucional
          light: "#4DA3FF",
          dark: "#003F7F",
        },
        secondary: {
          DEFAULT: "#00A6A6", // Verde-azulado complementario
          light: "#33CFCF",
          dark: "#007676",
        },
        neutral: {
          light: "#F5F7FA",
          DEFAULT: "#E4E8EE",
          dark: "#2E3A4E",
        },
        accent: "#FFD166", // Amarillo para resaltar
        danger: "#EF4444", // Rojo para errores
        success: "#10B981", // Verde éxito
      },
      fontFamily: {
        sans: ["Inter", "Roboto", "system-ui", "sans-serif"],
        display: ["Poppins", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}
