import { useActiveEdition } from '../api/core'
import { useTopArtists } from '../api/lineup'

export default function HomePage() {
  const { data: edition, isLoading: editionLoading } = useActiveEdition()
  const { data: artists, isLoading: artistsLoading } = useTopArtists(6)

  return (
    <div>
      {editionLoading ? (
        <p>Loading edition...</p>
      ) : edition ? (
        <div>
          <h1>{edition.name}</h1>
          <p>
            {edition.start_date} - {edition.end_date}
          </p>
          {edition.tagline && <p>{edition.tagline}</p>}
        </div>
      ) : (
        <p>No active edition</p>
      )}

      <section>
        <h2>Top Artists</h2>
        {artistsLoading ? (
          <p>Loading artists...</p>
        ) : (
          <ul>
            {artists?.map((artist) => (
              <li key={artist.id}>{artist.name}</li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
