"use client";
import { useState, useEffect } from "react";
import { Sun, Moon } from "lucide-react";
import { motion } from "motion/react";

// Optional dark/light mode toggle.
// To use: add this component to the Navbar.
// Requires: light mode CSS variables defined in globals.css (see design-tokens.css comments)

export function ThemeToggle() {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    // Check system preference on mount
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const stored = document.documentElement.classList.contains("light") ? false : true;
    setDark(stored ?? prefersDark);
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    if (next) {
      document.documentElement.classList.remove("light");
    } else {
      document.documentElement.classList.add("light");
    }
  }

  return (
    <button
      onClick={toggle}
      className="relative w-9 h-9 flex items-center justify-center rounded-lg hover:bg-card transition-colors cursor-pointer"
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
    >
      <motion.div
        initial={false}
        animate={{ rotate: dark ? 0 : 180, scale: dark ? 1 : 0 }}
        transition={{ type: "spring", damping: 15, stiffness: 200 }}
        className="absolute"
      >
        <Moon className="w-4 h-4" />
      </motion.div>
      <motion.div
        initial={false}
        animate={{ rotate: dark ? -180 : 0, scale: dark ? 0 : 1 }}
        transition={{ type: "spring", damping: 15, stiffness: 200 }}
        className="absolute"
      >
        <Sun className="w-4 h-4" />
      </motion.div>
    </button>
  );
}
