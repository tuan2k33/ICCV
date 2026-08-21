import type { ReactNode } from 'react'
import { twMerge } from 'tailwind-merge'
import CheckBox from '../CheckBox'

type Key = string | number

interface Column<T> {
  key?: string
  label?: ReactNode
  dataKey?: string
  className?: string
  cellClassName?: string
  align?: 'left' | 'center' | 'right' | 'justify' | 'char'
  width?: string | number
  render?: (record: T, index: number) => ReactNode
}

interface Props<T> {
  columns: Column<T>[]
  dataSource: T[]
  className?: string
  classNames?: {
    row?: string
    thead?: string
  }

  /**
   * key in dataSource to be used as unique identifier for each row (for example: id)
   * If not provided, the index of the row will be used as key
   */
  dataKey?: string
  rowSelection?: {
    selectedKeys: Key[]
    onChange?: (selectedKey: Key[]) => void
  }
  onRow?: {
    onClick?: (record: T) => void
  }
}

export default function Table<
  T extends Record<string, unknown> & {
    key?: Key
  },
>({
  columns,
  dataSource,
  className,
  classNames,
  dataKey,
  rowSelection,
  onRow,
}: Readonly<Props<T>>) {
  const handleSelectRowChange = (key: Key, checked: boolean) => {
    if (checked) rowSelection?.onChange?.([...rowSelection.selectedKeys, key])
    else rowSelection?.onChange?.(rowSelection.selectedKeys.filter((rowKey) => rowKey !== key))
  }

  return (
    <table className={twMerge('w-full', className)}>
      <thead className={twMerge('border-b border-border-secondary bg-white', classNames?.thead)}>
        <tr className="">
          {rowSelection && <th className="w-[68px]"></th>}
          {columns.map((column, index) => (
            <th
              key={column.key || index}
              className={twMerge('text-tertiary-600 font-semibold py-1.5 px-6', column.className)}
              align={column.align ?? 'center'}
              style={{
                width: column.width,
              }}
            >
              {column.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="text-sm">
        {dataSource.map((record, recordIndex) => {
          const rowKey = record.key ?? (dataKey ? (record[dataKey] as Key) : recordIndex)
          return (
            <tr
              key={rowKey}
              className={twMerge(
                'hover:bg-gray-100 border-b border-border-secondary last:border-b-0',
                onRow && 'cursor-pointer',
                classNames?.row,
              )}
              onClick={() => onRow?.onClick?.(record)}
            >
              {rowSelection && (
                <td align="center">
                  <div className="flex justify-center">
                    <CheckBox
                      checked={rowSelection.selectedKeys.includes(rowKey)}
                      onChange={(e) => handleSelectRowChange(rowKey, e.target.checked)}
                    />
                  </div>
                </td>
              )}
              {columns.map((column, columnIndex) => (
                <td
                  key={column.key || columnIndex}
                  align={column.align ?? 'center'}
                  className={twMerge('py-2 px-6', column.cellClassName)}
                >
                  {column.render
                    ? column.render(record, recordIndex)
                    : (record[column.dataKey ?? ''] as ReactNode)}
                </td>
              ))}
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
