import { useRef, useState } from 'react'
import { useResize } from '~/hooks/useResize'

interface Props {
  error?: string
}

export default function InputError({ error }: Readonly<Props>) {
  const [errorHeight, setErrorHeight] = useState(0)
  const errorRef = useRef<HTMLParagraphElement>(null)
  useResize(errorRef, () => {
    if (errorRef.current) {
      setErrorHeight(errorRef.current.offsetHeight)
    }
  }, [])
  return (
    <div style={{ height: errorHeight }} className="overflow-hidden duration-200">
      <p ref={errorRef} className="text-red-500 text-xs">
        {error}
      </p>
    </div>
  )
}
