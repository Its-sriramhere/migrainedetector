import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="notfound">
      <span className="notfound-code">404</span>
      <h1>Page not found</h1>
      <p>The page you are looking for does not exist.</p>
      <Link to="/" className="btn btn-primary btn-shine">
        Back to Home
      </Link>
    </div>
  );
}