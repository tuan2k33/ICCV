import { useDeferredValue, useLayoutEffect, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { twMerge } from 'tailwind-merge'
import XCloseIcon from '~/assets/icons/x-close.svg'

export interface ModalProps {
  open: boolean
  children: ReactNode
  classNames?: {
    wrapper?: string
    body?: string
    closeButton?: string
  }
  destroyOnHide?: boolean
  closeButton?: boolean
  onRequestClose?: () => void
}

export default function Modal({
  children,
  classNames,
  open,
  destroyOnHide,
  closeButton = true,
  onRequestClose,
}: ModalProps) {
  const [existDOM, setExistDOM] = useState(!destroyOnHide)
  const _open = useDeferredValue(open)

  useLayoutEffect(() => {
    let timeoutId = -1
    if (open) setExistDOM(true)
    else if (destroyOnHide) {
      timeoutId = window.setTimeout(() => {
        setExistDOM(false)
      }, 200)
    }

    return () => {
      clearTimeout(timeoutId)
    }
  }, [open, destroyOnHide])

  if (!existDOM) return null
  return createPortal(
    <div
      className={twMerge(
        'fixed inset-0 h-dvh w-dvw -z-50 backdrop-blur-lg bg-[#0C111DB3] flex items-center justify-center invisible opacity-0 duration-200 transition-opacity',
        _open && 'visible opacity-100 z-50',
        classNames?.wrapper,
      )}
      onClick={onRequestClose}
    >
      <div
        className={twMerge('rounded-xl p-6 bg-white relative max-w-dvw', classNames?.body)}
        onClick={(e) => e.stopPropagation()}
      >
        {closeButton && (
          <button
            type="button"
            className={twMerge(
              'absolute top-4 right-4 text-[#757575] text-2xl p-2.5 cursor-pointer hover:bg-gray-100 duration-200 rounded',
              classNames?.closeButton,
            )}
            onClick={onRequestClose}
          >
            <XCloseIcon />
          </button>
        )}
        {children}
      </div>
    </div>,
    document.body,
  )
}
