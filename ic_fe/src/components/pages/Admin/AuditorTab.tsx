import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react'
import { useFormik } from 'formik'
import { useSelector } from 'react-redux'
import { twMerge } from 'tailwind-merge'
import { ImSpinner8 } from 'react-icons/im'

import type { UserCommon } from '~/types/common'
import { Role } from '~/types/auth'
import { endpoints } from '~/configs/endpoints'
import { UpdateUserSchema } from '~/configs/schemas'
import { useMutation } from '~/hooks/useMutation'
import { useModal } from '~/hooks/useModal'
import { useGenerateUsername } from '~/hooks/useGenerateUsername'
import { useInfiniteGet } from '~/hooks/useInfiniteGet'
import { useIsInView } from '~/hooks/useIsInView'
import { toastSuccess } from '~/utils/toastSuccess'
import { toastError } from '~/utils/showErrorToast'
import { eventBus, EventBusType } from '~/utils/eventBus'
import { formatString } from '~/utils/formatString'
import { generateDisplayFullname } from '~/utils/generateDisplayFullname'
import { UsernameStore } from '~/classStore/UsernameStore'
import { PhoneNumberStore } from '~/classStore/PhoneNumberStore'
import type { RootState } from '~/redux'

import PencilIcon from '~/assets/icons/pencil.svg'
import CheckIcon from '~/assets/icons/check.svg'
import XCloseIcon from '~/assets/icons/x-close.svg'
import Table from '~/components/common/Table'
import Loading from '~/components/common/Loading'
import BaseModal from '~/components/common/BaseModal'
import Tooltip from '~/components/common/Tooltip'
import Input from '~/components/common/Input'

import TopActionBar, { type TopActionBarRef } from './TopActionBar'
import type { CreateUserForm } from './AddSingleUserForm'
import NoData from './NoData'
import EmptyWithSearch from './EmptyWithSearch'

interface Props {
  auditorsInfiniteData: ReturnType<
    typeof useInfiniteGet<
      UserCommon,
      {
        data: {
          total: number
          users: UserCommon[]
        }
      }
    >
  >
  search: string
  onSearchChange: (search: string) => void
}

