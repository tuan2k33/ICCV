import {
  useEffect,
  useImperativeHandle,
  useMemo,
  useState,
  type ChangeEvent,
  type RefObject,
} from 'react'
import { twMerge } from 'tailwind-merge'
import { useSelector } from 'react-redux'

import { useModal } from '~/hooks/useModal'
import { eventBus, EventBusType } from '~/utils/eventBus'
import { debounce } from '~/utils/debounce'
import type { RootState } from '~/redux'

import FolderPlusIcon from '~/assets/icons/folder-plus.svg'
import PlusIcon from '~/assets/icons/plus.svg'
import SearchIcon from '~/assets/icons/search.svg'
import TrashIcon from '~/assets/icons/trash.svg'
import Button from '~/components/common/Button'
import Input from '~/components/common/Input'
import BaseModal from '~/components/common/BaseModal'
import AddSingleUser, { type CreateUserForm } from './AddSingleUserForm'
import AddBatch from './AddBatch'

export interface TopActionBarRef {
  startSubmit: () => void
  afterSubmit: (isSuccess: boolean) => void
}

interface Props {
  className?: string
  hasCompany?: boolean
  ref?: RefObject<TopActionBarRef | null>
  onSubmitCreateUser: (values: CreateUserForm) => void
  onSearchChange: (search: string) => void
  onCreateBatchUserSuccess: () => void
}

type MODAL_TYPE = 'add_single' | 'add_multi' | 'add_batch'

export default function TopActionBar({
  className,
  hasCompany,
  ref,
  onSubmitCreateUser,
  onSearchChange,
  onCreateBatchUserSuccess,
}: Readonly<Props>) {
  const [openModal, setOpenModal] = useState<null | MODAL_TYPE>(null)
  const [loading, setLoading] = useState(false)
  const [selectedUserCount, setSelectedUserCount] = useState({
    linfox: 0,
    unilever: 0,
    auditor: 0,
  })
  const deleteUserModal = useModal()
  const { batch } = useSelector((state: RootState) => state.app)

  useEffect(() => {
    type Payload = {
      company: 'linfox' | 'unilever'
      count: number
      requestDelete?: boolean
    }
    const handleSelectedUserChange = (payload?: Payload) => {
      if (payload) {
        setSelectedUserCount((prev) => ({ ...prev, [payload.company]: payload.count }))
        if (payload.requestDelete) deleteUserModal.openModal()
      }
    }

    const handleSelectedAuditorChange = (payload?: { count: number; requestDelete?: boolean }) => {
      if (payload) {
        setSelectedUserCount({
          auditor: payload.count,
          linfox: 0,
          unilever: 0,
        })
        if (payload.requestDelete) deleteUserModal.openModal()
      }
    }

    const handleStartDeleteUser = () => {
      setLoading(true)
    }

    const handleStopDeleteUser = (isSuccess?: boolean) => {
      setLoading(false)
      if (isSuccess) {
        deleteUserModal.closeModal()
        setSelectedUserCount({
          auditor: 0,
          linfox: 0,
          unilever: 0,
        })
      }
    }

    eventBus.on<Payload>(EventBusType.SELECTED_COUNTER, handleSelectedUserChange)
    eventBus.on<{ count: number }>(EventBusType.SELECTED_AUDITOR, handleSelectedAuditorChange)
    eventBus.on(EventBusType.START_DELETE_USER, handleStartDeleteUser)
    eventBus.on<boolean>(EventBusType.STOP_DELETE_USER, handleStopDeleteUser)

    return () => {
      eventBus.off(EventBusType.SELECTED_COUNTER, handleSelectedUserChange)
      eventBus.off(EventBusType.SELECTED_AUDITOR, handleSelectedAuditorChange)
      eventBus.off(EventBusType.START_DELETE_USER, handleStartDeleteUser)
      eventBus.off(EventBusType.STOP_DELETE_USER, handleStopDeleteUser)
    }
  }, [deleteUserModal])

  useImperativeHandle(
    ref,
    () => ({
      startSubmit() {
        setLoading(true)
      },
      afterSubmit(isSuccess) {
        setLoading(false)
        if (isSuccess) setOpenModal(null)
      },
    }),
    [],
  )

  const handleInputChange = useMemo(
    () =>
      debounce((e: ChangeEvent<HTMLInputElement>) => {
        onSearchChange(e.target.value)
      }),
    [onSearchChange],
  )

  const selectedUser =
    selectedUserCount.linfox + selectedUserCount.unilever + selectedUserCount.auditor

  const handleDeleteClick = () => {
    if (selectedUser) deleteUserModal.openModal()
    else eventBus.emit(EventBusType.DELETE_ALL_USER_REQUEST)
  }

  const handleCancelDelete = () => {
    if (loading) return
    deleteUserModal.closeModal()
    eventBus.emit(EventBusType.CANCEL_DELETE_USER)
    setSelectedUserCount({
      linfox: 0,
      unilever: 0,
      auditor: 0,
    })
  }

  return (
    <>
      <div className={twMerge('flex items-center py-2 gap-3 shrink-0', className)}>
        <Input
          placeholder="Tìm tên, số điện thoại"
          prefix={<SearchIcon className="text-xl mr-1" />}
          classnames={{
            wrapper: 'w-[236px]',
          }}
          onChange={handleInputChange}
        />

        <Button
          className={twMerge(
            'w-fit text-sm gap-1 px-3.5 ml-auto',
            !!selectedUser && 'text-error-secondary border-[#FF4438]',
          )}
          outline
          disabled={!!batch}
          onClick={handleDeleteClick}
        >
          <TrashIcon className="text-xl" />
          Xóa {!!selectedUser && `(${selectedUser})`}
        </Button>
        <Button
          className="w-fit text-sm gap-1 px-3.5"
          outline
          onClick={() => setOpenModal('add_single')}
        >
          <PlusIcon className="text-xl" />
          Thêm lẻ
        </Button>
        <Button
          className="w-fit text-sm gap-1 px-3.5 bg-blue-secondary"
          onClick={() => setOpenModal('add_batch')}
        >
          <FolderPlusIcon className="text-xl" />
          Thêm hàng loạt
        </Button>
      </div>
      <AddSingleUser
        hasCompany={hasCompany}
        open={openModal === 'add_single'}
        submitting={loading}
        onRequestClose={() => !loading && setOpenModal(null)}
        onSubmit={onSubmitCreateUser}
      />
      <AddBatch
        open={openModal === 'add_batch'}
        hasCompany={hasCompany}
        onRequestClose={() => !loading && setOpenModal(null)}
        onCreateSuccess={onCreateBatchUserSuccess}
      />
      <BaseModal
        open={deleteUserModal.open}
        title="XÓA NGƯỜI DÙNG"
        classNames={{
          body: 'w-[430px]',
        }}
        onRequestClose={!loading ? deleteUserModal.closeModal : undefined}
        confirmButton={{
          label: 'Xóa',
          className: 'bg-[#FF5630]',
          icon: <TrashIcon className="text-base" />,
          loading,
          onClick() {
            eventBus.emit(EventBusType.CONFIRM_DELETE_USER)
          },
        }}
        cancelButton={{
          onClick: handleCancelDelete,
        }}
      >
        <p>
          <span className="text-error font-semibold">{selectedUser} người dùng</span> sẽ bị xóa vĩnh
          viễn. <br />
          Bạn có chắc chắn muốn xóa?
        </p>
      </BaseModal>
    </>
  )
}
