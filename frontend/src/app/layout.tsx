import type { Metadata } from "next";
import { Inter, Azeret_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ 
  subsets: ["latin"],
  variable: '--font-inter',
});

const azeretMono = Azeret_Mono({
  subsets: ["latin"],
  variable: '--font-azeret-mono',
});

export const metadata: Metadata = {
  title: "AgentForge",
  description: "AI-powered web application builder",
};
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${azeretMono.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
