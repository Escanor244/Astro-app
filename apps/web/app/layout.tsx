import type { Metadata, Viewport } from "next";
import { Noto_Sans_Tamil, Inter } from "next/font/google";
import "./globals.css";

// Noto Sans Tamil is loaded deliberately, not left to the system. Windows and
// Android ship usable Tamil fonts, but many Linux systems and some browsers
// fall back to tofu boxes, and a Tamil-native app rendering ????? is worse than
// useless. `display: swap` keeps first paint fast.
const tamil = Noto_Sans_Tamil({
  subsets: ["tamil"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-tamil",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ஜாதகம் · Jathagam",
  description:
    "Vedic astrology chart calculation — sidereal, South Indian, Tamil-native.",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "Jathagam" },
};

export const viewport: Viewport = {
  themeColor: "#d97706",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Runs before first paint, so a dark-mode user never sees a white
            flash (and vice versa). It has to be inline and blocking: anything
            deferred runs after the browser has already painted. Kept to one
            expression, duplicating the tiny bit of logic in ThemeToggle rather
            than importing it, because a module import cannot run this early. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('theme')||'system';var d=t==='dark'||(t==='system'&&matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.classList.toggle('dark',d);}catch(e){}})();`,
          }}
        />
      </head>
      <body
        className={`${inter.variable} ${tamil.variable} bg-slate-50 font-sans text-slate-900 antialiased dark:bg-slate-950 dark:text-slate-100`}
      >
        {children}
      </body>
    </html>
  );
}
