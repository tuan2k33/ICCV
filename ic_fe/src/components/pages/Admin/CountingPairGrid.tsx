import { useMemo, useState } from 'react'
import { twMerge } from 'tailwind-merge'

import { TaskStatus, type MapAreaData, type MapPack, type MapRow } from '~/types/task'
import type { CountingPairGridItem, CountingPairListItem } from '~/types/common'
import { useModal } from '~/hooks/useModal'
import { useMutation } from '~/hooks/useMutation'
import { endpoints } from '~/configs/endpoints'
import { toastError } from '~/utils/showErrorToast'
import { toastSuccess } from '~/utils/toastSuccess'

import CheckIcon from '~/assets/icons/check.svg'
import MapArea from '~/components/common/MapArea'
import BatchStatistic from '~/components/common/BatchStatistic'
import Badge from '~/components/common/Badge'
import Empty from '~/components/common/Empty'
import BaseModal from '~/components/common/BaseModal'
import Select from '~/components/common/Select'

interface Props {
  batchTaskData: MapRow[]
  gridPairData: CountingPairGridItem[]
  previewPairing?: CountingPairListItem[]
  listCountingPairData: CountingPairListItem[]
  onRowPairChanged: () => void
  onUpdatePreview: (from: string, to: string, name: string) => void
}

