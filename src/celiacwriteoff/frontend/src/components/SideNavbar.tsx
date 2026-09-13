import './Navbar.css'

function SideNavbar() {
  return (
    <nav className="side-navbar">
      <ul className="side-navbar-links">
        <li><a href="#">Home</a></li>
        <li><a href="#">Search</a></li>
        <li><a href="#">Saved</a></li>
        <li><a href="#">Profile</a></li>
      </ul>
    </nav>
  )
}

export default SideNavbar
