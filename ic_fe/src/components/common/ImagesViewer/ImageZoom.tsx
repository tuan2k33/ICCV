import { useRef } from 'react'
import { twMerge } from 'tailwind-merge'
import { useZoom } from '~/hooks/useZoom'

interface Props {
  src: string
  alt: string
  className?: string
  marker?: string
}

export default function ImageZoom({ src, alt, className, marker }: Readonly<Props>) {
  const containerRef = useRef<HTMLDivElement>(null)
  const imgRef = useRef<HTMLImageElement>(null)

  const { zoomScale, translate, isDragging } = useZoom(containerRef, imgRef, {
    init: 1,
    min: 1,
    max: 6,
    step: 0.003,
  })

  return (
    <div
      className={twMerge(
        'relative h-full group/image-zoom overflow-hidden select-none rounded-md border-gray-300 shadow-sm',
        className,
      )}
      style={{
        cursor: isDragging ? 'grabbing' : 'grab',
      }}
      ref={containerRef}
    >
      <img
        ref={imgRef}
        src={src}
        alt={alt}
        className="absolute w-full h-full max-w-[unset] object-fill"
        draggable={false}
        style={{
          transformOrigin: '0 0',
          userSelect: 'none',
          pointerEvents: 'none',
          scale: zoomScale,
          translate: `${translate.x}px ${translate.y}px`,
        }}
        onError={(e) => {
          e.currentTarget.parentElement!.style.borderWidth = '1px'
        }}
      />
      {marker && (
        <div
          className="absolute top-0 left-0 font-medium text-white border-r border-b border-current rounded-br-md
          px-2.5 py-0.5 bg-[#475467E5] select-none pointer-events-none"
        >
          {marker}
        </div>
      )}
    </div>
  )
}
