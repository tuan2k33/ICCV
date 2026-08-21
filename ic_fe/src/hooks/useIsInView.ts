import { useEffect, type DependencyList, type RefObject } from 'react'

export const useIsInView = (
  ref: RefObject<Element | null>,
  options: {
    deps?: DependencyList
    listener: (isInView: boolean) => void
  },
  intersectionObserverOptions?: IntersectionObserverInit,
) => {
  useEffect(() => {
    const observe = new IntersectionObserver(([entry]) => {
      options.listener(entry.isIntersecting)
    }, intersectionObserverOptions)

    if (ref.current) {
      observe.observe(ref.current)
    }

    return () => {
      observe.disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ref, ...(options.deps ?? [])])
}
