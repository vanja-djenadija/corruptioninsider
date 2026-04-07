'use client'

import Image from 'next/image'
import { useState } from 'react'
import { Dialog, DialogContent } from '@/components/ui/dialog'

const eventImages = [
  { src: '/images/event/team-working.jpg', alt: 'Team working on the project' },
  { src: '/images/event/presentation.jpg', alt: 'Project presentation' },
  { src: '/images/event/hackathon-venue.jpg', alt: 'Hackathon venue' },
  { src: '/images/event/team-photo.jpg', alt: 'Team photo' },
  { src: '/images/event/coding-session.jpg', alt: 'Coding session' },
  { src: '/images/event/award-ceremony.jpg', alt: 'Award ceremony' },
]

export default function Gallery() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null)

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-5xl mx-auto">
        {eventImages.map((image, index) => (
          <div
            key={index}
            className="relative aspect-square cursor-pointer overflow-hidden rounded-lg hover:opacity-90 transition-opacity"
            onClick={() => setSelectedImage(image.src)}
          >
            <Image
              src={image.src}
              alt={image.alt}
              fill
              className="object-cover"
              sizes="(max-width: 768px) 50vw, 33vw"
            />
          </div>
        ))}
      </div>

      <Dialog open={!!selectedImage} onOpenChange={() => setSelectedImage(null)}>
        <DialogContent className="max-w-4xl">
          {selectedImage && (
            <div className="relative w-full aspect-video">
              <Image
                src={selectedImage}
                alt="Event photo"
                fill
                className="object-contain"
              />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}