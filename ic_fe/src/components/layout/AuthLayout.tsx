import { Navigate, Outlet } from 'react-router'
import { useSelector } from 'react-redux'
import type { RootState } from '~/redux'
import logo from '~/assets/logo.svg'

export default function AuthLayout() {
  const { user } = useSelector((state: RootState) => state.auth)

  if (user) {
    return <Navigate to="/" />
  }

  return (
    <div className="flex items-center justify-center min-h-dvh flex-col gap-6">
      <div className="p-10 pt-8 rounded-4xl shadow-2xl">
        <img src={logo} alt="logo" className="w-[200px]" />
        <Outlet />
      </div>
    </div>
  )
}
