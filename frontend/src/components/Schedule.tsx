import { useSlots } from '../api/schedule'

export default function Schedule() {
  const {
    data: slots,
    isLoading,
    error,
  } = useSlots()

  if (isLoading) return <p>Loading schedule...</p>
  if (error) return <p>Error loading schedule</p>

  return (
    <div>
      <h2>Schedule</h2>
      <ul>
        {slots?.map((slot) => (
          <li key={slot.id}>
            {slot.day} {slot.start_time} - {slot.end_time}
          </li>
        ))}
      </ul>
    </div>
  )
}
