import type { ReactNode } from 'react'
import { twMerge } from 'tailwind-merge'

interface Props {
  children: ReactNode
  className?: string
}

export default function Badge({ children, className }: Readonly<Props>) {
  return (
    <span
      className={twMerge(
        'flex items-center justify-center rounded-full text-xs border h-5 min-w-5 w-fit px-1',
        className,
      )}
    >
      {children}
    </span>
  )
}
