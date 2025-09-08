import axios, { AxiosError, AxiosRequestConfig } from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/api/v1',
  withCredentials: true,
})

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const config = error.config as AxiosRequestConfig & {
      __retryCount?: number
    }
    const status = error.response?.status

    if (status && status >= 500 && status < 600) {
      config.__retryCount = config.__retryCount || 0
      if (config.__retryCount < 3) {
        config.__retryCount += 1
        const delay = 100 * Math.pow(2, config.__retryCount)
        await new Promise((r) => setTimeout(r, delay))
        return api(config)
      }
    }

    if (status === 401 || status === 403) {
      console.warn('Unauthorized access')
    }

    if (status === 429) {
      console.warn('Rate limited')
    }

    return Promise.reject(error)
  },
)

export { api }

