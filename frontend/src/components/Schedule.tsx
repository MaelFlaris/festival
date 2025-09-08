import { useEffect, useState } from 'react'

interface EventItem {
  id: number
  title: string
  start: string
  end: string
  stage?: string
}

export default function Schedule() {
  const [events, setEvents] = useState<EventItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    fetch('/api/schedule', {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      credentials: 'include',
    })
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok')
        return res.json()
      })
      .then((data) => setEvents(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading schedule...</p>
  if (error) return <p>Error: {error}</p>

  return (
    <div>
      <h2>Schedule</h2>
      <ul>
        {events.map((event) => (
          <li key={event.id}>
            {event.title} - {event.start} to {event.end}
            {event.stage ? ` @ ${event.stage}` : ''}
          </li>
        ))}
      </ul>
    </div>
  )
}
