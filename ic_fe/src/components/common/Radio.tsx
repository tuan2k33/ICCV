import { useId, type InputHTMLAttributes, type RefAttributes } from 'react'
import { twMerge } from 'tailwind-merge'

interface Props extends InputHTMLAttributes<HTMLInputElement>, RefAttributes<HTMLInputElement> {
  label?: string
  classNames?: {
    label?: string
    dot?: string
  }
}

export default function Radio({
  id,
  label,
  classNames,
  checked,
  disabled,
  ...props
}: Readonly<Props>) {
  const _id = useId()
  return (
    <label
      htmlFor={id ?? _id}
      className={twMerge(
        'cursor-pointer flex items-center gap-2 text-sm',
        disabled && 'cursor-not-allowed',
        classNames?.label,
      )}
      tabIndex={0}
    >
      <div
        className={twMerge(
          'h-4 w-4 rounded-full border border-border-primary flex items-center justify-center',
          checked && 'border-blue-secondary bg-blue-secondary',
        )}
      >
        <span
          className={twMerge('bg-white w-1.5 h-1.5 block rounded-full', classNames?.dot)}
        ></span>
      </div>
      <input
        tabIndex={-1}
        id={id ?? _id}
        type="radio"
        className="hidden"
        checked={checked}
        disabled={disabled}
        {...props}
      />
      {label && <span>{label}</span>}
    </label>
  )
}
