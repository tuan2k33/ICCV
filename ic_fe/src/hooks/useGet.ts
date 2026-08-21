import { useEffect, useState, type DependencyList } from 'react'
import type { AxiosError, AxiosRequestConfig } from 'axios'
import { axiosInstance } from '~/utils/axiosInstance'

export const useGet = <T = unknown>(
  { url, config }: { url: string; config?: AxiosRequestConfig },
  options?: {
    disabled?: boolean
    deps?: DependencyList
    onSuccess?: (response: T) => void
    onError?: (error: AxiosError) => void
  },
) => {
  const [data, setData] = useState<{
    pending: boolean
    error: AxiosError | null
  }>({
    pending: !options?.disabled,
    error: null,
  })
  const [response, setResponse] = useState<T | null>(null)

  const getData = async () => {
    try {
      setData((prev) => ({
        ...prev,
        pending: true,
      }))
      const response = await axiosInstance(url, {
        method: 'get',
        ...config,
      })

      setData({
        error: null,
        pending: false,
      })
      setResponse(response.data)
      options?.onSuccess?.(response.data)
    } catch (error) {
      setData({
        error: error as AxiosError,
        pending: false,
      })
      setResponse(null)
      options?.onError?.(error as AxiosError)
    }
  }

  useEffect(() => {
    if (!options?.disabled) getData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, options?.disabled, ...(options?.deps || [])])

  const reFetch = () => {
    if (data.pending || options?.disabled) return
    getData()
  }

  return { ...data, response, reFetch, setResponse }
}
