import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Navbar.css'

function TopNavbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <nav className="top-navbar">
      <span className="navbar-brand">CeliacWriteOff</span>
      <ul className="top-navbar-links">
        <li><NavLink to="/add-items">Add Items</NavLink></li>
        <li><NavLink to="/review-items">Review Items</NavLink></li>
        <li><NavLink to="/tax-information">Tax Information</NavLink></li>
        {user?.is_admin && <li><NavLink to="/admin/login-activity">Admin</NavLink></li>}
      </ul>
      <div className="navbar-user">
        {user && <span className="navbar-email">{user.full_name || user.email}</span>}
        <button type="button" onClick={handleLogout}>Log out</button>
      </div>
    </nav>
  )
}

export default TopNavbar
