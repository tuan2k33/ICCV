import { type DependencyList, type RefObject, useEffect } from 'react'

/**
 * @param deps - The dependencies, work like useEffect's deps
 */
export function useResize(
  ref: RefObject<HTMLElement | null>,
  handle: () => void,
  deps?: DependencyList,
) {
  useEffect(() => {
    if (!ref.current) return
    const observe = new ResizeObserver(handle)

    observe.observe(ref.current)

    return () => {
      observe.disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
