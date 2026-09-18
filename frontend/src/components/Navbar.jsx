import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <nav className="navbar">
      <Link to="/" className="brand">
        🦆 DuckyRoom
      </Link>
      {user && (
        <div className="nav-user">
          <span>
            {user.first_name || user.username} · {user.role === "TEACHER" ? "Profesor" : "Estudiante"}
          </span>
          <button onClick={handleLogout} className="btn-link">
            Salir
          </button>
        </div>
      )}
    </nav>
  );
}
