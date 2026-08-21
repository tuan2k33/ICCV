import { twMerge } from 'tailwind-merge'

interface Props {
  label: string
  value: string | number
  valueClassname?: string
}

export default function StatisticItem({ label, value, valueClassname }: Readonly<Props>) {
  return (
    <div className="flex justify-between items-center">
      <p>{label}</p>
      <span className={twMerge('font-semibold', valueClassname)}>{value}</span>
    </div>
  )
}
