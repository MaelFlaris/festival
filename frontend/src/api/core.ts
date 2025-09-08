import { useQuery } from '@tanstack/react-query'
import { api } from './client'
import type { Edition } from '../entities/core'

export async function fetchActiveEdition(): Promise<Edition | null> {
  const { data } = await api.get<Edition[]>('/core/editions', {
    params: { is_active: true },
  })
  return data[0] ?? null
}

export function useActiveEdition() {
  return useQuery({
    queryKey: ['core', 'editions', 'active'],
    queryFn: fetchActiveEdition,
  })
}

