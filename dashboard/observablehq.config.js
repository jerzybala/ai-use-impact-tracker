// Observable Framework configuration.
// See https://observablehq.com/framework/config

export default {
  title: "AI Use Impact Tracker",
  pages: [
    { name: "Overview",          path: "/" },
    { name: "By country",        path: "/by-country" },
    { name: "Frequency & impact", path: "/by-frequency" },
    { name: "Methodology",       path: "/about" }
  ],
  theme: ["air", "alt"],
  head: `<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E🧠%3C/text%3E%3C/svg%3E">`,
  footer: "Global Mind Project — Sapien Labs",
  toc: false
};
