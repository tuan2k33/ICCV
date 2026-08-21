import type { ReactNode } from 'react'
import { useNavigate } from 'react-router'
import { twMerge } from 'tailwind-merge'
import { TaskStatus, type MapAreaData, type MapRow } from '~/types/task'
import Button from '../Button'

interface Props {
  name: string
  areaData?: MapAreaData
  className?: string
  onRowClick?: (row: MapRow, type: 'odd' | 'even') => void
  renderButtonContent?: (row: MapRow | null, evenOdd: 'even' | 'odd') => ReactNode
}

export default function MapArea({
  name,
  areaData,
  className,
  onRowClick,
  renderButtonContent,
}: Readonly<Props>) {
  const navigate = useNavigate()
  const renderClassName = (status?: TaskStatus) => {
    switch (status) {
      case TaskStatus.NOT_STARTED:
        return 'bg-[#F9FAFB] text-text-secondary border-border-secondary'
      case TaskStatus.IN_PROGRESS:
        return 'bg-[#C2DAFB] text-[#175CD3] border-[#99CDF9]'
      case TaskStatus.REVIEW:
      case TaskStatus.COMPLETED:
        return 'bg-[#B4EAD1] text-[#067647] border-success'
      default:
        return ''
    }
  }

  const handleClick = (row: MapRow | null, type: 'odd' | 'even') => {
    if (onRowClick) return onRowClick(row!, type)
    if (!row?.id || row?.status !== TaskStatus.COMPLETED) return
    navigate(`/checker/${row.id}`)
  }

  return (
    <div className={className}>
      <h2 className="text-center text-xl font-semibold text-black">{name}</h2>
      <div className="mt-3">
        {areaData?.map((pack, index) => (
          <div key={`pack-${index}`} className="grid grid-cols-5 gap-2.5 not-first:mt-5">
            {pack.map((row, index) => (
              <div key={`row-${index}`}>
                <Button
                  className={twMerge(
                    'h-6 rounded-md text-sm justify-start px-2',
                    renderClassName(row.even?.status),
                    !row.even && 'invisible pointer-events-none select-none',
                  )}
                  outline
                  onClick={() => {
                    handleClick(row.even, 'even')
                  }}
                >
                  {renderButtonContent ? (
                    renderButtonContent(row.even, 'even')
                  ) : (
                    <>
                      {row.even?.rack_name} <span className="mx-auto">c</span>
                    </>
                  )}
                </Button>
                <Button
                  className={twMerge(
                    'h-6 rounded-md text-sm justify-between px-2 mt-2.5',
                    renderClassName(row.odd?.status),
                    !row.odd && 'invisible pointer-events-none select-none',
                  )}
                  outline
                  onClick={() => {
                    handleClick(row.odd, 'odd')
                  }}
                >
                  {renderButtonContent ? (
                    renderButtonContent(row.odd, 'odd')
                  ) : (
                    <>
                      {row.odd?.rack_name} <span className="mx-auto">l</span>
                    </>
                  )}
                </Button>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
