import { useRef } from 'react'
import { twMerge } from 'tailwind-merge'
import type { useModal } from '~/hooks/useModal'
import ImagesViewer from './ImagesViewer'
import ImageZoom from './ImagesViewer/ImageZoom'
import Modal from './Modal'

interface Props {
  className?: string
  videoUrl?: string
  images?: {
    top?: string
    front?: string
    code?: string
  }
  type: 'image' | 'video'
  viewCodeModal: ReturnType<typeof useModal>
}

export default function WorkspaceDataViewer({
  className,
  videoUrl,
  images,
  type,
  viewCodeModal,
}: Readonly<Props>) {
  const timeRef = useRef(0)
  const videoRef = useRef<HTMLVideoElement>(null)
  const viewRef = useRef<HTMLDivElement>(null)

  return (
    <>
      <div ref={viewRef} className={twMerge('grow relative', className)}>
        {type === 'image' && <ImagesViewer images={images} />}
        {type === 'video' && (
          <video
            ref={videoRef}
            className="w-full h-full absolute inset-0 object-fill rounded-md"
            controls
            autoPlay
            aria-label="Entry video content"
            src={videoUrl}
            onTimeUpdate={(e) => {
              timeRef.current = e.currentTarget.currentTime
            }}
          >
            <track kind="captions" />
          </video>
        )}
      </div>
      <Modal
        open={viewCodeModal.open}
        onRequestClose={viewCodeModal.closeModal}
        classNames={{
          wrapper: 'backdrop-blur-none bg-[#0C111D80]',
          body: 'p-0 w-full max-w-[max(850px,66%)] overflow-hidden h-full max-h-[max(540px,75%)] border-[0.5px] border-[#EAECF0]',
          closeButton: 'z-10 top-2.5 right-2.5 w-6 h-6 p-0 hover:bg-transparent rounded-none',
        }}
        destroyOnHide
      >
        <div className="bg-white w-full h-full flex flex-col">
          <p className="py-2 px-6 text-sm font-semibold">MÃ VỊ TRÍ</p>
          <div className="grow w-full">
            <ImageZoom src={images?.code ?? ''} className="rounded-t-none" alt="code" />
          </div>
        </div>
      </Modal>
    </>
  )
}
