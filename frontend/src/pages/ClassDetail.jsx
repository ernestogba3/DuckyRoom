import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function ClassDetail() {
  const { id } = useParams();
  const { user } = useAuth();

  const [classroom, setClassroom] = useState(null);
  const [announcements, setAnnouncements] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [tab, setTab] = useState("stream");
  const [error, setError] = useState("");

  const [newAnnouncement, setNewAnnouncement] = useState("");
  const [newAssignment, setNewAssignment] = useState({ title: "", description: "", points: 100 });
  const [submissionText, setSubmissionText] = useState({});

  const isTeacher = classroom && user && classroom.teacher.id === user.id;

  function loadAll() {
    api.get(`/classrooms/${id}/`).then(({ data }) => setClassroom(data));
    api.get(`/announcements/?classroom=${id}`).then(({ data }) => setAnnouncements(data));
    api.get(`/assignments/?classroom=${id}`).then(({ data }) => setAssignments(data));
  }

  useEffect(loadAll, [id]);

  async function handlePostAnnouncement(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/announcements/", { classroom: id, content: newAnnouncement });
      setNewAnnouncement("");
      loadAll();
    } catch {
      setError("No se pudo publicar el anuncio.");
    }
  }

  async function handleCreateAssignment(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/assignments/", { classroom: id, ...newAssignment });
      setNewAssignment({ title: "", description: "", points: 100 });
      loadAll();
    } catch {
      setError("No se pudo crear la tarea.");
    }
  }

  async function handleSubmit(assignmentId) {
    setError("");
    try {
      await api.post(`/assignments/${assignmentId}/submit/`, {
        content: submissionText[assignmentId] || "",
      });
      loadAll();
    } catch {
      setError("No se pudo entregar la tarea.");
    }
  }

  if (!classroom) return <p className="page-loading">Cargando clase...</p>;

  return (
    <div className="page">
      <div className="class-hero">
        <h1>{classroom.name}</h1>
        <p>
          {classroom.subject} · {classroom.section}
        </p>
        {isTeacher && <p className="code">Código para invitar: {classroom.code}</p>}
      </div>

      <div className="tabs">
        <button className={tab === "stream" ? "active" : ""} onClick={() => setTab("stream")}>
          Tablón
        </button>
        <button className={tab === "work" ? "active" : ""} onClick={() => setTab("work")}>
          Trabajo de clase
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {tab === "stream" && (
        <div>
          {isTeacher && (
            <form className="card form-card" onSubmit={handlePostAnnouncement}>
              <textarea
                placeholder="Anuncia algo a tu clase..."
                value={newAnnouncement}
                onChange={(e) => setNewAnnouncement(e.target.value)}
                required
              />
              <button type="submit">Publicar</button>
            </form>
          )}
          {announcements.map((a) => (
            <div className="card" key={a.id}>
              <strong>{a.author.first_name || a.author.username}</strong>
              <p>{a.content}</p>
              <small>{new Date(a.created_at).toLocaleString()}</small>
            </div>
          ))}
        </div>
      )}

      {tab === "work" && (
        <div>
          {isTeacher && (
            <form className="card form-card" onSubmit={handleCreateAssignment}>
              <input
                placeholder="Título de la tarea"
                value={newAssignment.title}
                onChange={(e) => setNewAssignment({ ...newAssignment, title: e.target.value })}
                required
              />
              <textarea
                placeholder="Instrucciones"
                value={newAssignment.description}
                onChange={(e) => setNewAssignment({ ...newAssignment, description: e.target.value })}
              />
              <input
                type="number"
                value={newAssignment.points}
                onChange={(e) => setNewAssignment({ ...newAssignment, points: e.target.value })}
              />
              <button type="submit">Crear tarea</button>
            </form>
          )}
          {assignments.map((a) => (
            <div className="card" key={a.id}>
              <h3>{a.title}</h3>
              <p>{a.description}</p>
              <small>{a.points} puntos</small>

              {!isTeacher && (
                <div className="submit-box">
                  {a.my_submission ? (
                    <p className="submitted">
                      ✅ Entregado {a.my_submission.grade != null && `· Calificación: ${a.my_submission.grade}`}
                    </p>
                  ) : (
                    <>
                      <textarea
                        placeholder="Escribe tu respuesta..."
                        value={submissionText[a.id] || ""}
                        onChange={(e) => setSubmissionText({ ...submissionText, [a.id]: e.target.value })}
                      />
                      <button onClick={() => handleSubmit(a.id)}>Entregar</button>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
