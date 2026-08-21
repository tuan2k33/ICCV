import axios from 'axios'
import { store } from '~/redux'
import { actionLogout } from '~/redux/slices/auth'

const axiosInstance = axios.create({
  timeout: 60000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

axiosInstance.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      store.dispatch(actionLogout())
    }

    throw error
  },
)

export { axiosInstance }
