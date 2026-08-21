import { useMemo, useState, type ChangeEvent } from 'react'
import { twMerge } from 'tailwind-merge'
import { useDispatch, useSelector } from 'react-redux'
import { AxiosError } from 'axios'

import { useGet } from '~/hooks/useGet'
import { useMutation } from '~/hooks/useMutation'
import { useModal } from '~/hooks/useModal'
import { endpoints } from '~/configs/endpoints'
import { ErrorCode } from '~/configs/errorCode'
import type { AppDispatch, RootState } from '~/redux'
import { actionThunkGetActiveBatch } from '~/redux/slices/app'
import type { CountingPairGridItem, CountingPairListItem, UserCommon } from '~/types/common'
import { type MapRow } from '~/types/task'
import { Role } from '~/types/auth'
import { toastError } from '~/utils/showErrorToast'
import { debounce } from '~/utils/debounce'
import { formatDateTime } from '~/utils/formatDateTime'
import { toastSuccess } from '~/utils/toastSuccess'

import ExcelDownloadIcon from '~/assets/icons/excel-download.svg'
import GridIcon from '~/assets/icons/grid.svg'
import ListIcon from '~/assets/icons/list.svg'
import RefreshIcon from '~/assets/icons/refresh.svg'
import SearchIcon from '~/assets/icons/search.svg'
import CheckCircleIcon from '~/assets/icons/check-circle.svg'
import AlertCircleIcon from '~/assets/icons/alert-circle.svg'
import Button from '~/components/common/Button'
import Input from '~/components/common/Input'
import Loading from '~/components/common/Loading'
import BaseModal from '~/components/common/BaseModal'
import CountingPairList, { type UpdatePairPayload } from './CountingPairList'
import CountingPairGrid from './CountingPairGrid'

interface Props {
  listCountingPairData: ReturnType<typeof useGet<{ data: CountingPairListItem[] }>>
}

