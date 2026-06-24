import { ClerkProvider } from '@clerk/nextjs'
import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
})

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-jetbrains-mono',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'Staqk — Build. Secure. Ship.',
  description: 'Security-first, multi-agent AI app builder.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <ClerkProvider>
      <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}>
        <body className="min-h-full bg-canvas text-ink flex flex-col font-sans">
          <Providers>{children}</Providers>
        </body>
      </html>
    </ClerkProvider>
  )
}
