import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import HomePage from './pages/HomePage'
import LineupPage from './pages/LineupPage'
import SchedulePage from './pages/SchedulePage'
import TicketsPage from './pages/TicketsPage'
import './App.css'

export default function App() {
  return (
    <Router>
      <nav>
        <ul className="flex gap-4">
          <li>
            <Link to="/">Home</Link>
          </li>
          <li>
            <Link to="/lineup">Lineup</Link>
          </li>
          <li>
            <Link to="/schedule">Schedule</Link>
          </li>
          <li>
            <Link to="/tickets">Tickets</Link>
          </li>
        </ul>
      </nav>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/lineup" element={<LineupPage />} />
        <Route path="/schedule" element={<SchedulePage />} />
        <Route path="/tickets" element={<TicketsPage />} />
      </Routes>
    </Router>
  )
}
