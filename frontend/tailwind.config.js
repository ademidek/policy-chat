export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'chat-bg': '#212121',
        'chat-sidebar': '#171717',
        'chat-text': '#eee',
        'chat-muted': '#cdcdcd',
        'chat-muted-dark': '#b4b4b4',
        'chat-accent': '#520913',
        'chat-accent-hover': '#6b0c18',
      },
      maxWidth: {
        'chat': '48rem',
      },
    },
  },
  plugins: [],
};