export default function AuditorTab({
  auditorsInfiniteData,
  search,
  onSearchChange,
}: Readonly<Props>) {
  const topActionBarRef = useRef<TopActionBarRef>(null)
  const prevTotalRef = useRef(0)
  const loadMoreRef = useRef<HTMLDivElement | null>(null)
  const [selectedKeys, setSelectedKeys] = useState<(string | number)[]>([])
  const [editingRow, setEditingRow] = useState<null | string | number>(null)
  const [openTooltip, setOpenTooltip] = useState<null | 'fullname' | 'phoneNumber'>(null)
  const confirmEditModal = useModal()

  const { user } = useSelector((state: RootState) => state.auth)

  const form = useFormik({
    initialValues: {
      /**
       * `id` is only used for validation purpose
       */
      id: -1,
      fullname: '',
      phoneNumber: '',
      username: '',
    },
    validationSchema: UpdateUserSchema,
    onSubmit() {
      confirmEditModal.openModal()
    },
  })

  useGenerateUsername(form.values.fullname, form.values.phoneNumber, undefined, {
    disabled: !!form.errors.fullname,
    userId: form.values.id,
    onGenerate: (username) => {
      form.setFieldValue('username', username)
    },
  })

  const createUserMutation = useMutation<{
    id: number
  }>({
    method: 'post',
    url: endpoints.AUTH_REGISTER,
  })

  const deleteUsersMutation = useMutation({
    url: endpoints.USER_DELETE_USERS,
    method: 'delete',
  })

  const updateUserMutation = useMutation({
    method: 'put',
    url: formatString(endpoints.USER_UPDATE, { user_id: editingRow as string }),
  })

  const filteredAuditors = useMemo(() => {
    return auditorsInfiniteData.response.map((record) => {
      if (!search) {
        UsernameStore.set(record.username, record.id)
        PhoneNumberStore.set(record.phone_number, record.id)
      }
      return {
        key: record.id,
        ...record,
        displayFullName: generateDisplayFullname(record.fullname, search),
      }
    })
  }, [auditorsInfiniteData.response, search])

  useEffect(() => {
    const handleCancelDeleteUser = () => {
      setSelectedKeys([])
    }
    eventBus.on(EventBusType.CANCEL_DELETE_USER, handleCancelDeleteUser)

    return () => {
      eventBus.off(EventBusType.CANCEL_DELETE_USER, handleCancelDeleteUser)
    }
  }, [])

  useEffect(() => {
    const handleDeleteAllUserRequest = () => {
      if (!auditorsInfiniteData.response.length) return

      setSelectedKeys(auditorsInfiniteData.response.map((record) => record.id))

      eventBus.emit(EventBusType.SELECTED_AUDITOR, {
        count: auditorsInfiniteData.response.length,
        requestDelete: true,
      })
    }
    eventBus.on(EventBusType.DELETE_ALL_USER_REQUEST, handleDeleteAllUserRequest)

    return () => {
      eventBus.off(EventBusType.DELETE_ALL_USER_REQUEST, handleDeleteAllUserRequest)
    }
  }, [auditorsInfiniteData.response])

  useEffect(() => {
    const handleDeleteUser = () => {
      eventBus.emit(EventBusType.START_DELETE_USER)

      deleteUsersMutation.mutate(
        {
          body: {
            data: selectedKeys.map((id) => ({
              id,
              is_active: false,
            })),
          },
        },
        {
          onSuccess() {
            eventBus.emit(EventBusType.STOP_DELETE_USER, true)
            setSelectedKeys([])
            auditorsInfiniteData.reFetch()
            toastSuccess('Xóa người dùng thành công')
          },
          onError() {
            eventBus.emit(EventBusType.STOP_DELETE_USER, false)
            toastError('Có lỗi xảy ra')
          },
        },
      )
    }
    eventBus.on(EventBusType.CONFIRM_DELETE_USER, handleDeleteUser)
    return () => {
      eventBus.off(EventBusType.CONFIRM_DELETE_USER, handleDeleteUser)
    }
  }, [auditorsInfiniteData, deleteUsersMutation, selectedKeys])

  useIsInView(loadMoreRef, {
    deps: [auditorsInfiniteData.pending],
    listener(isInView) {
      if (isInView && !auditorsInfiniteData.pending) {
        auditorsInfiniteData.fetchNextPage()
      }
    },
  })

  const handleCreateUser = async (values: CreateUserForm) => {
    topActionBarRef.current?.startSubmit()

    createUserMutation.mutate(
      {
        body: {
          fullname: values.fullname,
          username: values.username,
          phone_number: values.phoneNumber,
          password: values.password,
          tenant_id: user?.tenant_id,
          roles: [Role.CHECKER],
        },
      },
      {
        onSuccess(response) {
          topActionBarRef.current?.afterSubmit(true)
          toastSuccess('Thêm người dùng thành công')
          auditorsInfiniteData.reFetch()
          UsernameStore.set(values.username, response.id)
        },
        onError() {
          topActionBarRef.current?.afterSubmit(false)
          toastError('Thêm người dùng thất bại')
        },
      },
    )
  }

  const handleSelectedKeysChange = (selectedKeys: (string | number)[]) => {
    setSelectedKeys(selectedKeys)
    eventBus.emit(EventBusType.SELECTED_AUDITOR, {
      count: selectedKeys.length,
    })
  }

  const handleEditRow = (row: NonNullable<typeof filteredAuditors>[number]) => {
    form.resetForm()
    setEditingRow(row.key)
    form.setValues(
      {
        ...form.values,
        id: row.id,
        fullname: row.fullname,
        phoneNumber: row.phone_number,
        username: row.username,
      },
      true,
    )
  }

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.name === 'phoneNumber') {
      form.setValues({
        ...form.values,
        phoneNumber: e.target.value,
      })
    } else if (e.target.name === 'fullname') {
      const fullname = e.target.value
      form.setValues({
        ...form.values,
        fullname: fullname,
      })
    }
  }

  const handleCancelEdit = () => {
    setEditingRow(null)
    form.resetForm()
  }

  const handleUpdate = () => {
    updateUserMutation.mutate(
      {
        body: {
          fullname: form.values.fullname,
          phone_number: form.values.phoneNumber,
          username: form.values.username,
        },
      },
      {
        onError: () => {
          toastError('Sửa thông tin thất bại, vui lòng thử lại')
        },
        onSuccess() {
          form.resetForm()
          confirmEditModal.closeModal()
          setEditingRow(null)
          toastSuccess('Sửa thông tin thành công')
          auditorsInfiniteData.reFetch()
        },
      },
    )
  }

  const renderUI = () => {
    if (
      !auditorsInfiniteData.total &&
      !search &&
      !auditorsInfiniteData.pending &&
      !prevTotalRef.current
    )
      return (
        <NoData
          submitting={createUserMutation.pending}
          onSubmitSingle={handleCreateUser}
          onCreateBatchUserSuccess={auditorsInfiniteData.reFetch}
        />
      )
    return (
      <>
        <Table
          rowSelection={{ selectedKeys: selectedKeys, onChange: handleSelectedKeysChange }}
          columns={[
            {
              key: 'full_name',
              label: 'Họ và tên',
              dataKey: 'fullname',
              align: 'left',
              width: '27%',
              cellClassName: 'has-[input]:py-0',
              render(record) {
                if (editingRow === record.key)
                  return (
                    <Tooltip content={form.errors.fullname} open={openTooltip === 'fullname'}>
                      <Input
                        name="fullname"
                        value={form.values.fullname}
                        classnames={{
                          wrapper: 'h-8',
                        }}
                        autoFocus
                        maxLength={100}
                        touched
                        errorStatusWithOutMessage={!!form.errors.fullname}
                        onFocus={() => setOpenTooltip('fullname')}
                        onBlur={() => setOpenTooltip(null)}
                        onChange={handleInputChange}
                      />
                    </Tooltip>
                  )
                return (
                  <div
                    dangerouslySetInnerHTML={{
                      __html: record.displayFullName ?? record.fullname,
                    }}
                  />
                )
              },
            },
            {
              key: 'phone_number',
              dataKey: 'phone_number',
              label: 'Số điện thoại',
              align: 'left',
              width: '27%',
              cellClassName: 'has-[input]:py-0',
              render(record) {
                if (record.key === editingRow)
                  return (
                    <Tooltip content={form.errors.phoneNumber} open={openTooltip === 'phoneNumber'}>
                      <Input
                        name="phoneNumber"
                        value={form.values.phoneNumber}
                        classnames={{
                          wrapper: 'h-8',
                        }}
                        maxLength={10}
                        touched
                        errorStatusWithOutMessage={!!form.errors.phoneNumber}
                        onFocus={() => setOpenTooltip('phoneNumber')}
                        onBlur={() => setOpenTooltip(null)}
                        onChange={handleInputChange}
                      />
                    </Tooltip>
                  )
                return record.phone_number
              },
            },
            {
              key: 'username',
              dataKey: 'username',
              label: 'Username',
              align: 'left',
              cellClassName: 'text-tertiary',
              render(record) {
                if (record.key === editingRow) return form.values.username
                return record.username
              },
            },
            {
              key: 'action',
              width: '10%',
              render: (record) => {
                if (record.key === editingRow)
                  return (
                    <div className="flex items-center justify-center gap-2.5 text-xl">
                      <button onClick={form.submitForm} disabled={!form.isValid}>
                        <CheckIcon className="text-success" />
                      </button>
                      <button>
                        <XCloseIcon className="text-error" onClick={handleCancelEdit} />
                      </button>
                    </div>
                  )
                return (
                  <button
                    className="block text-text-secondary text-xl"
                    onClick={() => handleEditRow(record)}
                  >
                    <PencilIcon />
                  </button>
                )
              },
            },
          ]}
          dataSource={filteredAuditors ?? []}
        />
        <div
          className={twMerge(
            'h-20',
            auditorsInfiniteData.response.length === auditorsInfiniteData.total && 'hidden',
          )}
        >
          <div
            className="h-full flex items-center justify-center pointer-events-none select-none"
            ref={loadMoreRef}
          >
            <ImSpinner8 className="animate-spin" />
          </div>
        </div>
        {auditorsInfiniteData.pending && !auditorsInfiniteData.response.length && (
          <Loading className="absolute inset-0" />
        )}
      </>
    )
  }

  return (
    <>
      <div className="h-full px-4 pb-2.5 flex flex-col gap-2">
        {(!!auditorsInfiniteData.total ||
          !!search ||
          auditorsInfiniteData.pending ||
          !!prevTotalRef.current) && (
          <TopActionBar
            ref={topActionBarRef}
            onCreateBatchUserSuccess={auditorsInfiniteData.reFetch}
            onSearchChange={onSearchChange}
            onSubmitCreateUser={handleCreateUser}
          />
        )}

        <div className="flex-1 relative overflow-y-auto flex flex-col">
          {renderUI()}
          {!!search && !auditorsInfiniteData.pending && !auditorsInfiniteData.total && (
            <EmptyWithSearch />
          )}
        </div>
      </div>
      <BaseModal
        open={confirmEditModal.open}
        title="SỬA THÔNG TIN"
        classNames={{
          body: 'w-[430px]',
        }}
        confirmButton={{
          label: 'Lưu',
          onClick: handleUpdate,
          loading: updateUserMutation.pending,
        }}
        onRequestClose={confirmEditModal.closeModal}
      >
        <p>
          Chỉnh sửa Số điện thoại có thể thay đổi Mật khẩu. Thay đổi sẽ áp dụng từ lần đăng nhập
          tiếp theo. <br />
          <br /> Bạn có chắc chắn muốn sửa?
        </p>
      </BaseModal>
    </>
  )
}
