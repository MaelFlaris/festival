import { useQuery } from '@tanstack/react-query'
import { api } from './client'
import type { Artist } from '../entities/lineup'

export async function fetchArtists(): Promise<Artist[]> {
  const { data } = await api.get<Artist[]>('/lineup/artists')
  return data
}

export function useArtists() {
  return useQuery({ queryKey: ['lineup', 'artists'], queryFn: fetchArtists })
}

export async function fetchTopArtists(limit = 6): Promise<Artist[]> {
  const { data } = await api.get<Artist[]>('/lineup/artists/top', {
    params: { limit },
  })
  return data
}

export function useTopArtists(limit = 6) {
  return useQuery({
    queryKey: ['lineup', 'artists', 'top', limit],
    queryFn: () => fetchTopArtists(limit),
  })
}

