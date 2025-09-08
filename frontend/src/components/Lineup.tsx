import { useArtists } from '../api/lineup'

export default function Lineup() {
  const {
    data: artists,
    isLoading,
    error,
  } = useArtists()

  if (isLoading) return <p>Loading lineup...</p>
  if (error) return <p>Error loading lineup</p>

  return (
    <div>
      <h2>Lineup</h2>
      <ul>
        {artists?.map((artist) => (
          <li key={artist.id}>{artist.name}</li>
        ))}
      </ul>
    </div>
  )
}
