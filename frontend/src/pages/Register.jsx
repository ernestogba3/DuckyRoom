import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const initialForm = {
  username: "",
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  role: "STUDENT",
};

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function update(field, value) {
    setForm({ ...form, [field]: value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(form);
      navigate("/");
    } catch (err) {
      const data = err.response?.data;
      setError(data ? Object.values(data).flat().join(" ") : "No se pudo crear la cuenta.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Crear cuenta</h1>
        {error && <p className="error">{error}</p>}
        <label>
          Nombre
          <input value={form.first_name} onChange={(e) => update("first_name", e.target.value)} />
        </label>
        <label>
          Apellido
          <input value={form.last_name} onChange={(e) => update("last_name", e.target.value)} />
        </label>
        <label>
          Usuario
          <input value={form.username} onChange={(e) => update("username", e.target.value)} required />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={(e) => update("email", e.target.value)} required />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={form.password}
            onChange={(e) => update("password", e.target.value)}
            required
          />
        </label>
        <label>
          Soy...
          <select value={form.role} onChange={(e) => update("role", e.target.value)}>
            <option value="STUDENT">Estudiante</option>
            <option value="TEACHER">Profesor</option>
          </select>
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? "Creando..." : "Crear cuenta"}
        </button>
        <p>
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </p>
      </form>
    </div>
  );
}
