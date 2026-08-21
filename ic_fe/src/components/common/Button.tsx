import { type ButtonHTMLAttributes, type ReactNode } from 'react'
import { CgSpinnerAlt } from 'react-icons/cg'
import { twMerge } from 'tailwind-merge'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
  loading?: boolean
  square?: boolean
  circle?: boolean
  outline?: boolean
  subfix?: ReactNode
}

export default function Button({
  children,
  className,
  disabled,
  loading,
  square,
  circle,
  outline,
  subfix,
  ...props
}: Readonly<ButtonProps>) {
  return (
    <button
      className={twMerge(
        'bg-primary text-white px-4 rounded-lg cursor-pointer flex w-full justify-center items-center h-10',
        'relative select-none active:scale-95 duration-200 font-semibold text-xl shadow-[0_1px_2px_#1018280D]',
        'border border-transparent',
        square && 'aspect-square w-[unset] px-0',
        circle && 'rounded-full',
        outline && 'border-border-primary bg-transparent text-text-secondary',
        disabled && 'opacity-50 cursor-not-allowed active:scale-100',
        loading && 'pointer-events-none',
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center backdrop-blur-[1px] rounded-[inherit]">
          <CgSpinnerAlt className="animate-spin" />
        </div>
      )}
      {children}
      {subfix}
    </button>
  )
}
