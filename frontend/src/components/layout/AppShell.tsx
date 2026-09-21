import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  Database,
  HeartPulse,
  History,
  LayoutDashboard,
  Menu,
  Microscope,
  Radio,
  Settings,
  Sparkles,
  User,
  X,
} from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useLive } from "../../context/LiveContext";
import { SignalBackground } from "../live/SignalBackground";

const sections: { title?: string; items: { to: string; label: string; icon: React.ReactNode }[] }[] = [
  {
    items: [
      { to: "/dashboard", label: "Dashboard", icon: <LayoutDashboard size={17} /> },
      { to: "/monitoring", label: "Live Monitoring", icon: <Activity size={17} /> },
      { to: "/demo", label: "Demo & Simulation", icon: <Radio size={17} /> },
      { to: "/predictions", label: "Predictions", icon: <BrainCircuit size={17} /> },
      { to: "/xai", label: "Explainable AI", icon: <Sparkles size={17} /> },
      { to: "/history", label: "Migraine History", icon: <History size={17} /> },
      { to: "/alerts", label: "Alerts", icon: <AlertTriangle size={17} /> },
    ],
  },
  {
    title: "Insights",
    items: [
      { to: "/reports", label: "Reports", icon: <BarChart3 size={17} /> },
      { to: "/datasets", label: "Datasets", icon: <Database size={17} /> },
      { to: "/device", label: "Device", icon: <Microscope size={17} /> },
    ],
  },
  {
    title: "Account",
    items: [
      { to: "/profile", label: "Profile", icon: <User size={17} /> },
      { to: "/settings", label: "Settings", icon: <Settings size={17} /> },
    ],
  },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const { connected, demoRunning, prediction } = useLive();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const sidebar = (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-mark">
          <HeartPulse size={18} />
        </span>
        <span>
          MIGRAINE <em>DETECTOR</em>
        </span>
        {demoRunning ? (
          <span className="live-indicator demo" title="Demo / simulation mode active">
            ● DEMO MODE
          </span>
        ) : (
          <span className={`live-indicator ${connected ? "live" : "offline"}`}>
            ● {connected ? "RASPBERRY PI CONNECTED" : "OFFLINE"}
          </span>
        )}
      </div>

      <nav className="sidebar-nav">
        {sections.map((section) => (
          <div className="sidebar-section" key={section.title ?? "main"}>
            {section.title && <div className="sidebar-section-label">{section.title}</div>}
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => (isActive ? "sidebar-link active" : "sidebar-link")}
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <span className="avatar">{user?.name?.charAt(0) ?? "U"}</span>
          <div>
            <strong>{user?.name || user?.email}</strong>
            <small>{user?.email}</small>
          </div>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
          Sign out
        </button>
      </div>
    </aside>
  );

  return (
    <div className="app-shell">
      <SignalBackground riskLevel={prediction?.risk_level ?? null} />

      <div className="app-mobile-bar">
        <button className="icon-btn" onClick={() => setOpen(true)} aria-label="Open menu">
          <Menu size={20} />
        </button>
        <Link to="/dashboard" className="navbar-brand">
          <span className="brand-mark">
            <HeartPulse size={18} />
          </span>
          <span>MIGRAINE DETECTOR</span>
        </Link>
      </div>

      {open && (
        <div className="mobile-overlay" onClick={() => setOpen(false)}>
          <div className="mobile-drawer" onClick={(e) => e.stopPropagation()}>
            <button className="icon-btn drawer-close" onClick={() => setOpen(false)} aria-label="Close menu">
              <X size={20} />
            </button>
            {sidebar}
          </div>
        </div>
      )}

      <div className="app-sidebar-desktop">{sidebar}</div>

      <main className="app-main">
        <div className="app-main-inner">
          <Outlet />
        </div>
      </main>

      <nav className="app-tabbar" aria-label="Primary">
        {[
          { to: "/dashboard", label: "Home", icon: <LayoutDashboard size={19} /> },
          { to: "/monitoring", label: "Live", icon: <Activity size={19} /> },
          { to: "/demo", label: "Demo", icon: <Radio size={19} /> },
          { to: "/alerts", label: "Alerts", icon: <AlertTriangle size={19} /> },
          { to: "/profile", label: "Profile", icon: <User size={19} /> },
        ].map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) => (isActive ? "app-tab active" : "app-tab")}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}