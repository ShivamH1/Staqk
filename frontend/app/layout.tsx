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
  title: { default: 'Staqk — Build. Secure. Ship.', template: '%s · Staqk' },
  description: 'Security-first, multi-agent AI app builder.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <ClerkProvider
      appearance={{
        variables: {
          colorBackground: '#141414',
          colorPrimary: '#ffffff',
          colorPrimaryForeground: '#000000',
          colorForeground: '#ffffff',
          colorMutedForeground: '#999999',
          colorInput: '#1c1c1c',
          colorInputForeground: '#ffffff',
          colorNeutral: '#ffffff',
          colorBorder: '#262626',
          borderRadius: '10px',
          fontFamily: 'var(--font-inter)',
        },
        elements: {
          card: 'bg-surface-1 border border-hairline shadow-none',
          headerTitle: 'text-ink',
          headerSubtitle: 'text-ink-muted',
          socialButtonsBlockButton: 'bg-surface-2 border-hairline text-ink',
          formButtonPrimary: 'bg-white text-black hover:bg-white/90',
          footerActionLink: 'text-accent-blue hover:text-accent-blue',
        },
      }}
    >
      <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}>
        <body className="min-h-full bg-canvas text-ink flex flex-col font-sans">
          <Providers>{children}</Providers>
        </body>
      </html>
    </ClerkProvider>
  )
}
