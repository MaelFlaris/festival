import { useEffect, useState } from 'react'

interface Artist {
  id: number
  name: string
  stage?: string
  time?: string
}

export default function Lineup() {
  const [artists, setArtists] = useState<Artist[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    fetch('/api/lineup', {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      credentials: 'include',
    })
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok')
        return res.json()
      })
      .then((data) => setArtists(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading lineup...</p>
  if (error) return <p>Error: {error}</p>

  return (
    <div>
      <h2>Lineup</h2>
      <ul>
        {artists.map((artist) => (
          <li key={artist.id}>
            {artist.name}
            {artist.stage ? ` - ${artist.stage}` : ''}
            {artist.time ? ` (${artist.time})` : ''}
          </li>
        ))}
      </ul>
    </div>
  )
}
