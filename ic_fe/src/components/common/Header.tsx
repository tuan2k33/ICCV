import { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import toast from 'react-hot-toast'
import { LuLogOut } from 'react-icons/lu'
import type { RootState } from '~/redux'
import { actionLogout } from '~/redux/slices/auth'
import { useMutation } from '~/hooks/useMutation'
import { endpoints } from '~/configs/endpoints'
import { ErrorMessage } from '~/configs/errorCode'
import logo from '~/assets/logo.png'
import HomeIcon from '~/assets/icons/home.svg'
import Button from './Button'
import BreadCrumb from './BreadCrumb'
import Popover from './Popover'

const TIMEOUT = 1800000 // 30 minutes

export default function Header() {
  const timeOutRef = useRef<number>(null)
  const dispatch = useDispatch()
  const { user } = useSelector((state: RootState) => state.auth)

  const logoutMutation = useMutation({
    method: 'post',
    url: endpoints.AUTH_LOGOUT,
  })

  useEffect(() => {
    timeOutRef.current = window.setTimeout(() => {
      handleLogout()
    }, TIMEOUT)

    const abortController = new AbortController()

    window.addEventListener('mousemove', resetTimeout, {
      signal: abortController.signal,
      capture: true,
    })
    window.addEventListener('keydown', resetTimeout, {
      signal: abortController.signal,
      capture: true,
    })
    window.addEventListener('touchstart', resetTimeout, {
      signal: abortController.signal,
      capture: true,
    })

    window.addEventListener('scroll', resetTimeout, {
      signal: abortController.signal,
      capture: true,
    })

    return () => {
      if (timeOutRef.current) {
        clearTimeout(timeOutRef.current)
      }

      abortController.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const resetTimeout = () => {
    if (timeOutRef.current) {
      clearTimeout(timeOutRef.current)
    }

    timeOutRef.current = window.setTimeout(() => {
      handleLogout()
    }, TIMEOUT)
  }

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
    <header className="h-10 border-b-[0.5px] border-[#D9D9D9] flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-8">
        <img src={logo} alt="logo" className="w-[138px] h-6 object-cover" />
        <BreadCrumb
          items={[
            {
              label: <HomeIcon className="text-xl text-quaternary" />,
            },
          ]}
        />
      </div>

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
    </header>
  )
}
