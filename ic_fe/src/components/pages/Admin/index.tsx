import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router'
import { twMerge } from 'tailwind-merge'
import { useDispatch, useSelector } from 'react-redux'

import type { AppDispatch, RootState } from '~/redux'
import { actionThunkGetActiveBatch } from '~/redux/slices/app'
import { useGet } from '~/hooks/useGet'
import { useInfiniteGet } from '~/hooks/useInfiniteGet'
import type { CountingPairListItem, UserCommon } from '~/types/common'
import { Role } from '~/types/auth'
import { endpoints } from '~/configs/endpoints'
import { generateUserSearchParams } from '~/utils/generateUserSearchParams'
import { UsernameStore } from '~/classStore/UsernameStore'
import { PhoneNumberStore } from '~/classStore/PhoneNumberStore'
import Badge from '~/components/common/Badge'
import CounterTab from './CounterTab'
import CountingPairTab from './CountingPairTab'
import AuditorTab from './AuditorTab'

export type Tab = 'COUNTER' | 'COUNTING_PAIR' | 'AUDITOR'

const tabs = [
  { key: 'COUNTER', label: 'Người đếm' },
  {
    key: 'COUNTING_PAIR',
    label: 'Cặp đếm',
  },
  {
    key: 'AUDITOR',
    label: 'Người kiểm toán',
  },
] as const

const LIMIT_PER_PAGE = 20

