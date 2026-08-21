import type { RefObject } from 'react'
import toast from 'react-hot-toast'
import { LuLogOut } from 'react-icons/lu'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router'

import { endpoints } from '~/configs/endpoints'
import { ErrorMessage } from '~/configs/errorCode'
import { useMutation } from '~/hooks/useMutation'
import type { RootState } from '~/redux'
import { actionLogout } from '~/redux/slices/auth'
import logo from '~/assets/logo.png'
import HomeIcon from '~/assets/icons/home.svg'
import BreadCrumb from '~/components/common/BreadCrumb'
import Button from '~/components/common/Button'
import Counting, { type CountingRef } from '~/components/common/Counting'
import Popover from '~/components/common/Popover'
import Progress from '~/components/common/Progress'

interface Props {
  total?: number
  current?: number
  countingRef?: RefObject<CountingRef | null>
  isEmpty?: boolean
  taskName?: string
}

export default function Header({
  total,
  current,
  countingRef,
  isEmpty,
  taskName,
}: Readonly<Props>) {
  const dispatch = useDispatch()
  const { user } = useSelector((state: RootState) => state.auth)

  const logoutMutation = useMutation({
    method: 'post',
    url: endpoints.AUTH_LOGOUT,
  })

  const handleLogout = () => {
    logoutMutation.mutate(
      {},
      {
        onSuccess() {
          dispatch(actionLogout())
        },
        onError: (error: any) => {
          toast.error(error.response?.data?.detail?.message || ErrorMessage.UNKNOWN_ERROR)
        },
      },
    )
  }

  return (
    <div className="shrink-0 flex h-10 border-b-[0.5px] border-[#D9D9D9] items-center justify-between px-6">
      <div className="flex items-center gap-8">
        <div>
          <img src={logo} alt="logo" className="w-[138px] h-6 object-cover" />
        </div>
        <BreadCrumb
          items={[
            {
              label: (
                <Link to="/">
                  <HomeIcon className="text-xl" />
                </Link>
              ),
            },
            ...(isEmpty
              ? []
              : [
                  {
                    label: taskName,
                  },
                ]),
          ]}
        />
      </div>

      {!!total && (
        <Progress
          current={current ?? 0}
          total={total}
          classNames={{
            label: 'text-sm',
          }}
        />
      )}

      <div className="flex gap-8 items-center">
        {!isEmpty && <Counting errorValue={31} warnValue={18} ref={countingRef} />}
        <Popover
          content={
            <div className="w-40">
              <Button className="" outline loading={logoutMutation.pending} onClick={handleLogout}>
                Logout <LuLogOut className="ml-2" />
              </Button>
            </div>
          }
        >
          <Button circle square className="h-6 text-xs font-semibold bg-[#078DEE] uppercase">
            {(user?.fullname || user?.username)?.slice(0, 2)}
          </Button>
        </Popover>
      </div>
    </div>
  )
}
