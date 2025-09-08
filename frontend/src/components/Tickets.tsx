import { useState } from 'react'
import { useOnSaleTickets, reserveTicket } from '../api/tickets'

export default function Tickets() {
  const { data: tickets, isLoading, error } = useOnSaleTickets()
  const [message, setMessage] = useState<string | null>(null)

  const handleReserve = (id: number) => {
    setMessage(null)
    reserveTicket(id, 1, false)
      .then((res) =>
        setMessage(`Reserved ${res.reserved}, remaining ${res.available}`),
      )
      .catch(() => setMessage('Reservation failed'))
  }

  if (isLoading) return <p>Loading tickets...</p>
  if (error) return <p>Error loading tickets</p>

  return (
    <div>
      <h2>Tickets</h2>
      {message && <p>{message}</p>}
      <ul>
        {tickets?.map((ticket) => (
          <li key={ticket.id}>
            {ticket.name} - {ticket.price} {ticket.currency}
            {ticket.is_active ? (
              <button onClick={() => handleReserve(ticket.id)}>Reserve</button>
            ) : (
              <span> Sold out</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
