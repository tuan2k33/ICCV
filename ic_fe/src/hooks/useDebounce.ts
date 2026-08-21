import { useEffect, useState, type Dispatch, type SetStateAction } from 'react'

export const useDebounce = <T>(value: T, delay = 700): [T, Dispatch<SetStateAction<T>>] => {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setDebounced(value)
    }, delay)

    return () => {
      clearTimeout(timeoutId)
    }
  }, [value, delay])

  return [debounced, setDebounced]
}
