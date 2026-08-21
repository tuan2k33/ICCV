import { useSelector } from 'react-redux'
import { Navigate } from 'react-router'
import type { RootState } from '~/redux'
import { Role } from '~/types/auth'
import Checker from '~/components/pages/Checker'

export default function CheckerPage() {
  const { user } = useSelector((state: RootState) => state.auth)
  if (!user?.roles.includes(Role.CHECKER)) return <Navigate to="/" replace />

  return (
    <>
      <title>Checker</title>
      <Checker />
    </>
  )
}
