import { Navigate, Outlet, useNavigation } from 'react-router'
import Loading from '../common/Loading'
import { useSelector } from 'react-redux'
import type { RootState } from '~/redux'

export default function HeadlessProtectedLayout() {
  const navigation = useNavigation()
  const { user } = useSelector((state: RootState) => state.auth)

  if (!user) return <Navigate to="/auth/login" />

  return (
    <>
      <Outlet />
      {!!navigation.location && <Loading className="absolute inset-0" />}
    </>
  )
}
