import {
  cloneElement,
  useEffect,
  useMemo,
  useRef,
  useState,
  type HTMLAttributes,
  type ReactElement,
  type RefAttributes,
  type RefObject,
} from 'react'
import { createPortal } from 'react-dom'
import { twMerge } from 'tailwind-merge'

interface Props {
  id?: string
  open?: boolean
  children: ReactElement<HTMLAttributes<HTMLElement> & RefAttributes<HTMLElement>>
  content?: string
  placement?:
    | 'top'
    | 'top-start'
    | 'top-end'
    | 'right'
    | 'right-start'
    | 'right-end'
    | 'bottom'
    | 'bottom-start'
    | 'bottom-end'
    | 'left'
    | 'left-start'
    | 'left-end'
  classNames?: {
    wrapper?: string
    tooltip?: string
  }
}
export default function Tooltip({
  open: openProps,
  children,
  content,
  placement = 'top',
  classNames,
}: Readonly<Props>) {
  const [open, setOpen] = useState(openProps ?? false)
  const childrenRef = useRef<HTMLElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const mergedChildrenRef = (children.props.ref ?? childrenRef) as RefObject<HTMLElement | null>

  const renderClassName: {
    content: string
    arrow: string
  } = useMemo(() => {
    switch (placement) {
      case 'top':
        return {
          content: '-translate-x-1/2 -translate-y-2',
          arrow: 'bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2',
        }

      case 'left':
        return {
          content: '-translate-y-1/2 -translate-x-2',
          arrow: 'right-0 top-1/2 translate-x-1/2 -translate-y-1/2',
        }

      case 'right':
        return {
          content: '-translate-y-1/2 translate-x-2',
          arrow: 'left-0 top-1/2 -translate-x-1/2 -translate-y-1/2',
        }

      case 'bottom':
        return {
          content: '-translate-x-1/2 translate-y-2',
          arrow: 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2',
        }

      default:
        return {
          content: '',
          arrow: '',
        }
    }
  }, [placement])

  let isOpen = false
  if (typeof openProps === 'boolean') isOpen = openProps
  else isOpen = open

  useEffect(() => {
    const target = mergedChildrenRef.current

    const handleMouseEnter = () => {
      setOpen(true)
    }
    const handleMouseLeave = () => {
      setOpen(false)
    }
    target?.addEventListener('mouseover', handleMouseEnter)
    target?.addEventListener('mouseleave', handleMouseLeave)

    const updateStyle = async () => {
      if (tooltipRef.current && target) {
        const targetRect = target.getBoundingClientRect()
        let top = 0,
          left = 0
        switch (placement) {
          case 'top':
            top = targetRect.top - tooltipRef.current.offsetHeight
            left = targetRect.left + targetRect.width / 2
            break
          case 'right':
            top = targetRect.top + targetRect.height / 2
            left = targetRect.right
            break
          case 'bottom':
            top = targetRect.bottom
            left = targetRect.left + targetRect.width / 2
            break
          case 'left':
            top = targetRect.top + targetRect.height / 2
            left = targetRect.left - tooltipRef.current.offsetWidth
            break
          default:
            // TODO
            break
        }

        tooltipRef.current.style.top = `${top}px`
        tooltipRef.current.style.left = `${left}px`
        tooltipRef.current.style.visibility = 'visible'
      }
    }

    updateStyle()

    return () => {
      target?.removeEventListener('mouseover', handleMouseEnter)
      target?.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [open, openProps, placement, mergedChildrenRef, isOpen, content])

  const childrenCloned = cloneElement(children, {
    ref: mergedChildrenRef,
  })

  return (
    <>
      {childrenCloned}
      {isOpen &&
        !!content &&
        createPortal(
          <div
            className={twMerge(
              'invisible fixed z-50 bg-[#111] text-white p-2 rounded-md duration-200',
              'text-sm min-w-10 text-center z-10 max-w-sm',
              renderClassName.content,
              classNames?.tooltip,
            )}
            ref={tooltipRef}
          >
            {content}
            <span
              className={twMerge(
                'absolute w-2 block aspect-square bg-inherit rotate-45',
                renderClassName.arrow,
              )}
            ></span>
          </div>,
          document.body,
        )}
    </>
  )
}
