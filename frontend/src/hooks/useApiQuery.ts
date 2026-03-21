import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import type { AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'

type ApiCall<T> = () => Promise<AxiosResponse<ApiResponse<T>>>

/** Thin wrapper around useQuery that unwraps the ApiResponse envelope */
export function useApiQuery<T>(key: unknown[], fn: ApiCall<T>, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: key,
    queryFn: async () => {
      const res = await fn()
      return res.data.data
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
      return res.data.data
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
