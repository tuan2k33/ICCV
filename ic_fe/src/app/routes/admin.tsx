import { useSelector } from 'react-redux'
import { Navigate } from 'react-router'
import type { RootState } from '~/redux'
import { Role } from '~/types/auth'
import Admin from '~/components/pages/Admin'

export default function AdminPage() {
  const { user } = useSelector((state: RootState) => state.auth)
  if (!user?.roles.includes(Role.ADMIN)) return <Navigate to="/" replace />
  return <Admin />
}
