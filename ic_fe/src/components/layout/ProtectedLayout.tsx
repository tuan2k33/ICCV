import { useSelector } from 'react-redux'
import { Navigate, Outlet, useNavigation } from 'react-router'
import type { RootState } from '~/redux'
import Header from '~/components/common/Header'
import Loading from '~/components/common/Loading'

export default function ProtectedLayout() {
  const navigation = useNavigation()
  const { user } = useSelector((state: RootState) => state.auth)

  if (!user) return <Navigate to="/auth/login" />

  return (
    <div className="h-dvh flex flex-col">
      <Header />
      <main className="grow overflow-y-auto relative">
        {/* {selectedRole ? <Outlet /> : <ChooseRole />} */}
        <Outlet />
        {!!navigation.location && <Loading className="absolute inset-0" />}
      </main>
    </div>
  )
}

// function ChooseRole() {
//   const dispatch = useDispatch()
//   const navigate = useNavigate()

//   const handleChooseRole = (role: string) => {
//     dispatch(actionSetSelectedRole(role))

//     switch (role) {
//       case 'Entry':
//         return navigate('/entry')
//       case 'Check':
//         return navigate('/check')
//       default:
//         return navigate('/')
//     }
//   }
//   return (
//     <div className="h-full self-stretch flex justify-center items-center gap-5">
//       <RoleCard role="Entry" onClick={() => handleChooseRole('Entry')} />
//       <RoleCard role="Check" onClick={() => handleChooseRole('Check')} />
//     </div>
//   )
// }

// function RoleCard({ role, onClick }: Readonly<{ role: string; onClick: () => void }>) {
//   return (
//     <button
//       className="w-40 aspect-square block rounded-2xl border-2 text-3xl cursor-pointer
//       hover:border-primary hover:scale-105 duration-200 hover:text-primary"
//       onClick={onClick}
//     >
//       {role}
//     </button>
//   )
// }
