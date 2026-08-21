import { useSelector } from 'react-redux'
import { Navigate } from 'react-router'
import type { RootState } from '~/redux'
import { Role } from '~/types/auth'
import Dashboard from '~/components/pages/Dashboard'

export default function DashboardPage() {
  const { user } = useSelector((state: RootState) => state.auth)
  if (!user?.roles.includes(Role.CHECKER)) return <Navigate to="/" replace />

  return <Dashboard />
}
