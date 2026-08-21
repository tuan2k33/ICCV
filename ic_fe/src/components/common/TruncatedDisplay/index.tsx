import { useRef, useState } from 'react'
import { useResize } from '~/hooks/useResize'
import Tooltip from '../Tooltip'

interface Props {
  content: string
  className?: string
}

export default function TruncatedDisplay({ content, className }: Readonly<Props>) {
  const contentRef = useRef<HTMLDivElement>(null)
  const [openable, setOpenable] = useState<boolean | undefined>(undefined)

  useResize(contentRef, () => {
    if (contentRef.current && contentRef.current.scrollHeight > contentRef.current.offsetHeight)
      setOpenable(true)
    else setOpenable(false)
  }, [])

  return (
    <Tooltip content={openable ? content : undefined}>
      <div className={className} ref={contentRef}>
        {content}
      </div>
    </Tooltip>
  )
}
