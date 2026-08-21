import React from 'react'
import { twMerge } from 'tailwind-merge'
import emptyIcon from '~/assets/empty.svg'

interface Props {
  className?: string
  label?: string
}

export default function Empty({ className, label }: Readonly<Props>) {
  return (
    <div className={twMerge('flex justify-center items-center flex-col gap-2', className)}>
      <img src={emptyIcon} alt="empty" />
      <p className="font-semibold">{label || 'No data available'}</p>
    </div>
  )
}
