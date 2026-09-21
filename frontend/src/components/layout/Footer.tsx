import { Activity } from "lucide-react";
import { Link } from "react-router-dom";

const columns: { title: string; links: { to: string; label: string }[] }[] = [
  {
    title: "Platform",
    links: [
      { to: "/", label: "Home" },
      { to: "/how-it-works", label: "How It Works" },
      { to: "/research", label: "Research" },
      { to: "/contact", label: "Contact" },
    ],
  },
  {
    title: "Application",
    links: [
      { to: "/login", label: "Sign in" },
      { to: "/register", label: "Create account" },
      { to: "/dashboard", label: "Dashboard" },
      { to: "/demo", label: "Demo Lab" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div className="footer-brand">
          <span className="brand-mark">
            <Activity size={18} />
          </span>
          <span>
            MIGRAINE <em>DETECTOR</em>
          </span>
          <p>
            A personalized IoT early-warning research prototype combining
            physiological sensing, machine learning and explainable AI.
          </p>
          <p className="footer-note">
            Research prototype. Not a medically validated diagnostic device.
          </p>
        </div>
        {columns.map((col) => (
          <div className="footer-col" key={col.title}>
            <h4>{col.title}</h4>
            {col.links.map((link) => (
              <Link key={link.to} to={link.to}>
                {link.label}
              </Link>
            ))}
          </div>
        ))}
      </div>
      <div className="container footer-bottom">
        <span>© {new Date().getFullYear()} Migraine Detector</span>
        <span>Built with FastAPI · React · Raspberry Pi</span>
      </div>
    </footer>
  );
}