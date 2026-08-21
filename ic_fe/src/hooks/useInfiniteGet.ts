import { useEffect, useRef, useState, type DependencyList } from 'react'
import type { AxiosError, AxiosRequestConfig } from 'axios'
import { axiosInstance } from '~/utils/axiosInstance'

interface InfiniteGetProps<T, R> {
  url: string
  config?: AxiosRequestConfig
  options?: {
    disabled?: boolean
    deps?: DependencyList
    onSuccess?: (response: { total: number; list: T[] }) => void
    onError?: (error: AxiosError) => void
  }
  /**
   * @returns the Axios params object
   */
  getPageProps: (page: number) => Record<string, unknown>
  /**
   * @param response raw response from the server
   * @returns converted array of data items
   */
  onResponse: (response: R) => {
    total: number
    items: T[]
  }
}

/**
 * @template T type of each data item
 * @template R raw response from the server
 */
export const useInfiniteGet = <T = unknown, R = unknown>({
  url,
  config,
  options,
  getPageProps,
  onResponse,
}: InfiniteGetProps<T, R>) => {
  const isFirstTrackingDepsChangeRef = useRef(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [data, setData] = useState<{
    pending: boolean
    error: AxiosError | null
    total: number
  }>({
    pending: !options?.disabled,
    error: null,
    total: 0,
  })
  const [response, setResponse] = useState<T[]>([])

  const getData = async () => {
    if (options?.disabled) return
    try {
      setData((prev) => ({
        ...prev,
        pending: true,
      }))
      const responseRequest = await axiosInstance(url, {
        method: 'get',
        ...config,
        params: {
          ...config?.params,
          ...getPageProps(currentPage),
        },
      })

      const { total, items } = onResponse(responseRequest.data)
      // support reFetch will reset currentPage to 1, so we need to replace the response
      if (currentPage === 1) setResponse(items)
      else setResponse((prev) => [...prev, ...items])
      setData({
        total,
        error: null,
        pending: false,
      })
      options?.onSuccess?.({
        total,
        list: currentPage === 1 ? items : [...response, ...items],
      })
    } catch (error) {
      setData((prev) => ({
        ...prev,
        error: error as AxiosError,
        pending: false,
      }))

      options?.onError?.(error as AxiosError)
    }
  }

  useEffect(() => {
    if (isFirstTrackingDepsChangeRef.current) {
      // we only track deps change after the first run
      // because there is other useEffect run on the first render
      isFirstTrackingDepsChangeRef.current = false
      return
    }
    // reset to page 1 when url or deps change
    // in case currentPage is 1, we need to re-call for new data
    setResponse([])
    if (currentPage !== 1) setCurrentPage(1)
    else getData()

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, ...(options?.deps ?? [])])

  useEffect(() => {
    if (options?.disabled) return
    getData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage])

  const fetchNextPage = () => {
    if (data.pending || options?.disabled) return
    setCurrentPage((prev) => prev + 1)
  }

  const reFetch = () => {
    if (data.pending || options?.disabled) return
    setResponse([])
    if (currentPage === 1) getData()
    else setCurrentPage(1)
  }

  return {
    ...data,
    response,
    setResponse,
    fetchNextPage,
    reFetch,
  }
}