export default function CountingPairTab({ listCountingPairData }: Readonly<Props>) {
  const [displayMode, setDisplayMode] = useState<'list' | 'grid'>('list')
  const [searchValue, setSearchValue] = useState('')
  const { user } = useSelector((state: RootState) => state.auth)
  const { batch } = useSelector((state: RootState) => state.app)
  const dispatch = useDispatch<AppDispatch>()
  const confirmParingModal = useModal()

  const gridCountingPairData = useGet<{
    data: CountingPairGridItem[]
  }>(
    {
      url: endpoints.COUNTING_GROUP,
      config: {
        params: {
          convert_racks: true,
          batch_id: batch,
        },
      },
    },
    {
      disabled: !batch,
    },
  )

  const batchData = useGet<{
    data: { tasks: MapRow[]; batch_id: number }
  }>(
    {
      url: endpoints.BATCH_PREVIEW,
    },
    {
      disabled: !batch,
    },
  )

  const allLinfoxCounters = useGet<{
    data: UserCommon[]
  }>({
    url: endpoints.USER_FETCH_ALL,
    config: {
      params: {
        roles: Role.ENTRY,
        company: 'Linfox', // TODO
      },
    },
  })

  const allUnileverCounters = useGet<{
    data: UserCommon[]
  }>({
    url: endpoints.USER_FETCH_ALL,
    config: {
      params: {
        roles: Role.ENTRY,
        company: 'Unilever', // TODO
      },
    },
  })

  const rePairingMutation = useMutation<{
    data: CountingPairListItem[]
  }>({
    url: endpoints.COUNTING_GROUP_RANDOM,
    method: 'post',
    config: {
      params: {
        tenant_id: user?.tenant_id,
        batch_id: batch,
      },
    },
  })

  const exportExcelMutation = useMutation<Blob>({
    method: 'post',
    url: endpoints.COUNTING_GROUP_EXPORT,
    config: {
      responseType: 'blob',
      params: {
        batch_id: batch,
      },
    },
  })

  const submitPairMutation = useMutation({
    url: endpoints.COUNTING_GROUP_SUBMIT,
    method: 'post',
  })

  const handleSearchChange = useMemo(
    () =>
      debounce((e: ChangeEvent<HTMLInputElement>) => {
        setSearchValue(e.target.value)
      }),
    [],
  )

  const handleRePairing = () => {
    rePairingMutation.mutate(
      {},
      {
        onError(e) {
          const error_code = (e as AxiosError<Record<string, any>>).response?.data?.detail
            ?.error_code
          toastError(
            error_code === ErrorCode.ERROR_TASK_IN_PROGRESS
              ? 'Đã có nhiệm vụ đang tiến hành, không thể thực hiện'
              : 'Có lỗi xảy ra',
          )
        },
      },
    )
  }

  const handleExportExcel = () => {
    exportExcelMutation.mutate(
      {},
      {
        onSuccess(response) {
          const objectUrl = URL.createObjectURL(response)
          const link = document.createElement('a')
          link.href = objectUrl
          link.download = `Danh_sach_cap_dem_${formatDateTime(new Date(), 'YYYYMMDD')}.xlsx`

          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          URL.revokeObjectURL(objectUrl)
        },
        onError() {
          toastError('Có lỗi xảy ra')
        },
      },
    )
  }

  const handleUpdatePair = (payload: UpdatePairPayload) => {
    if (batch) return listCountingPairData.reFetch()

    rePairingMutation.setResponse((prev) => {
      if (!prev) return prev
      const newState = { ...prev }
      let targetPair = null,
        affectedPair1 = null,
        affectedPair2 = null

      for (const pair of newState.data) {
        if (targetPair && affectedPair1 && affectedPair2) break

        if (payload.code === pair.code) targetPair = pair

        if (payload.user_id_1 === pair.user_id_1 && payload.user_id_1 !== targetPair?.user_id_1)
          affectedPair1 = pair
        if (payload.user_id_2 === pair.user_id_2 && payload.user_id_2 !== targetPair?.user_id_2)
          affectedPair2 = pair
      }

      if (!targetPair) return prev

      if (affectedPair1) {
        const tmp = {
          userId: targetPair.user_id_1,
          fullname: targetPair.fullname_1,
        }

        targetPair.user_id_1 = payload.user_id_1
        targetPair.fullname_1 = payload.fullname_1

        affectedPair1.user_id_1 = tmp.userId
        affectedPair1.fullname_1 = tmp.fullname
      }

      if (affectedPair2) {
        const tmp = {
          userId: targetPair.user_id_2,
          fullname: targetPair.fullname_2,
        }

        targetPair.user_id_2 = payload.user_id_2
        targetPair.fullname_2 = payload.fullname_2

        affectedPair2.user_id_2 = tmp.userId
        affectedPair2.fullname_2 = tmp.fullname
      }

      return newState
    })
  }

  const handleSubmitPair = () => {
    submitPairMutation.mutate(
      {
        body: {
          tenant_id: user?.tenant_id,
          data: rePairingMutation.response?.data,
        },
      },
      {
        onError() {
          toastError('Có lỗi xảy ra')
        },
        onSuccess() {
          dispatch(actionThunkGetActiveBatch(user?.tenant_id!))
          rePairingMutation.setResponse(null)
        },
      },
    )
  }

  const handleChangPairOfTaskPreview = (from: string, to: string, name: string) => {
    rePairingMutation.setResponse((prev) => {
      if (!prev?.data.length) return prev

      const newState = { ...prev }

      for (const countingPair of newState.data) {
        if (countingPair.code === from) {
          const index = countingPair.racks?.indexOf(name)

          if (index && index !== -1) countingPair.racks?.splice(index, 1)
        }

        if (countingPair.code === to) {
          countingPair.racks = [...(countingPair.racks ?? []), name]
        }
      }

      newState.data = [...newState.data]
      return newState
    })
    toastSuccess('Cập nhật thành công')
  }

  const handleChangeDisplayMode = (mode: 'list' | 'grid') => {
    setDisplayMode(mode)
    if (mode === 'list') {
      allLinfoxCounters.reFetch()
      allUnileverCounters.reFetch()
    } else {
      gridCountingPairData.reFetch()
    }
    if (!batch) dispatch(actionThunkGetActiveBatch(user?.tenant_id!))

    listCountingPairData.reFetch()
    batchData.reFetch()
    setSearchValue('')
  }

  const renderContent = () => {
    if (listCountingPairData.pending || gridCountingPairData.pending || batchData.pending)
      return <Loading className="grow" />

    return (
      <div className="grow overflow-hidden relative">
        {rePairingMutation.pending && <Loading className="absolute inset-0 z-10" />}
        {displayMode === 'list' ? (
          <CountingPairList
            searchValue={searchValue}
            batchTaskData={batchData.response?.data.tasks ?? []}
            data={listCountingPairData.response?.data ?? rePairingMutation.response?.data ?? []}
            allLinfoxUsers={allLinfoxCounters.response?.data ?? []}
            allUnileverUsers={allUnileverCounters.response?.data ?? []}
            onUpdatePair={handleUpdatePair}
          />
        ) : (
          <CountingPairGrid
            batchTaskData={batchData.response?.data.tasks ?? []}
            gridPairData={gridCountingPairData.response?.data ?? []}
            previewPairing={rePairingMutation.response?.data}
            listCountingPairData={listCountingPairData.response?.data ?? []}
            onRowPairChanged={() => {
              listCountingPairData.reFetch()
              gridCountingPairData.reFetch()
              batchData.reFetch()
            }}
            onUpdatePreview={handleChangPairOfTaskPreview}
          />
        )}
      </div>
    )
  }

  return (
    <div className="h-full px-4 pb-3 flex flex-col gap-2">
      <div className="flex items-center py-2 gap-3 shrink-0">
        {displayMode === 'list' ? (
          <Input
            placeholder="Tìm người đếm, tên dãy"
            prefix={<SearchIcon className="text-xl mr-1" />}
            classnames={{
              wrapper: 'max-w-[300px]',
            }}
            readOnly={listCountingPairData.pending || batchData.pending}
            onChange={handleSearchChange}
          />
        ) : (
          <span className="text-xs italic text-primary flex items-center gap-1">
            <AlertCircleIcon /> Nhấn để thay đổi cặp đếm
          </span>
        )}

        <span className="ml-auto invisible"></span>
        {!batch && (
          <>
            <Button
              className="w-fit text-sm gap-1 px-3.5 text-blue-secondary border-current disabled:text-text-default-secondary"
              outline
              disabled={!!batch}
              loading={rePairingMutation.pending}
              onClick={handleRePairing}
            >
              Ghép cặp {(rePairingMutation.response?.data || batchData.response?.data) && 'lại'}
              <RefreshIcon className="text-lg" />
            </Button>
            {rePairingMutation.response?.data.length && (
              <Button
                className="w-fit px-3.5 text-sm text-[#067647] border-current bg-[#DCFAE6] gap-1"
                outline
                disabled={rePairingMutation.pending}
                loading={submitPairMutation.pending}
                onClick={handleSubmitPair}
              >
                Xác nhận <CheckCircleIcon className="text-xl" />
              </Button>
            )}
          </>
        )}
        <Button
          className="w-fit text-sm gap-1 px-3.5"
          outline
          disabled={displayMode !== 'list' || !batchData.response}
          loading={exportExcelMutation.pending}
          onClick={handleExportExcel}
        >
          <ExcelDownloadIcon className="text-xl" />
          Xuất file Excel
        </Button>
        <div className="flex items-center gap-0.4 border border-border-secondary rounded-lg">
          <button className="p-2" onClick={() => handleChangeDisplayMode('list')}>
            <ListIcon
              className={twMerge(
                'text-2xl text-[#64748B] rounded-xs',
                displayMode === 'list' && 'bg-border-primary',
              )}
            />
          </button>
          <button className="p-2" onClick={() => handleChangeDisplayMode('grid')}>
            <GridIcon
              className={twMerge(
                'text-2xl text-[#64748B] rounded-xs',
                displayMode === 'grid' && 'bg-border-primary',
              )}
            />
          </button>
        </div>
      </div>

      {renderContent()}

      <BaseModal
        title="XÁC NHẬN GHÉP CẶP"
        open={confirmParingModal.open}
        classNames={{
          body: 'w-[448px]',
        }}
        onRequestClose={() => !submitPairMutation.pending && confirmParingModal.closeModal()}
        confirmButton={{
          icon: <CheckCircleIcon className="text-base" />,
          label: 'Xác nhận',
          loading: submitPairMutation.pending,
          onClick: handleSubmitPair,
        }}
      >
        <p>
          Sau khi xác nhận, hệ thống sẽ khóa các cặp đếm và bạn sẽ không thể chỉnh sửa nữa. <br />
          <br />
          Bạn có chắc chắn muốn xác nhận ghép cặp?
        </p>
      </BaseModal>
    </div>
  )
}
