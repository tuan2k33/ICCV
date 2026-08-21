import { useSelector } from 'react-redux'
import { Navigate } from 'react-router'
import type { RootState } from '~/redux'
import { Role } from '~/types/auth'

export default function Home() {
  const { user } = useSelector((state: RootState) => state.auth)
  if (user?.roles.includes(Role.ENTRY)) return <Navigate to="/tasks" replace />
  if (user?.roles.includes(Role.CHECKER)) return <Navigate to="/dashboard" replace />
  if (user?.roles.includes(Role.ADMIN)) return <Navigate to="/admin" replace />
}
