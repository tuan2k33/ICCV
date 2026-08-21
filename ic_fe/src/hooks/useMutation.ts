import { useState } from 'react'
import type { AxiosError, AxiosRequestConfig } from 'axios'
import { axiosInstance } from '~/utils/axiosInstance'

type Method = 'post' | 'put' | 'patch' | 'delete'

interface Options<T> {
  onError?: (e: unknown) => void
  onSuccess?: (result: T) => void
}

interface MutatePayload {
  url?: string
  method?: Method
  body?: any
  config?: AxiosRequestConfig
}

interface MutationProps {
  url?: string
  method?: Method
  config?: AxiosRequestConfig
}

/**
 * This hook require `url` and `method` to be passed in props or when calling mutate function.
 * If `url` and `method` was pass in both props and mutate function, **props** will be used
 */
export const useMutation = <T = unknown>(props?: MutationProps) => {
  const [response, setResponse] = useState<T | null>(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<unknown>(null)

  return {
    /**
     * response after call mutate()
     */
    response,
    pending,
    error,
    /**
     * allow mutate the response directly
     */
    setResponse,
    mutate: async (
      { url, config, body, method }: MutatePayload,
      options?: Options<T>,
    ): Promise<{
      response: T | null
      error: AxiosError | null
    }> => {
      if (typeof url !== 'string' && typeof props?.url !== 'string') throw new Error('Invalid url')
      if (!method && !props?.method) throw new Error('Invalid method')

      try {
        setPending(true)
        setError(null)
        const response = await axiosInstance({
          url: url ?? props?.url,
          method: method ?? props?.method,
          ...props?.config,
          ...config,
          data: body,
        })

        setResponse(response.data)
        options?.onSuccess?.(response.data)
        return {
          response: response.data,
          error: null,
        }
      } catch (error) {
        setError(error)
        setResponse(null)
        options?.onError?.(error)
        return {
          response: null,
          error: error as AxiosError,
        }
      } finally {
        setPending(false)
      }
    },
  }
}
