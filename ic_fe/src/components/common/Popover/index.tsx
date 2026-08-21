import {
  cloneElement,
  useEffect,
  useRef,
  useState,
  type HTMLAttributes,
  type ReactElement,
  type ReactNode,
  type RefAttributes,
  type RefObject,
} from 'react'
import { createPortal } from 'react-dom'
import { twMerge } from 'tailwind-merge'
import { useClickOutside } from '~/hooks/useClickOutside'

interface Props {
  open?: boolean
  children: ReactElement<HTMLAttributes<HTMLElement> & RefAttributes<HTMLElement>>
  content: ReactNode
  classNames?: {
    wrapper?: string
    popover?: string
  }
  onOpenChange?: (open: boolean) => void
}

/**
 * `children` ref must only `RefObject`
 */
export default function Popover({
  open,
  children,
  content,
  classNames,
  onOpenChange,
}: Readonly<Props>) {
  const [localOpen, setLocalOpen] = useState(open ?? false)
  const popoverRef = useRef<HTMLDivElement>(null)
  const childrenRef = useRef<HTMLElement>(null)

  const childrenCloned = cloneElement(children, {
    ref: children.props.ref ?? childrenRef,
  })

  const mergedChildrenRef = (children.props.ref ?? childrenRef) as RefObject<HTMLElement | null>

  useEffect(() => {
    if (!mergedChildrenRef.current) return

    const handleClick = () => {
      changeOpenStatus(typeof open === 'boolean' ? !open : !localOpen)
    }
    mergedChildrenRef.current.addEventListener('click', handleClick, true)

    const wrapper = mergedChildrenRef.current

    if (wrapper && popoverRef.current) {
      const { bottom, right } = wrapper.getBoundingClientRect()
      popoverRef.current.style.top = `${bottom}px`
      popoverRef.current.style.left = `${right - popoverRef.current.offsetWidth}px`
    }

    return () => {
      wrapper?.removeEventListener('click', handleClick, true)
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, localOpen])

  useClickOutside(
    popoverRef,
    (e) => {
      if (!mergedChildrenRef.current?.contains(e.target as Node)) {
        changeOpenStatus(false)
      }
    },
    [],
  )

  useClickOutside(
    mergedChildrenRef,
    (e) => {
      if (!popoverRef.current?.contains(e.target as Node)) {
        changeOpenStatus(false)
      }
    },
    [],
  )

  const changeOpenStatus = (isOpen: boolean) => {
    onOpenChange?.(isOpen)
    if (typeof open !== 'boolean') setLocalOpen(isOpen)
  }

  return (
    <>
      {childrenCloned}
      {(open || localOpen) &&
        createPortal(
          <div
            ref={popoverRef}
            className={twMerge(
              'hidden fixed rounded-lg p-2 bg-white shadow-lg shadow-gray-400 w-fit',
              'block z-50',
              classNames?.popover,
            )}
          >
            {content}
          </div>,
          document.body,
        )}
    </>
  )
}
