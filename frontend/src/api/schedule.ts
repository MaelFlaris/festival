import { useQuery } from '@tanstack/react-query'
import { api } from './client'
import type { Slot } from '../entities/schedule'

export async function fetchSlots(): Promise<Slot[]> {
  const { data } = await api.get<Slot[]>('/schedule/slots')
  return data
}

export function useSlots() {
  return useQuery({ queryKey: ['schedule', 'slots'], queryFn: fetchSlots })
}

