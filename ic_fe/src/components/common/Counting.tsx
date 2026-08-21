import { useEffect, useImperativeHandle, useRef, useState, type RefObject } from 'react'
import { twMerge } from 'tailwind-merge'
import { formatTime } from '~/utils/formatTime'
import ClockIcon from '~/assets/icons/clock.svg'

interface Props {
  className?: string
  /**
   * This shouldn't be changed dynamically
   */
  autoStart?: boolean
  ref?: RefObject<CountingRef | null>
  warnValue?: number
  errorValue?: number
}

export interface CountingRef {
  start: () => void
  pause: () => void
  resume: () => void

  reset: (init?: number) => void
  getValue: () => number
}

export default function Counting({
  className,
  autoStart = true,
  ref,
  warnValue,
  errorValue,
}: Readonly<Props>) {
  const [count, setCount] = useState(0)
  const intervalRef = useRef<number>(null)

  useEffect(() => {
    if (autoStart) {
      intervalRef.current = window.setInterval(() => {
        setCount((prev) => prev + 1)
      }, 1000)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useImperativeHandle(
    ref,
    () => ({
      start: () => {
        if (intervalRef.current) return
        runInterval()
      },
      pause: () => {
        clearInterval(intervalRef.current ?? -1)
        intervalRef.current = null
      },
      resume: () => {
        if (intervalRef.current) return
        runInterval()
      },
      reset: (init = 0) => {
        setCount(init)
      },
      getValue: () => count,
    }),
    [count],
  )

  const runInterval = () => {
    intervalRef.current = window.setInterval(() => {
      setCount((prev) => prev + 1)
    }, 1000)
  }

  return (
    <div
      className={twMerge(
        'h-6 rounded-lg bg-[#DCFAE6] flex items-center min-w-[73px] justify-center text-[#067647] font-semibold gap-2',
        warnValue && count >= warnValue && 'text-amber-500 bg-amber-100',
        errorValue && count >= errorValue && 'text-error bg-red-100',
        className,
      )}
    >
      <ClockIcon />
      <span className="text-sm font-semibold">{formatTime(count)}</span>
    </div>
  )
}
