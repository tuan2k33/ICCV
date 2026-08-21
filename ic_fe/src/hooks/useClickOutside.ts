import { useEffect, type DependencyList, type RefObject } from 'react'

export const useClickOutside = (
  ref: RefObject<HTMLElement | null>,
  handler: (e: MouseEvent) => void,
  deps: DependencyList,
) => {
  useEffect(() => {
    if (!ref.current) return

    const handleWindowClick = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) {
        handler(e)
      }
    }

    window.addEventListener('click', handleWindowClick, true)

    return () => {
      window.removeEventListener('click', handleWindowClick, true)
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
