import { twMerge } from 'tailwind-merge'
import Button from '../Button'
import StatisticItem from './StatisticItem'

interface Props {
  total: number
  inProgress: number
  completed: number
  notStarted: number
  exporting: boolean
  className?: string
  exportable?: boolean
  onExport: () => void
}

export default function BatchStatistic({
  completed,
  inProgress,
  notStarted,
  total,
  exporting,
  className,
  exportable = true,
  onExport,
}: Readonly<Props>) {
  return (
    <div
      className={twMerge(
        'self-center py-2.5 px-3 rounded-lg bg-white shadow-[0_4px_10px_#00000026] max-w-full w-[328px]',
        className,
      )}
    >
      <div className="flex justify-between items-center">
        <p className="font-semibold">Dashboard</p>
        <p className="text-sm">Chú thích: c (chẵn), l (lẻ)</p>
      </div>
      <div className="mt-4 py-2.5 text-sm flex flex-col gap-4">
        <StatisticItem
          label="Tổng số dãy (chẵn + lẻ):"
          value={total}
          valueClassname="text-text-secondary"
        />
        <StatisticItem label="Đang đếm:" value={inProgress} valueClassname="text-[#175CD3]" />
        <StatisticItem label="Đã đếm:" value={completed} valueClassname="text-[#067647]" />
        <StatisticItem label="Chưa đếm:" value={notStarted} valueClassname="text-text-secondary" />
      </div>
      <Button
        className="mt-4 h-9 text-sm font-bold bg-success disabled:bg-transparent"
        outline={!exportable}
        loading={exporting}
        disabled={!exportable}
        onClick={onExport}
      >
        Xuất file Excel
      </Button>
    </div>
  )
}
