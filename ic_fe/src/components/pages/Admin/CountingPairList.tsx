import { useMemo, type ReactNode } from 'react'
import { twMerge } from 'tailwind-merge'
import { useFormik } from 'formik'
import { useSelector } from 'react-redux'

import type { CountingPairListItem, UserCommon } from '~/types/common'
import { TaskStatus, type MapRow } from '~/types/task'
import { useModal } from '~/hooks/useModal'
import { useMutation } from '~/hooks/useMutation'
import type { RootState } from '~/redux'
import { endpoints } from '~/configs/endpoints'
import { toastError } from '~/utils/showErrorToast'
import { toastSuccess } from '~/utils/toastSuccess'

import CheckIcon from '~/assets/icons/check.svg'
import Progress from '~/components/common/Progress'
import Table from '~/components/common/Table'
import TruncatedDisplay from '~/components/common/TruncatedDisplay'
import BaseModal from '~/components/common/BaseModal'
import Input from '~/components/common/Input'
import Select, { type RenderOptionProps, type SelectOption } from '~/components/common/Select'
import Empty from '~/components/common/Empty'

interface Props {
  data: CountingPairListItem[]
  batchTaskData: MapRow[]
  searchValue?: string
  allLinfoxUsers: UserCommon[]
  allUnileverUsers: UserCommon[]
  onUpdatePair: (payload: UpdatePairPayload) => void
}

export interface UpdatePairPayload {
  id: number | null
  code: string | null
  user_id_1: number | null
  fullname_1: string | null
  user_id_2: number | null
  fullname_2: string | null
}

