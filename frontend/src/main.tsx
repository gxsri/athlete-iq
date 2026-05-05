import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Theme: 'auto' | 'dark' | 'light'
// Auto: 18:00~06:00 = dark, else light
const savedTheme = localStorage.getItem('athleteiq-theme') || 'auto';
const hour = new Date().getHours();
const isNight = hour >= 18 || hour < 6;

let useDark: boolean;
if (savedTheme === 'dark') {
  useDark = true;
} else if (savedTheme === 'light') {
  useDark = false;
} else {
  useDark = isNight; // auto mode
}

if (useDark) document.documentElement.classList.add('dark');

// Expose for runtime checks
(window as any).__athleteiqTheme = savedTheme;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
