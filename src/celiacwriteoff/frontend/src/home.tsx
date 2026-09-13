import { Outlet } from 'react-router-dom'
import './App.css'
import TopNavbar from './components/TopNavbar'
import SideNavbar from './components/SideNavbar'

function Home() {
  return (
    <>
      <TopNavbar />
      <SideNavbar />
      <main className="layout-content">
        <Outlet />
      </main>
    </>
  )
}

export default Home
