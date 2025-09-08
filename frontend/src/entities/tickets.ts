export type TicketType = {
  id: number
  edition: number
  code: string
  name: string
  description?: string
  price: number
  currency: string
  quota?: number
  phase: 'early' | 'regular' | 'late'
  is_active: boolean
  day?: string
}

