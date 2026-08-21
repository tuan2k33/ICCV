import type { ReactNode } from 'react'
import { ImSpinner8 } from 'react-icons/im'
import { twMerge } from 'tailwind-merge'

interface Props {
  className?: string
  label?: ReactNode
}

export default function Loading({ className, label }: Readonly<Props>) {
  return (
    <div
      className={twMerge(
        'flex flex-col items-center justify-center backdrop-blur-xs text-4xl text-primary ',
        className,
      )}
    >
      <ImSpinner8 className="animate-spin" />
      {label}
    </div>
  )
}
