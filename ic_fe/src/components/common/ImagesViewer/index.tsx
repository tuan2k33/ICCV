import { twMerge } from 'tailwind-merge'
import ImageZoom from './ImageZoom'

interface Props {
  images?: {
    top?: string
    front?: string
    code?: string
  }
}

export default function ImagesViewer({ images }: Readonly<Props>) {
  return (
    <div className="grow h-full overflow-y-auto">
      <div className={twMerge('grow grid gap-3 grid-cols-2 h-full overflow-y-auto items-stretch')}>
        <ImageZoom src={images?.front ?? ''} alt="entry" marker="Mặt trước" />
        <ImageZoom src={images?.top ?? ''} alt="entry" marker="Mặt trên" />
      </div>
    </div>
  )
}
