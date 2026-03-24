import type { Metadata } from 'next'
import { Inter, Merriweather, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-sans',
})

const merriweather = Merriweather({ 
  weight: ['300', '400', '700', '900'],
  subsets: ['latin'],
  variable: '--font-serif',
})

const jetbrainsMono = JetBrains_Mono({ 
  subsets: ['latin'],
  variable: '--font-mono',
})

export const metadata: Metadata = {
  title: 'Balkan Corruption Insider | Exposing Corruption Through Data',
  description: 'An open-source platform analyzing public procurement data across the Balkans to detect corruption patterns and enhance transparency.',
  keywords: 'corruption, balkans, transparency, public procurement, data analysis',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${merriweather.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        {children}
        <script async src="https://platform.twitter.com/widgets.js" charSet="utf-8"></script>
      </body>
    </html>
  )
}