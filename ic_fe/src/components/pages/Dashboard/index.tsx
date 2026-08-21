import { useMemo, useState } from 'react'
import type { AxiosError } from 'axios'
import { useGet } from '~/hooks/useGet'
import { endpoints } from '~/configs/endpoints'
import { TaskStatus, type MapAreaData, type MapPack, type MapRow } from '~/types/task'
import { axiosInstance } from '~/utils/axiosInstance'
import { toastError } from '~/utils/showErrorToast'
import Loading from '~/components/common/Loading'
import Empty from '~/components/common/Empty'
import MapArea from '~/components/common/MapArea'
import BatchStatistic from '~/components/common/BatchStatistic'

export default function Dashboard() {
  const [exporting, setExporting] = useState(false)
  const batchData = useGet<{
    data: { tasks: MapRow[]; batch_id: number }
  }>({
    url: endpoints.BATCH_PREVIEW,
  })

  const convertedBatchData = useMemo(() => {
    const result: Record<string, MapAreaData> = {}
    const statistic = {
      total: batchData.response?.data.tasks.length ?? 0,
      inProgress: 0,
      completed: 0,
      notStarted: 0,
    }
    const map = new Map<
      string,
      {
        even: MapRow | null
        odd: MapRow | null
      }
    >()

    let packsMap = new Map<string, MapPack>()

    batchData.response?.data.tasks.forEach((rowData) => {
      const [name, type] = rowData.rack_name.split('-')
      switch (rowData.status) {
        case TaskStatus.NOT_STARTED:
          statistic.notStarted += 1
          break
        case TaskStatus.IN_PROGRESS:
          statistic.inProgress += 1
          break
        case TaskStatus.COMPLETED:
        case TaskStatus.REVIEW:
          statistic.completed += 1
          break
        default:
          break
      }

      if (!map.has(name)) {
        map.set(name, {
          even: null,
          odd: null,
        })
      }
      map.set(name, {
        ...map.get(name)!,
        [type]: rowData,
      })
    })

    map.forEach((v, k) => {
      if (!packsMap.has(k.charAt(0))) packsMap.set(k.charAt(0), [])

      packsMap.set(k.charAt(0), [
        ...packsMap.get(k.charAt(0))!,
        {
          odd: v.odd
            ? {
                rack_name: k,
                status: v.odd.status,
                id: v.odd.id,
              }
            : null,
          even: v.even
            ? {
                rack_name: k,
                status: v.even.status,
                id: v.even.id,
              }
            : null,
        },
      ])

      if (packsMap.get(k.charAt(0))!.length === 5) {
        if (!result[k.charAt(0)]) result[k.charAt(0)] = []

        result[k.charAt(0)].push([...packsMap.get(k.charAt(0))!])
        packsMap.set(k.charAt(0), [])
      }
    })

    packsMap.forEach((pack, k) => {
      if (pack.length) {
        if (!result[k]) result[k] = []
        result[k].push([...pack])
      }
    })

    return {
      result,
      statistic,
    }
  }, [batchData.response?.data])

  const handleExport = async () => {
    try {
      setExporting(true)
      const res = await axiosInstance.get(endpoints.TASK_EXPORT_DATA, {
        params: {
          batch_id: batchData.response?.data.batch_id,
        },
        responseType: 'blob',
      })

      const blob = new Blob([res.data])
      const url = URL.createObjectURL(blob)

      const linkEl = document.createElement('a')
      linkEl.href = url
      linkEl.download = `AI-IC_report_batch_${batchData.response?.data.batch_id}.xlsx`
      linkEl.style.display = 'none'
      document.body.appendChild(linkEl)
      linkEl.click()
      document.body.removeChild(linkEl)
      URL.revokeObjectURL(url)
    } catch (error) {
      if ((error as AxiosError).status === 404) toastError('Không có dữ liệu!')
      else toastError('Có lỗi xảy ra!')
    } finally {
      setExporting(false)
    }
  }

  if (batchData.pending) return <Loading className="h-full" />
  if (!batchData.response?.data.tasks.length) return <Empty className="h-full" />

  return (
    <div className="grid grid-cols-3 p-5 gap-[26px] h-full overflow-y-auto">
      <div>
        <MapArea name="D" areaData={convertedBatchData.result['D']} />
      </div>
      <div className="flex flex-col justify-between">
        <MapArea name="C" areaData={convertedBatchData.result['C']} />
        <BatchStatistic
          {...convertedBatchData.statistic}
          exporting={exporting}
          onExport={handleExport}
        />
      </div>
      <div>
        <MapArea name="A" areaData={convertedBatchData.result['A']} />
        <MapArea name="B" areaData={convertedBatchData.result['B']} className="mt-1.5" />
      </div>
    </div>
  )
}
