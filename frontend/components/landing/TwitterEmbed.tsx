'use client'

import { useEffect } from 'react'

export default function TwitterEmbed() {
  useEffect(() => {
    // Reload Twitter widgets after component mounts
    if (typeof window !== 'undefined' && (window as any).twttr) {
      (window as any).twttr.widgets.load()
    }
  }, [])

  return (
    <div className="flex justify-center">
      <blockquote className="twitter-tweet">
        <p lang="en" dir="ltr">
          How do you expose{' '}
          <a href="https://twitter.com/hashtag/transnational?src=hash&amp;ref_src=twsrc%5Etfw">
            #transnational
          </a>{' '}
          corruption networks? In many regions, tons of data is already available, primed for analysis &amp; aggregation. 
          One of our winning{' '}
          <a href="https://twitter.com/hashtag/HackCorruption?src=hash&amp;ref_src=twsrc%5Etfw">
            #HackCorruption
          </a>{' '}
          Balkans teams, Balkan Corruption Insider, is doing just that...
          <a href="https://twitter.com/DGateway?ref_src=twsrc%5Etfw">@dgateway</a>{' '}
          <a href="https://twitter.com/CIPEglobal?ref_src=twsrc%5Etfw">@CIPEglobal</a>{' '}
          <a href="https://twitter.com/MSIWorldwide?ref_src=twsrc%5Etfw">@MSIWorldwide</a>{' '}
          <a href="https://t.co/lGlGwuYq2O">pic.twitter.com/lGlGwuYq2O</a>
        </p>
        &mdash; #HackCorruption (@hackcorruption){' '}
        <a href="https://twitter.com/hackcorruption/status/1853717410420810133?ref_src=twsrc%5Etfw">
          November 5, 2024
        </a>
      </blockquote>
    </div>
  )
}