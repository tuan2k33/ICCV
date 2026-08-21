import { useSelector } from 'react-redux'
import { Navigate } from 'react-router'
import type { RootState } from '~/redux'
import { Role } from '~/types/auth'
import Entry from '~/components/pages/Entry'

export default function EntryPage() {
  const { user } = useSelector((state: RootState) => state.auth)
  if (!user?.roles.includes(Role.ENTRY)) return <Navigate to="/" replace />

  return (
    <>
      <title>Entry</title>
      <Entry />
    </>
  )
}
