import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { ShortlistProvider } from "@/contexts/shortlist-context";
import { AuthProvider } from "@/contexts/auth-context";
import { SecurityBanner } from "@/components/security-banner";

export const metadata: Metadata = {
  title: "The Courseteer",
  description: "Australian university course aggregator",
  icons: { icon: '/logo-icon.png', apple: '/logo-icon.png' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="flex min-h-screen flex-col bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <AuthProvider>
            <ShortlistProvider>
              <SecurityBanner />
              <Header />
              <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
              <Footer />
            </ShortlistProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
