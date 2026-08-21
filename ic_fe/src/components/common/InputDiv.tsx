import { useEffect, useId, useRef, type HTMLAttributes, type RefObject } from 'react'
import { twMerge } from 'tailwind-merge'
import InputError from './InputError'

interface Props extends HTMLAttributes<HTMLDivElement> {
  placeholder?: string
  label?: string
  classnames?: {
    label?: string
  }
  value?: string
  ref?: RefObject<HTMLDivElement>
  error?: string
  touched?: boolean
}

export default function InputDiv({
  placeholder,
  label,
  id,
  classnames,
  className,
  ref,
  onInput,
  value,
  error,
  touched,
  ...props
}: Readonly<Props>) {
  const inputId = useId()
  const inputRef = useRef<HTMLDivElement>(null)
  const placeholderRef = useRef<HTMLDivElement>(null)

  const handleFocus = () => {
    if (ref?.current) {
      ref.current.focus()
    } else {
      inputRef.current?.focus()
    }
  }

  useEffect(() => {
    if (value) {
      placeholderRef.current?.classList.add('hidden')
    } else {
      placeholderRef.current?.classList.remove('hidden')
    }
  }, [value])

  return (
    <div>
      {label && (
        <label
          htmlFor={id || inputId}
          className={twMerge('text-sm inline-block', classnames?.label)}
          onClick={handleFocus}
        >
          {label}
        </label>
      )}
      <div className="relative">
        <div
          role="textbox"
          id={id || inputId}
          contentEditable
          className={twMerge(
            'outline-none border rounded-md border-gray-200 duration-200 px-2 min-h-9 overflow-hidden',
            'leading-9',
            error && touched ? 'border-red-500' : 'focus:border-primary',
            className,
          )}
          data-placeholder={placeholder}
          ref={ref || inputRef}
          dangerouslySetInnerHTML={{
            __html: value || '',
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
            }
          }}
          onInput={(e) => {
            onInput?.(e)
            const textContent = e.currentTarget.textContent
            if (textContent) {
              placeholderRef.current?.classList.add('hidden')
            } else {
              placeholderRef.current?.classList.remove('hidden')
            }
          }}
          {...props}
        ></div>
        <div
          ref={placeholderRef}
          className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none select-none"
        >
          {placeholder}
        </div>
      </div>
      <InputError error={touched && error ? error : undefined} />
    </div>
  )
}
