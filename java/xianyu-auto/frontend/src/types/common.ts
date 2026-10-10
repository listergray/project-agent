export interface PageResult<T> {
  list: T[]
  total: number
}

export interface CommonResult<T> {
  code: number
  message: string
  data: T
  timestamp: number
}
