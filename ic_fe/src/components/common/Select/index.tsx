import {
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from 'react'
import { twMerge } from 'tailwind-merge'
import CheckIcon from '~/assets/icons/check.svg'
import ChevronDownIcon from '~/assets/icons/chevron-down.svg'
import { useClickOutside } from '~/hooks/useClickOutside'

export type SelectOption = { value: string | number; label: string; className?: string } & Record<
  string,
  unknown
>

export interface RenderOptionProps {
  onClick: () => void
}

export interface SelectRef {
  open: () => void
  close: () => void
}

export interface SelectProps<T extends readonly SelectOption[]> {
  label?: string
  options: T
  value?: T[number]['value'] | null
  placeholder?: string
  className?: string
  error?: string
  touched?: boolean
  errorStatusWithOutMessage?: boolean
  ref?: RefObject<SelectRef | null>
  stackLabel?: boolean
  renderOption?: (option: T[number], selected: boolean, props: RenderOptionProps) => ReactNode
  onChange?: (value: NonNullable<T[number]['value']>) => void
}

export default function Select<T extends readonly SelectOption[]>({
  label,
  options,
  value,
  placeholder = 'Select an option',
  className,
  error,
  errorStatusWithOutMessage,
  touched,
  ref,
  stackLabel,
  renderOption,
  onChange,
}: Readonly<SelectProps<T>>) {
  const [open, setOpen] = useState(false)
  const selectRef = useRef<HTMLDivElement>(null)

  const selected = useMemo(() => options.find((o) => o.value === value), [options, value])

  useClickOutside(selectRef, () => {
    setOpen(false)
  }, [])

  useImperativeHandle(
    ref,
    () => ({
      open() {
        setOpen(true)
      },
      close() {
        setOpen(false)
      },
    }),
    [],
  )

  return (
    <div className={twMerge('relative', className)} ref={selectRef}>
      {label && (
        <label
          className={twMerge(
            'block mb-1 text-[13px] font-semibold text-text-default-secondary',
            stackLabel && 'absolute top-0 left-2 -translate-y-1/2 bg-white z-2 px-1',
          )}
        >
          {label}
        </label>
      )}
      <div className="relative">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className={twMerge(
            'h-13 w-full flex justify-between items-center px-3 border duration-200 border-border-primary rounded-lg shadow-[0_1px_2px_#1018280D] text-left text-sm',
            open && 'border-primary',
            (error || errorStatusWithOutMessage) &&
              touched &&
              'border-[#FF4438] ring-4 ring-[#9E77ED3D]',
          )}
        >
          <span
            className={twMerge(
              'text-sm text-[#757575] truncate',
              selected && 'font-medium text-text-primary',
            )}
          >
            {selected ? selected.label : placeholder}
          </span>
          <ChevronDownIcon
            className={twMerge(
              'duration-200 text-xl text-quaternary shrink-0',
              open && 'rotate-180',
            )}
          />
        </button>

        {open && (
          <div className="max-h-[248px] absolute w-full overflow-hidden z-10 rounded-lg shadow-[0_4px_6px_-2px_#10182808,_0_12px_16px_-4px_#10182814]">
            <ul className="w-full bg-white overflow-y-auto px-1.5 py-1 max-h-[inherit]">
              {options.map((option) => (
                <li key={option.value}>
                  {renderOption ? (
                    renderOption(option, option.value === value, {
                      onClick() {
                        if (option.value !== value) {
                          onChange?.(option.value)
                          setOpen(false)
                        }
                      },
                    })
                  ) : (
                    <button
                      onClick={() => {
                        if (option.value !== value) {
                          onChange?.(option.value)
                          setOpen(false)
                        }
                      }}
                      className={twMerge(
                        'w-full cursor-pointer text-left rounded-md duration-200 hover:bg-[#F2F4F7] h-11 px-2 flex items-center gap-1',
                        option.value === value && 'bg-[#F2F4F7]',
                        option.className,
                      )}
                      type="button"
                    >
                      <span className="truncate">{option.label}</span>
                      {value === option.value && (
                        <CheckIcon className="shrink-0 text-xl text-[#BB1B0F] ml-auto" />
                      )}
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
