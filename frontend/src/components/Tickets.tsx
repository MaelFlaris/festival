import { useEffect, useState } from 'react'

interface Ticket {
  id: number
  type: string
  price: number
  available: boolean
}

export default function Tickets() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    fetch('/api/tickets', {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      credentials: 'include',
    })
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok')
        return res.json()
      })
      .then((data) => setTickets(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const buyTicket = (id: number) => {
    setMessage(null)
    const token = localStorage.getItem('token')
    fetch(`/api/tickets/${id}/purchase`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      credentials: 'include',
    })
      .then((res) => {
        if (!res.ok) throw new Error('Purchase failed')
        return res.json()
      })
      .then(() => setMessage('Ticket purchased successfully'))
      .catch((err) => setMessage(err.message))
  }

  if (loading) return <p>Loading tickets...</p>
  if (error) return <p>Error: {error}</p>

  return (
    <div>
      <h2>Tickets</h2>
      {message && <p>{message}</p>}
      <ul>
        {tickets.map((ticket) => (
          <li key={ticket.id}>
            {ticket.type} - {ticket.price}€
            {ticket.available ? (
              <button onClick={() => buyTicket(ticket.id)}>Buy</button>
            ) : (
              <span> Sold out</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
