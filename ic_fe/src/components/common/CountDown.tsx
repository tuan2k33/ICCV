import { memo, useEffect, useImperativeHandle, useRef, useState, type RefObject } from 'react'
import { twMerge } from 'tailwind-merge'
import { formatTime } from '~/utils/formatTime'

interface Props {
  initCount: number
  /**
   * This shouldn't be changed dynamically
   */
  autoStart?: boolean
  ref?: RefObject<CountDownRef | null>
  className?: string
  radius?: number
  stroke?: number
  onFinish?: () => void
}

export interface CountDownRef {
  start: () => void
  pause: () => void
  resume: () => void

  /**
   * @param init - The new initial count
   */
  reset: (init?: number) => void
}

const TIME_STEP = 1000

function CountDown({
  initCount,
  autoStart = true,
  ref,
  className,
  radius = 26,
  stroke = 2,
  onFinish,
}: Readonly<Props>) {
  const [count, setCount] = useState(initCount)
  const intervalRef = useRef<number>(null)

  useEffect(() => {
    if (count <= 0) {
      clearInterval(intervalRef.current ?? -1)
      intervalRef.current = null
      onFinish?.()
    }

    return () => {
      clearInterval(intervalRef.current ?? -1)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [count])

  useEffect(() => {
    if (autoStart)
      intervalRef.current = window.setInterval(() => {
        setCount((prev) => prev - 1)
      }, TIME_STEP)

    return () => {
      clearTimeout(intervalRef.current ?? -1)
      intervalRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useImperativeHandle(ref, () => ({
    start: () => {
      if (!intervalRef.current) runInterval()
    },
    pause: () => {
      clearInterval(intervalRef.current ?? -1)
      intervalRef.current = null
    },
    resume: () => {
      if (!intervalRef.current) runInterval()
    },
    reset: (init?: number) => {
      setCount(init ?? initCount)
    },
  }))

  const runInterval = () => {
    intervalRef.current = window.setInterval(() => {
      setCount((prev) => prev - 1)
    }, TIME_STEP)
  }

  const normalizedRadius = radius - stroke / 2
  const circumference = 2 * Math.PI * normalizedRadius
  const progress = count / initCount
  const strokeDashoffset = circumference * (1 - progress)

  return (
    <div
      style={{ width: radius * 2, height: radius * 2 }}
      className={twMerge('relative', className)}
    >
      <svg width={radius * 2} height={radius * 2}>
        <circle
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          fill="transparent"
          stroke="#eee"
          strokeWidth={stroke}
        />
        <circle
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          fill="transparent"
          stroke={'var(--color-primary)'}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform={`rotate(-90 ${radius} ${radius})`}
          style={{
            transition: 'stroke-dashoffset 1s linear',
          }}
        />
      </svg>
      <div
        style={{
          width: radius * 2,
          height: radius * 2,
        }}
        className="font-semibold justify-center items-center flex absolute top-0 left-0"
      >
        {formatTime(count)}
      </div>
    </div>
  )
}

export default memo(CountDown)
