import { useId, type InputHTMLAttributes, type RefAttributes } from 'react'
import { twMerge } from 'tailwind-merge'
import CheckCheckboxIcon from '~/assets/icons/check-checkbox.svg'

interface Props extends InputHTMLAttributes<HTMLInputElement>, RefAttributes<HTMLInputElement> {
  label?: string
  classNames?: {
    label?: string
    wrapper?: string
  }
}

export default function CheckBox({
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
        'cursor-pointer flex items-center gap-2',
        disabled && 'cursor-not-allowed',
        classNames?.wrapper,
      )}
      tabIndex={0}
    >
      <div
        className={twMerge(
          'h-4 w-4 rounded-sm border border-border-primary flex items-center justify-center',
          checked && 'border-blue-secondary bg-blue-secondary',
        )}
      >
        <CheckCheckboxIcon className={twMerge('text-xs text-white hidden', checked && 'block')} />
      </div>
      <input
        tabIndex={-1}
        id={id ?? _id}
        type="checkbox"
        className="hidden"
        checked={checked}
        disabled={disabled}
        {...props}
      />
      {label && <span className={classNames?.label}>{label}</span>}
    </label>
  )
}
