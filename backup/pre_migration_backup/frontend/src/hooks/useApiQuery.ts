import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import type { AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'
import type { QueryKey, UseQueryOptions } from '@tanstack/react-query'

type ApiCall<T> = () => Promise<AxiosResponse<ApiResponse<T>>>

function unwrapApiData<T>(res: AxiosResponse<ApiResponse<T>>) {
  const payload = res.data as unknown as {
    success?: boolean
    message?: string
    data?: T
  } | T

  if (
    payload &&
    typeof payload === 'object' &&
    'data' in payload &&
    (('success' in payload) || ('message' in payload))
  ) {
    return (payload as { data: T }).data
  }

  return payload as T
}

/** Thin wrapper around useQuery that unwraps the ApiResponse envelope */
export function useApiQuery<T>(
  key: QueryKey,
  fn: ApiCall<T>,
  options?: Omit<UseQueryOptions<T, Error, T, QueryKey>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: key,
    queryFn: async () => {
      const res = await fn()
      return unwrapApiData(res)
    },
    ...options,
  })
}

/** Thin wrapper around useMutation with success/error toasts */
export function useApiMutation<TData, TVariables>(
  fn: (vars: TVariables) => Promise<AxiosResponse<ApiResponse<TData>>>,
  options?: {
    successMessage?: string
    errorMessage?: string
    invalidateKeys?: unknown[][]
    onSuccess?: (data: TData) => void
  }
) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (vars: TVariables) => {
      const res = await fn(vars)
      return unwrapApiData(res)
    },
    onSuccess: (data) => {
      if (options?.successMessage) {
        message.success(options.successMessage)
      }
      options?.invalidateKeys?.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: key })
      })
      options?.onSuccess?.(data)
    },
    onError: (err: unknown) => {
      const msg =
        options?.errorMessage ||
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
        'Something went wrong'
      message.error(msg)
    },
  })
}
