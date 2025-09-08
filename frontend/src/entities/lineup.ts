export type Artist = {
  id: number
  name: string
  country?: string
  bio?: string
  popularity?: number
  genres: number[]
  links?: Record<string, string>
}

