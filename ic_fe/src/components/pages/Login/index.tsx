import { useFormik } from 'formik'
import { useDispatch, useSelector } from 'react-redux'
import toast from 'react-hot-toast'

import { LoginSchema } from '~/configs/schemas'
import { ErrorMessage } from '~/configs/errorCode'
import { actionThunkGetMe } from '~/redux/slices/auth'
import type { AppDispatch, RootState } from '~/redux'
import { useMutation } from '~/hooks/useMutation'
import { endpoints } from '~/configs/endpoints'
import Button from '~/components/common/Button'
import Input from '~/components/common/Input'

export default function Login() {
  const dispatch = useDispatch<AppDispatch>()
  const { loading } = useSelector((state: RootState) => state.auth)

  const loginMutation = useMutation({
    method: 'post',
    url: endpoints.AUTH_LOGIN,
  })

  const formik = useFormik({
    initialValues: {
      username: '',
      password: '',
    },
    validationSchema: LoginSchema,
    onSubmit: (values) => {
      loginMutation.mutate(
        {
          body: values,
        },
        {
          onSuccess: () => {
            dispatch(actionThunkGetMe())
          },
          onError: (error: any) => {
            toast.error(error.response?.data?.detail?.message || ErrorMessage.UNKNOWN_ERROR)
          },
        },
      )
    },
  })
  return (
    <div className="min-w-[320px]">
      <h1 className="mt-6 text-3xl text-center font-bold text-primary">Login</h1>
      <form className="space-y-2 mt-5" onSubmit={formik.handleSubmit}>
        <Input
          name="username"
          label="Username"
          placeholder="Enter your username"
          stackLabel={false}
          value={formik.values.username}
          touched={formik.touched.username}
          error={formik.errors.username}
          onChange={formik.handleChange}
        />
        <Input
          name="password"
          label="Password"
          placeholder="Enter your password"
          type="password"
          stackLabel={false}
          value={formik.values.password}
          touched={formik.touched.password}
          error={formik.errors.password}
          onChange={formik.handleChange}
        />
        <Button type="submit" className="h-11 mt-4" loading={loginMutation.pending || loading}>
          Login
        </Button>
      </form>
    </div>
  )
}
