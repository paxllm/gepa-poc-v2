import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import SetupPage from './pages/SetupPage';
import DashboardPage from './pages/DashboardPage';
import EvolutionPage from './pages/EvolutionPage';
import ResumesPage from './pages/ResumesPage';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <header className="app-header">
          <a href="/" className="app-header__logo">
            <div className="app-header__logo-icon">🧬</div>
            <span className="app-header__title">Resume GEPA</span>
          </a>
          <nav className="app-header__nav">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `app-header__nav-link ${isActive ? 'app-header__nav-link--active' : ''}`
              }
            >
              Setup
            </NavLink>
            <NavLink
              to="/resumes"
              className={({ isActive }) =>
                `app-header__nav-link ${isActive ? 'app-header__nav-link--active' : ''}`
              }
            >
              Resumes
            </NavLink>
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `app-header__nav-link ${isActive ? 'app-header__nav-link--active' : ''}`
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/evolution"
              className={({ isActive }) =>
                `app-header__nav-link ${isActive ? 'app-header__nav-link--active' : ''}`
              }
            >
              Evolution
            </NavLink>
          </nav>
        </header>

        <main className="page-container">
          <Routes>
            <Route path="/" element={<SetupPage />} />
            <Route path="/resumes" element={<ResumesPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/evolution" element={<EvolutionPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
