import { useEffect, useRef } from 'react'
import { twMerge } from 'tailwind-merge'
import type { Pallet } from '~/types/task'
import Button from '~/components/common/Button'

interface Props {
  pallets: Pallet[]
  currentPosition: number
  onChange: (index: number) => void
}

export default function PalletButtons({ pallets, currentPosition, onChange }: Readonly<Props>) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [pallets])

  return (
    <div ref={containerRef} className="overflow-y-auto scrollbar-xs shrink-0">
      <div className="flex gap-6 flex-col-reverse items-center justify-center min-h-full">
        {pallets.map((item, index) => (
          <Button
            key={item.name}
            className={twMerge(
              'w-fit block h-[30px] text-sm ',
              item.data._is_finished && 'text-success px-2',
              item.data._need_confirm && 'text-error',
              currentPosition === index && 'text-white',
            )}
            outline={currentPosition !== index}
            type="button"
            square
            onClick={() => {
              if (currentPosition !== index) onChange(index)
            }}
          >
            {item.name.split('-').pop()}{' '}
          </Button>
        ))}
      </div>
    </div>
  )
}