export default function CountingPairGrid({
  batchTaskData,
  gridPairData,
  previewPairing,
  listCountingPairData,
  onRowPairChanged,
  onUpdatePreview,
}: Readonly<Props>) {
  const changePairModal = useModal()
  const [editingRow, setEditingRow] = useState<
    (MapRow & { type: 'odd' | 'even'; newPair?: string }) | null
  >(null)

  const convertedBatchData = useMemo(() => {
    const result: Record<string, MapAreaData> = {}
    const statistic = {
      total: batchTaskData.length ?? 0,
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

    const rackNameMapPairCode: Record<string, string | number> = {}
    gridPairData.forEach((item) => {
      rackNameMapPairCode[item.rack_name] = item.code
    })

    const findPairId = (rackName: string) => {
      return rackNameMapPairCode[rackName]
    }

    batchTaskData.forEach((rowData) => {
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
                pairId: findPairId(`${k}-odd`),
              }
            : null,
          even: v.even
            ? {
                rack_name: k,
                status: v.even.status,
                id: v.even.id,
                pairId: findPairId(`${k}-even`),
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
  }, [batchTaskData, gridPairData])

  const previewPair = useMemo(() => {
    if (!previewPairing) return null

    type Row = { name: string; pairId: string }

    const rows: Row[] = []
    previewPairing.forEach((pair) => {
      pair.racks?.forEach((row) => {
        rows.push({
          name: row,
          pairId: pair.code,
        })
      })
    })

    rows.sort((rowA, rowB) => rowA.name.localeCompare(rowB.name))

    const result: Record<string, MapAreaData> = {}
    const statistic = {
      total: rows.length ?? 0,
      inProgress: 0,
      completed: 0,
      notStarted: rows.length ?? 0,
    }
    let packsMap = new Map<string, MapPack>()
    const map = new Map<
      string,
      {
        even: Row | null
        odd: Row | null
      }
    >()

    rows.forEach((row) => {
      const [name, type] = row.name.split('-')
      if (!map.has(name)) {
        map.set(name, {
          even: null,
          odd: null,
        })
      }

      map.set(name, {
        ...map.get(name)!,
        [type]: row,
      })
    })

    map.forEach((value, key) => {
      if (!packsMap.has(key.charAt(0))) packsMap.set(key.charAt(0), [])

      packsMap.set(key.charAt(0), [
        ...packsMap.get(key.charAt(0))!,
        {
          even: value.even
            ? {
                rack_name: key,
                status: TaskStatus.NOT_STARTED,
                pairId: value.even.pairId,
                id: -1, // ignore
              }
            : null,
          odd: value.odd
            ? {
                rack_name: key,
                status: TaskStatus.NOT_STARTED,
                pairId: value.odd.pairId,
                id: -1, // ignore
              }
            : null,
        },
      ])

      if (packsMap.get(key.charAt(0))!.length === 5) {
        if (!result[key.charAt(0)]) result[key.charAt(0)] = []

        result[key.charAt(0)].push([...packsMap.get(key.charAt(0))!])
        packsMap.set(key.charAt(0), [])
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
  }, [previewPairing])

  const changePairMutation = useMutation({
    method: 'post',
    url: endpoints.COUNTING_GROUP_MOVE_RACK,
  })

  const renderButtonContent = (row: MapRow | null, evenOdd: 'even' | 'odd') => {
    if (!row) return null
    return (
      <>
        {row.rack_name} <span className="mx-auto text-xs">{evenOdd === 'even' ? 'c' : 'l'}</span>
        <Badge className="h-[18px] px-0.5 min-w-[18px] text-[10px] text-error-secondary bg-[#FFB5B0]">
          {row.pairId}
        </Badge>
      </>
    )
  }

  const handleRowClick = (row: MapRow | null, type: 'odd' | 'even') => {
    if (!row || row.status === TaskStatus.COMPLETED) return
    setEditingRow({ ...row, type })
    changePairModal.openModal()
  }

  const handleCancelEdit = () => {
    if (changePairMutation.pending) return
    changePairModal.closeModal()
    setEditingRow(null)
  }

  const handleUpdateChangePair = () => {
    if (!editingRow?.newPair || editingRow.newPair === editingRow.pairId) {
      return handleCancelEdit()
    }

    const rackName = `${editingRow.rack_name}-${editingRow.type}`

    if (previewPairing) {
      onUpdatePreview(editingRow.pairId as string, editingRow.newPair, rackName)
      handleCancelEdit()
      return
    }

    let oldID: number | null = null,
      newID: number | null = null

    for (const countingPair of listCountingPairData) {
      if (countingPair.code === editingRow.pairId) oldID = countingPair.id
      if (countingPair.code === editingRow.newPair) newID = countingPair.id

      if (oldID && newID) break
    }

    changePairMutation.mutate(
      {
        body: {
          rack_name: rackName,
          group_from_id: oldID,
          group_to_id: newID,
        },
      },
      {
        onError() {
          toastError('Có lỗi xảy ra')
        },
        onSuccess() {
          toastSuccess('Cập nhật thành công')
          onRowPairChanged()
        },
      },
    )
  }

  if ((!batchTaskData.length || !gridPairData.length) && !previewPairing?.length)
    return <Empty className="h-full" />

  return (
    <>
      <div className="grid grid-cols-3 p-5 gap-[26px] h-full overflow-y-auto">
        <div>
          <MapArea
            name="D"
            areaData={convertedBatchData.result['D'] ?? previewPair?.result['D']}
            renderButtonContent={renderButtonContent}
            onRowClick={handleRowClick}
          />
        </div>
        <div className="flex flex-col justify-between">
          <MapArea
            name="C"
            areaData={convertedBatchData.result['C'] ?? previewPair?.result['C']}
            renderButtonContent={renderButtonContent}
            onRowClick={handleRowClick}
          />
          <BatchStatistic
            {...(previewPair?.statistic ?? convertedBatchData.statistic)}
            exporting={false}
            exportable={false} // TODO
            onExport={() => {}}
          />
        </div>
        <div>
          <MapArea
            name="A"
            areaData={convertedBatchData.result['A'] ?? previewPair?.result['A']}
            renderButtonContent={renderButtonContent}
            onRowClick={handleRowClick}
          />
          <MapArea
            name="B"
            areaData={convertedBatchData.result['B'] ?? previewPair?.result['B']}
            className="mt-1.5"
            renderButtonContent={renderButtonContent}
            onRowClick={handleRowClick}
          />
        </div>
      </div>
      <BaseModal
        open={changePairModal.open}
        title="THAY CẶP ĐẾM"
        classNames={{
          body: 'w-[448px]',
        }}
        onRequestClose={handleCancelEdit}
        confirmButton={{
          label: 'Cập nhật',
          loading: changePairMutation.pending,
          onClick: handleUpdateChangePair,
        }}
      >
        <div>
          <p>
            Dãy:{' '}
            <span className="font-bold">
              {editingRow?.rack_name} {editingRow?.type === 'even' ? 'chẵn' : 'lẻ'}
            </span>
          </p>
          <Select
            label="Cặp đếm"
            stackLabel
            value={editingRow?.newPair ?? (editingRow?.pairId as string)}
            options={[...(previewPairing ?? listCountingPairData)]
              .sort((pairA, pairB) => +pairA.code - +pairB.code)
              .map((countingPair) => ({
                value: countingPair.code,
                label: countingPair.code,
                user1: countingPair.fullname_1,
                user2: countingPair.fullname_2,
              }))}
            className="mt-10"
            renderOption={(option, selected, props) => {
              return (
                <button
                  {...props}
                  className={twMerge(
                    'text-xs flex items-center justify-between w-full text-left py-1 px-1.5 hover:bg-[#EAECF0B2] rounded-md leading-5 mt-1.5',
                    selected && 'bg-[#EAECF0B2]',
                  )}
                >
                  <div>
                    <p className="text-[#1C252E] font-semibold">{option.label}</p>
                    <p className="truncate">
                      {option.user1} - {option.user2}
                    </p>
                  </div>
                  {selected && <CheckIcon className="shrink-0 text-xl text-success" />}
                </button>
              )
            }}
            onChange={(value) => {
              setEditingRow((prev) => ({ ...prev!, newPair: value }))
            }}
          />
        </div>
      </BaseModal>
    </>
  )
}
