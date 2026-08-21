import { useId, useState, type InputHTMLAttributes, type ReactNode } from 'react'
import { LuEye, LuEyeOff } from 'react-icons/lu'
import { twMerge } from 'tailwind-merge'
import InputError from './InputError'

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, 'prefix'> {
  label?: string
  classnames?: {
    wrapper?: string
    label?: string
    labelWrapper?: string
  }
  error?: string
  touched?: boolean
  errorStatusWithOutMessage?: boolean
  stackLabel?: boolean
  bubbleLabel?: boolean
  prefix?: ReactNode
}

export default function Input({
  label,
  type,
  className,
  classnames,
  id,
  error,
  touched,
  errorStatusWithOutMessage,
  stackLabel = true,
  bubbleLabel = false,
  prefix,
  disabled,
  ...props
}: Readonly<Props>) {
  const [inputType, setInputType] = useState(type)
  const inputId = useId()

  return (
    <div className="relative">
      {label && !bubbleLabel && (
        <label
          htmlFor={id || inputId}
          className={twMerge(
            'text-xs w-fit block relative z-2 font-semibold leading-6',
            stackLabel && 'bg-white px-1 absolute top-0 left-2 -translate-y-1/2',
            classnames?.label,
            disabled && 'bg-transparent opacity-80 cursor-not-allowed backdrop-blur-xs',
          )}
        >
          {label}
        </label>
      )}
      <div
        className={twMerge(
          'relative border rounded-lg border-border-primary duration-200 [&:has(.error)]:border-border-error',
          'shadow-[0_1px_2px_#1018280D] [&:has(.error)]:shadow-[0_0_0_3px_#FDA29B3D] h-10',
          (error || errorStatusWithOutMessage) && touched
            ? 'border-border-error shadow-[0_0_0_3px_#FDA29B3D]'
            : 'focus-within:border-primary',
          classnames?.wrapper,
        )}
      >
        <label
          htmlFor={id || inputId}
          className={twMerge(
            'flex items-center cursor-text pl-3.5 text-sm text-text-primary h-full peer',
            disabled && 'bg-[#EAECF0] cursor-not-allowed',
            classnames?.labelWrapper,
          )}
        >
          {prefix && <div className="select-none">{prefix}</div>}
          <input
            id={id || inputId}
            type={inputType}
            disabled={disabled}
            {...props}
            className={twMerge(
              'border-none outline-none pr-3.5 w-full h-full grow autofill:inset-shadow-[1000px_1000px_0_#ffffff] rounded-lg',
              type === 'password' && 'pr-7',
              className,
              disabled && 'cursor-not-allowed',
            )}
          />
        </label>
        {type === 'password' && (
          <button
            type="button"
            className="absolute right-2 top-1/2 -translate-y-1/2"
            onClick={() => setInputType(inputType === 'password' ? 'text' : 'password')}
          >
            {inputType === 'password' ? <LuEye /> : <LuEyeOff />}
          </button>
        )}
        {label && bubbleLabel && (
          <label
            htmlFor={id || inputId}
            className={twMerge(
              'text-sm w-fit block absolute z-2 text-tertiary leading-6 top-1/2 -translate-y-1/2 left-3 duration-200',
              'peer-[:has(input:not(:placeholder-shown))]:top-0 peer-[:has(input:not(:placeholder-shown))]:bg-white px-1',
              'peer-[:has(input:not(:placeholder-shown))]:text-[13px] peer-[:has(input:not(:placeholder-shown))]:text-text-secondary',
              'peer-[:has(input:not(:placeholder-shown))]:font-semibold',
              classnames?.label,
              disabled && 'bg-transparent opacity-80 cursor-not-allowed backdrop-blur-xs',
            )}
          >
            {label}
          </label>
        )}
      </div>
      <InputError error={touched && error ? error : undefined} />
    </div>
  )
}
