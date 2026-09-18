import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [newClass, setNewClass] = useState({ name: "", section: "", subject: "", description: "" });

  const [showJoin, setShowJoin] = useState(false);
  const [joinCode, setJoinCode] = useState("");

  function loadClasses() {
    setLoading(true);
    api
      .get("/classrooms/")
      .then(({ data }) => setClasses(data))
      .catch(() => setError("No se pudieron cargar las clases."))
      .finally(() => setLoading(false));
  }

  useEffect(loadClasses, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/classrooms/", newClass);
      setNewClass({ name: "", section: "", subject: "", description: "" });
      setShowCreate(false);
      loadClasses();
    } catch {
      setError("No se pudo crear la clase. Revisa los datos.");
    }
  }

  async function handleJoin(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/classrooms/join/", { code: joinCode });
      setJoinCode("");
      setShowJoin(false);
      loadClasses();
    } catch (err) {
      setError(err.response?.data?.code?.[0] || "Código inválido.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Mis clases</h1>
        <div className="actions">
          {user?.role === "TEACHER" && (
            <button onClick={() => setShowCreate((v) => !v)}>+ Crear clase</button>
          )}
          {user?.role === "STUDENT" && (
            <button onClick={() => setShowJoin((v) => !v)}>Unirme a una clase</button>
          )}
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {showCreate && (
        <form className="card form-card" onSubmit={handleCreate}>
          <input
            placeholder="Nombre de la clase"
            value={newClass.name}
            onChange={(e) => setNewClass({ ...newClass, name: e.target.value })}
            required
          />
          <input
            placeholder="Sección"
            value={newClass.section}
            onChange={(e) => setNewClass({ ...newClass, section: e.target.value })}
          />
          <input
            placeholder="Materia"
            value={newClass.subject}
            onChange={(e) => setNewClass({ ...newClass, subject: e.target.value })}
          />
          <textarea
            placeholder="Descripción"
            value={newClass.description}
            onChange={(e) => setNewClass({ ...newClass, description: e.target.value })}
          />
          <button type="submit">Crear</button>
        </form>
      )}

      {showJoin && (
        <form className="card form-card" onSubmit={handleJoin}>
          <input
            placeholder="Código de la clase (ej: 7PC055)"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
            maxLength={6}
            required
          />
          <button type="submit">Unirme</button>
        </form>
      )}

      {loading ? (
        <p>Cargando...</p>
      ) : classes.length === 0 ? (
        <p className="empty">Todavía no tienes clases.</p>
      ) : (
        <div className="grid">
          {classes.map((c) => (
            <Link to={`/classes/${c.id}`} key={c.id} className="class-card">
              <h2>{c.name}</h2>
              <p>{c.subject || "Sin materia"}</p>
              <span className="badge">{c.teacher.first_name || c.teacher.username}</span>
              {user?.role === "TEACHER" && c.teacher.id === user.id && (
                <span className="code">Código: {c.code}</span>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
