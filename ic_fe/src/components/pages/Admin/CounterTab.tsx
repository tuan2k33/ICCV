import { memo, useEffect, useMemo, useRef } from 'react'
import { useSelector } from 'react-redux'
import { twMerge } from 'tailwind-merge'

import { Role } from '~/types/auth'
import type { UserCommon } from '~/types/common'
import { toastError } from '~/utils/showErrorToast'
import { toastSuccess } from '~/utils/toastSuccess'
import { eventBus, EventBusType } from '~/utils/eventBus'
import { useMutation } from '~/hooks/useMutation'
import { useInfiniteGet } from '~/hooks/useInfiniteGet'
import { endpoints } from '~/configs/endpoints'
import type { RootState } from '~/redux'
import { UsernameStore } from '~/classStore/UsernameStore'

import CounterTable, { type CounterTableRef } from './CounterTable'
import TopActionBar, { type TopActionBarRef } from './TopActionBar'
import type { CreateUserForm } from './AddSingleUserForm'
import EmptyWithSearch from './EmptyWithSearch'
import NoData from './NoData'

interface Props {
  linfoxInfiniteCounters: ReturnType<
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
  unileverInfiniteCounters: ReturnType<
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
  badgeValue: number
  search: string
  onUpdatedUser: () => void
  onSearchChange: (search: string) => void
  onAddedUser: () => void
}

function CounterTab({
  linfoxInfiniteCounters,
  unileverInfiniteCounters,
  search,
  badgeValue,
  onUpdatedUser,
  onSearchChange,
  onAddedUser,
}: Readonly<Props>) {
  const { user } = useSelector((state: RootState) => state.auth)
  const topActionBarRef = useRef<TopActionBarRef>(null)
  const linfoxTableRef = useRef<CounterTableRef>(null)
  const unileverTableRef = useRef<CounterTableRef>(null)

  const isEmptyWithSearch = useMemo(() => {
    return !!search && !linfoxInfiniteCounters.total && !unileverInfiniteCounters.total
  }, [linfoxInfiniteCounters.total, search, unileverInfiniteCounters.total])

  const createUserMutation = useMutation<{ id: number }>({
    method: 'post',
    url: endpoints.AUTH_REGISTER,
  })

  const deleteUsersMutation = useMutation({
    url: endpoints.USER_DELETE_USERS,
    method: 'delete',
  })

  useEffect(() => {
    const handleDeleteUser = () => {
      const selectedUser = [
        ...(linfoxTableRef.current?.getSelectedKeys() ?? []),
        ...(unileverTableRef.current?.getSelectedKeys() ?? []),
      ]

      eventBus.emit(EventBusType.START_DELETE_USER)

      deleteUsersMutation.mutate(
        {
          body: {
            data: selectedUser.map((id) => ({
              id,
              is_active: false,
            })),
          },
        },
        {
          onSuccess() {
            linfoxInfiniteCounters.reFetch()
            unileverInfiniteCounters.reFetch()
            eventBus.emit(EventBusType.STOP_DELETE_USER, true)
            eventBus.emit(EventBusType.CLEAR_SELECTED_USER, true)
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
  }, [linfoxInfiniteCounters, unileverInfiniteCounters, deleteUsersMutation])

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
          roles: [Role.ENTRY],
          company: values.company.replace(
            values.company.charAt(0),
            values.company.charAt(0).toUpperCase(),
          ),
        },
      },
      {
        onSuccess(response) {
          topActionBarRef.current?.afterSubmit(true)
          toastSuccess('Thêm người dùng thành công')
          if (values.company === 'linfox') linfoxInfiniteCounters.reFetch()
          else unileverInfiniteCounters.reFetch()
          UsernameStore.set(values.username, response.id)
          onAddedUser()
        },
        onError() {
          topActionBarRef.current?.afterSubmit(false)
          toastError('Thêm người dùng thất bại')
        },
      },
    )
  }

  if (
    !linfoxInfiniteCounters.pending &&
    !linfoxInfiniteCounters.total &&
    !unileverInfiniteCounters.pending &&
    !unileverInfiniteCounters.total &&
    !badgeValue
  ) {
    return (
      <NoData
        hasCompany
        submitting={createUserMutation.pending}
        onSubmitSingle={handleCreateUser}
        onCreateBatchUserSuccess={() => {
          linfoxInfiniteCounters.reFetch()
          unileverInfiniteCounters.reFetch()
        }}
      />
    )
  }

  return (
    <div className="h-full px-4 pb-2.5 flex flex-col">
      <TopActionBar
        hasCompany
        ref={topActionBarRef}
        onSubmitCreateUser={handleCreateUser}
        onSearchChange={onSearchChange}
        onCreateBatchUserSuccess={() => {
          linfoxInfiniteCounters.reFetch()
          unileverInfiniteCounters.reFetch()
          onAddedUser()
        }}
      />
      <div
        className={twMerge(
          'border border-border-secondary rounded-lg mt-2 grid grid-cols-2 overflow-hidden',
          !isEmptyWithSearch && 'grow',
        )}
      >
        <CounterTable
          company="LINFOX"
          search={search}
          total={linfoxInfiniteCounters.total}
          users={linfoxInfiniteCounters.response ?? []}
          loading={linfoxInfiniteCounters.pending}
          ref={linfoxTableRef}
          onUpdatedUser={() => {
            linfoxInfiniteCounters.reFetch()
            onUpdatedUser()
          }}
          fetchNextPage={linfoxInfiniteCounters.fetchNextPage}
        />
        <CounterTable
          company="UNILEVER"
          search={search}
          total={unileverInfiniteCounters.total}
          users={unileverInfiniteCounters.response}
          loading={unileverInfiniteCounters.pending}
          ref={unileverTableRef}
          onUpdatedUser={() => {
            unileverInfiniteCounters.reFetch()
            onUpdatedUser()
          }}
          fetchNextPage={unileverInfiniteCounters.fetchNextPage}
        />
      </div>
      {isEmptyWithSearch && <EmptyWithSearch />}
    </div>
  )
}

export default memo(CounterTab)
