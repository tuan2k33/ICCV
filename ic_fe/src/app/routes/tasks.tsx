import { useSelector } from 'react-redux'
import { Navigate } from 'react-router'
import type { RootState } from '~/redux'
import { Role } from '~/types/auth'
import MyTasks from '~/components/pages/MyTasks'

export default function TaskPage() {
  const { user } = useSelector((state: RootState) => state.auth)
  if (!user?.roles.includes(Role.ENTRY)) return <Navigate to="/" replace />

  return <MyTasks />
}
