import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type { TicketType } from '../entities/tickets'

export async function fetchOnSaleTickets(): Promise<TicketType[]> {
  const { data } = await api.get<TicketType[]>('/tickets/types/on-sale')
  return data
}

export function useOnSaleTickets() {
  return useQuery({ queryKey: ['tickets', 'on-sale'], queryFn: fetchOnSaleTickets })
}

export async function reserveTicket(
  id: number,
  quantity: number,
  dry_run = true,
) {
  const { data } = await api.post(`/tickets/types/${id}/reserve`, {
    quantity,
    channel: 'web',
    dry_run,
  })
  return data as { reserved: number; available: number; dry_run?: boolean }
}

export function useReserveTicket(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { quantity: number; dry_run?: boolean }) =>
      reserveTicket(id, payload.quantity, payload.dry_run),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tickets', 'on-sale'] }),
  })
}

