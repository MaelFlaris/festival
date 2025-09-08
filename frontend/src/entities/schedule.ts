export type Slot = {
  id: number
  edition: number
  stage: number
  artist: number
  day: string
  start_time: string
  end_time: string
  status: 'tentative' | 'confirmed' | 'cancelled'
  is_headliner?: boolean
}