export default function Admin() {
  const { batch } = useSelector((state: RootState) => state.app)
  const { user } = useSelector((state: RootState) => state.auth)
  const dispatch = useDispatch<AppDispatch>()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = (searchParams.get('tab') || 'COUNTER') as Tab
  const [badgeValues, setBadgeValues] = useState({
    COUNTER: 0,
    AUDITOR: 0,
  })
  const [search, setSearch] = useState('')
  const totalRef = useRef({
    auditor: 0,
    linfox: 0,
    unilever: 0,
  })

  const linfoxInfiniteCounters = useInfiniteGet<
    UserCommon,
    {
      data: {
        total: number
        users: UserCommon[]
      }
    }
  >({
    url: endpoints.USER,
    config: {
      params: {
        roles: Role.ENTRY,
        company: 'Linfox', // TODO
        ...generateUserSearchParams(search),
      },
    },
    getPageProps: (page) => ({
      limit: LIMIT_PER_PAGE,
      skip: (page - 1) * LIMIT_PER_PAGE,
    }),
    onResponse(response) {
      return {
        total: response.data.total,
        items: response.data.users,
      }
    },
    options: {
      deps: [search],
      disabled: !!search && activeTab !== 'COUNTER',
      onSuccess(response) {
        if (!search) {
          totalRef.current.linfox = response.total
          handleTotalChange(response.total + totalRef.current.unilever, 'COUNTER')

          response.list.forEach((user) => {
            UsernameStore.set(user.username, user.id)
            PhoneNumberStore.set(user.phone_number, user.id)
          })
        }
      },
    },
  })

  const unileverInfiniteCounters = useInfiniteGet<
    UserCommon,
    {
      data: {
        total: number
        users: UserCommon[]
      }
    }
  >({
    url: endpoints.USER,
    config: {
      params: {
        roles: Role.ENTRY,
        company: 'Unilever', // TODO
        ...generateUserSearchParams(search),
      },
    },
    getPageProps: (page) => ({
      limit: LIMIT_PER_PAGE,
      skip: (page - 1) * LIMIT_PER_PAGE,
    }),
    onResponse(response) {
      return {
        total: response.data.total,
        items: response.data.users,
      }
    },
    options: {
      deps: [search],
      disabled: !!search && activeTab !== 'COUNTER',
      onSuccess(response) {
        if (!search) {
          totalRef.current.unilever = response.total
          handleTotalChange(response.total + totalRef.current.linfox, 'COUNTER')
          response.list.forEach((user) => {
            UsernameStore.set(user.username, user.id)
            PhoneNumberStore.set(user.phone_number, user.id)
          })
        }
      },
    },
  })

  const listCountingPairData = useGet<{ data: CountingPairListItem[] }>(
    {
      url: endpoints.COUNTING_GROUP,
      config: {
        params: {
          convert_racks: false,
          batch_id: batch,
        },
      },
    },
    {
      disabled: !batch,
    },
  )

  const auditorsInfiniteData = useInfiniteGet<
    UserCommon,
    {
      data: {
        total: number
        users: UserCommon[]
      }
    }
  >({
    url: endpoints.USER,
    config: {
      params: {
        roles: Role.CHECKER,
        ...generateUserSearchParams(search),
      },
    },
    getPageProps(page) {
      return {
        skip: (page - 1) * LIMIT_PER_PAGE,
        limit: LIMIT_PER_PAGE,
      }
    },
    onResponse(response) {
      return {
        total: response.data.total,
        items: response.data.users,
      }
    },
    options: {
      deps: [search],
      disabled: !!search && activeTab !== 'AUDITOR',
      onSuccess(response) {
        if (!search) {
          handleTotalChange(response.total, 'AUDITOR')
          totalRef.current.auditor = response.total
        }
      },
    },
  })

  useEffect(() => {
    switch (activeTab) {
      case 'COUNTER':
        if (!linfoxInfiniteCounters.pending) linfoxInfiniteCounters.reFetch()
        if (!unileverInfiniteCounters.pending) unileverInfiniteCounters.reFetch()
        break
      case 'COUNTING_PAIR':
        if (!listCountingPairData.pending) listCountingPairData.reFetch()
        break
      case 'AUDITOR':
        if (!auditorsInfiniteData.pending) auditorsInfiniteData.reFetch()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  const handleTotalChange = useCallback((total: number, tab: Tab) => {
    setBadgeValues((prev) => ({ ...prev, [tab]: total }))
  }, [])

  const getBadgeValue = (tab: Tab) => {
    if (tab === 'COUNTING_PAIR') return listCountingPairData.response?.data.length ?? 0
    if (tab === 'COUNTER') return badgeValues.COUNTER
    if (tab === 'AUDITOR') return badgeValues.AUDITOR
  }

  const renderTab = () => {
    if (activeTab === 'COUNTER')
      return (
        <CounterTab
          linfoxInfiniteCounters={linfoxInfiniteCounters}
          unileverInfiniteCounters={unileverInfiniteCounters}
          search={search}
          badgeValue={badgeValues.COUNTER}
          onUpdatedUser={listCountingPairData.reFetch}
          onSearchChange={setSearch}
          onAddedUser={listCountingPairData.reFetch}
        />
      )
    if (activeTab === 'COUNTING_PAIR')
      return <CountingPairTab listCountingPairData={listCountingPairData} />
    if (activeTab === 'AUDITOR')
      return (
        <AuditorTab
          auditorsInfiniteData={auditorsInfiniteData}
          search={search}
          onSearchChange={setSearch}
        />
      )
  }

  return (
    <>
      <title>Admin</title>
      <div className="flex flex-col h-full">
        <div className="pt-4 pb-3 flex items-center justify-center gap-3 text-quaternary text-sm font-semibold shrink-0">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              className={twMerge(
                'cursor-pointer w-[clamp(150px,18%,240px)] pb-3 border-b-2 border-transparent hover:text-error-secondary duration-200 flex justify-center gap-2',
                activeTab === tab.key && 'border-error-secondary text-error-secondary',
              )}
              onClick={() => {
                setSearchParams((prev) => ({ ...prev, tab: tab.key }))
                setSearch('')
                if (!batch) dispatch(actionThunkGetActiveBatch(user?.tenant_id!))
              }}
            >
              {tab.label}
              <Badge
                className={twMerge(
                  'bg-[#F9FAFB] border-border-secondary text-text-secondary',
                  tab.key === activeTab && 'bg-[#FFB5B0] border-[#FF6A60] text-error-secondary',
                )}
              >
                {getBadgeValue(tab.key)}
              </Badge>
            </button>
          ))}
        </div>
        <div className="grow overflow-hidden">{renderTab()}</div>
      </div>
    </>
  )
}
