import { twMerge } from 'tailwind-merge'

interface Props {
  current: number
  total: number
  usePercent?: boolean
  classNames?: {
    bar?: string
    progressBar?: string
    label?: string
    wrapper?: string
  }
}

export default function Progress({ current, total, classNames, usePercent }: Readonly<Props>) {
  return (
    <div className={twMerge('flex items-center gap-3', classNames?.wrapper)}>
      <div
        className={twMerge(
          'w-[278px] rounded-full h-2 bg-[#EAECF0] overflow-hidden',
          classNames?.bar,
        )}
      >
        <div
          className={twMerge(
            'h-full rounded-full bg-blue-secondary duration-200',
            classNames?.progressBar,
          )}
          style={{
            width: `${((current ?? 0) * 100) / (total || 1)}%`,
          }}
        ></div>
      </div>
      <span className={twMerge('text-text-secondary font-medium', classNames?.label)}>
        {usePercent
          ? `${Number(((current * 100) / (total || 1)).toFixed(1))}%`
          : `${current}/${total}`}
      </span>
    </div>
  )
}