export default function CountingPairList({
  data,
  searchValue,
  batchTaskData,
  allLinfoxUsers,
  allUnileverUsers,
  onUpdatePair,
}: Readonly<Props>) {
  const { batch } = useSelector((state: RootState) => state.app)
  const pairDetailModal = useModal()
  const form = useFormik<UpdatePairPayload>({
    initialValues: {
      id: null,
      code: null,
      user_id_1: null,
      fullname_1: null,
      user_id_2: null,
      fullname_2: null,
    },
    onSubmit(values) {
      if (batch) return handleUpdateChangeUserPair(values)

      onUpdatePair(values)
      pairDetailModal.closeModal()
    },
  })
  const memorizedData = useMemo(() => {
    let dataCloned = data.map((pair) => {
      const clonedPair: CountingPairListItem & { progress?: number } = { ...pair }

      const rackNameMapStatus: Record<string, TaskStatus> = {}
      batchTaskData.forEach((row) => {
        rackNameMapStatus[row.rack_name] = row.status
      })
      clonedPair.progress = clonedPair.racks?.reduce(
        (count, rackName) => count + Number(rackNameMapStatus[rackName] === TaskStatus.COMPLETED),
        0,
      )
      clonedPair.racks = pair.racks?.map((rowName) => {
        const [name, type] = rowName.split('-')
        return `${name} ${type === 'odd' ? 'lẻ' : 'chẵn'}`
      })
      return clonedPair
    })

    if (searchValue) {
      const loweredCaseSearchValue = searchValue.toLowerCase()
      dataCloned = dataCloned.filter(
        (pair) =>
          pair.fullname_1?.toLowerCase().includes(loweredCaseSearchValue) ||
          pair.fullname_2?.toLowerCase().includes(loweredCaseSearchValue) ||
          pair.racks?.some((rowName) => rowName.toLowerCase().includes(loweredCaseSearchValue)),
      )
    }

    return dataCloned
      .map((pair) => ({
        key: pair.code,
        ...pair,
      }))
      .sort((pairA, pairB) => Number(pairA.code) - Number(pairB.code))
  }, [data, searchValue, batchTaskData])

  const updateUserPairMutation = useMutation({
    url: endpoints.COUNTING_GROUP_CHANGE_USER_IN_GROUP,
    method: 'put',
  })

  const handleUpdateChangeUserPair = (payload: UpdatePairPayload) => {
    updateUserPairMutation.mutate(
      {
        body: {
          user_id_1: payload.user_id_1,
          user_id_2: payload.user_id_2,
          fullname_1: payload.fullname_1,
          fullname_2: payload.fullname_2,
          id: payload.id,
        },
      },
      {
        onError() {
          toastError('Cõ lỗi xảy ra')
        },
        onSuccess() {
          pairDetailModal.closeModal()
          onUpdatePair(payload)
          form.resetForm()
          toastSuccess('Cập nhật thành công')
        },
      },
    )
  }

  const renderOptionSelect = (
    option: SelectOption,
    selected: boolean,
    props: RenderOptionProps,
  ) => {
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
          <p>{option.phone as string}</p>
        </div>
        {selected && <CheckIcon className="shrink-0 text-xl text-success" />}
      </button>
    )
  }

  const handleRowClick = (record: CountingPairListItem) => {
    pairDetailModal.openModal()
    form.setValues({
      id: record.id,
      code: record.code,
      user_id_1: record.user_id_1,
      user_id_2: record.user_id_2,
      fullname_1: record.fullname_1,
      fullname_2: record.fullname_2,
    })
  }

  const handleSelectChange = (value: string | number, part: '1' | '2') => {
    const user = (part === '1' ? allLinfoxUsers : allUnileverUsers).find(
      (user) => user.id === value,
    )
    const payload = {
      [`user_id_${part}`]: user?.id,
      [`fullname_${part}`]: user?.fullname,
    }
    form.setValues({ ...form.values, ...payload })
  }

  const renderFullname = (fullname: string | null, isError: boolean) => {
    if (!fullname) return

    let content: string | null | ReactNode = fullname
    if (searchValue && typeof content === 'string') {
      const index = content.toLowerCase().indexOf(searchValue.toLowerCase())
      if (index !== -1) {
        content = (
          <>
            {content.slice(0, index)}
            <span className="bg-[#F2B32C]">{content.slice(index, index + searchValue.length)}</span>
            {content.slice(index + searchValue.length)}
          </>
        )
      }
    }

    if (isError) return <span className="text-error">{content}</span>
    return content
  }

  return (
    <div className="h-full flex flex-col overflow-y-auto relative">
      <Table
        classNames={{
          thead: 'sticky top-0 left-0',
        }}
        columns={[
          {
            key: 'pair',
            dataKey: 'code',
            label: 'Cặp',
            align: 'left',
            width: '4%',
            className: 'pl-6',
            cellClassName: 'px-6',
            render(record) {
              if (!record.user_id_1 || !record.user_id_2)
                return <span className="text-error">{record.code}</span>
              return record.code
            },
          },
          {
            key: 'linfox',
            dataKey: 'fullname_1',
            label: 'Linfox',
            align: 'left',
            width: '24%',
            className: 'px-6',
            cellClassName: 'px-6',
            render(record) {
              return renderFullname(record.fullname_1, !record.user_id_2)
            },
          },
          {
            key: 'unilever',
            dataKey: 'fullname_2',
            label: 'Unilever',
            align: 'left',
            width: '24%',
            className: 'px-6',
            cellClassName: 'px-6',
            render(record) {
              return renderFullname(record.fullname_2, !record.user_id_1)
            },
          },
          {
            key: 'rows',
            label: 'Dãy đếm',
            align: 'left',
            width: '24%',
            className: 'px-6',
            cellClassName: 'px-6',
            render(record) {
              return (
                <TruncatedDisplay
                  content={record.racks?.join(', ') ?? ''}
                  className="line-clamp-1"
                />
              )
            },
          },
          {
            key: 'completed',
            dataKey: 'completed',
            label: 'Hoàn thành',
            align: 'left',
            width: '24%',
            className: 'px-6',
            cellClassName: 'px-6',
            render(record) {
              return (
                <Progress
                  total={record.racks?.length ?? 1}
                  current={record.progress ?? 0}
                  usePercent
                  classNames={{
                    bar: 'W-[unset] grow',
                  }}
                />
              )
            },
          },
        ]}
        dataSource={memorizedData}
        onRow={{
          onClick: handleRowClick,
        }}
      />
      {!data.length && <Empty className="grow" />}
      <BaseModal
        open={pairDetailModal.open}
        title="CHI TIẾT CẶP"
        classNames={{ body: 'w-[560px]' }}
        confirmButton={{
          label: 'Lưu',
          loading: updateUserPairMutation.pending,
          onClick: () => {
            form.submitForm()
          },
        }}
        onRequestClose={() => !updateUserPairMutation.pending && pairDetailModal.closeModal()}
      >
        <div className="grid grid-cols-2 gap-x-5 gap-y-4">
          <Input
            label="Công ty"
            disabled
            value="Linfox"
            classnames={{
              label: 'text-tertiary text-[13px] font-bold',
              labelWrapper: 'bg-transparent',
              wrapper: 'h-13',
            }}
            className="text-tertiary"
          />
          <Input
            label="Công ty"
            disabled
            value="Unilever"
            classnames={{
              label: 'text-tertiary text-[13px] font-bold',
              labelWrapper: 'bg-transparent',
              wrapper: 'h-13',
            }}
            className="text-tertiary"
          />

          <Select
            label="Họ và tên*"
            options={allLinfoxUsers.map((user) => ({
              value: user.id,
              label: user.fullname,
              phone: user.phone_number,
            }))}
            value={form.values.user_id_1}
            stackLabel
            renderOption={renderOptionSelect}
            onChange={(value) => handleSelectChange(value, '1')}
          />
          <Select
            label="Họ và tên*"
            options={allUnileverUsers.map((user) => ({
              value: user.id,
              label: user.fullname,
              phone: user.phone_number,
            }))}
            value={form.values.user_id_2}
            stackLabel
            renderOption={renderOptionSelect}
            onChange={(value) => handleSelectChange(value, '2')}
          />

          <Input
            label="Số điện thoại*"
            disabled
            value="0908765123"
            classnames={{
              label: 'text-tertiary text-[13px] font-bold',
              labelWrapper: 'bg-transparent',
              wrapper: 'h-13',
            }}
            className="text-tertiary"
          />
          <Input
            label="Số điện thoại*"
            disabled
            value="0908765123"
            classnames={{
              label: 'text-tertiary text-[13px] font-bold',
              labelWrapper: 'bg-transparent',
              wrapper: 'h-13',
            }}
            className="text-tertiary"
          />
        </div>
      </BaseModal>
    </div>
  )
}
