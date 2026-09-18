import { useEffect, useMemo, useState } from "react";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";

const WEEKDAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
const MONTHS = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const EVENT_LABELS = { EXAM: "Examen", PROJECT: "Proyecto", OTHER: "Otro" };

/**
 * Construye "YYYY-MM-DD" a partir de números.
 * Ojo: no usamos toISOString() porque convierte a UTC y, según tu zona
 * horaria, podría devolver el día anterior.
 */
function toISODate(year, monthIndex, day) {
  return `${year}-${String(monthIndex + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

/** Días que se muestran en la cuadrícula, empezando en lunes. */
function buildMonthGrid(year, monthIndex) {
  const firstDay = new Date(year, monthIndex, 1);
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  // getDay() devuelve 0 para domingo; lo giramos para que la semana empiece en lunes.
  const leadingBlanks = (firstDay.getDay() + 6) % 7;

  const cells = Array.from({ length: leadingBlanks }, () => null);
  for (let day = 1; day <= daysInMonth; day++) {
    cells.push(day);
  }
  while (cells.length % 7 !== 0) {
    cells.push(null);
  }
  return cells;
}

const emptyForm = { classroom: "", title: "", description: "", event_type: "EXAM" };

export default function Calendar() {
  const { user } = useAuth();
  const today = new Date();

  const [year, setYear] = useState(today.getFullYear());
  const [monthIndex, setMonthIndex] = useState(today.getMonth());
  const [events, setEvents] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [classes, setClasses] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const monthParam = `${year}-${String(monthIndex + 1).padStart(2, "0")}`;

  function loadMonth() {
    setLoading(true);
    Promise.all([
      api.get(`/events/?month=${monthParam}`),
      api.get("/assignments/"),
      api.get("/classrooms/"),
    ])
      .then(([eventsRes, assignmentsRes, classesRes]) => {
        setEvents(eventsRes.data);
        setAssignments(assignmentsRes.data.filter((a) => a.due_date));
        setClasses(classesRes.data);
      })
      .catch(() => setError("No se pudo cargar el calendario."))
      .finally(() => setLoading(false));
  }

  useEffect(loadMonth, [monthParam]);

  // Agrupa todo lo que cae en cada día: { "2026-10-15": [ {...}, {...} ] }
  const itemsByDate = useMemo(() => {
    const grouped = {};

    for (const event of events) {
      (grouped[event.date] ??= []).push({
        key: `event-${event.id}`,
        kind: event.event_type,
        title: event.title,
        description: event.description,
        className: event.classroom_name,
        classroom: event.classroom,
        createdBy: event.created_by,
        id: event.id,
        editable: true,
      });
    }

    for (const assignment of assignments) {
      const due = new Date(assignment.due_date);
      const date = toISODate(due.getFullYear(), due.getMonth(), due.getDate());
      (grouped[date] ??= []).push({
        key: `assignment-${assignment.id}`,
        kind: "ASSIGNMENT",
        title: assignment.title,
        description: assignment.description,
        className: classes.find((c) => c.id === assignment.classroom)?.name ?? "",
        editable: false,
      });
    }

    return grouped;
  }, [events, assignments, classes]);

  const cells = buildMonthGrid(year, monthIndex);
  const todayISO = toISODate(today.getFullYear(), today.getMonth(), today.getDate());

  function changeMonth(step) {
    const next = new Date(year, monthIndex + step, 1);
    setYear(next.getFullYear());
    setMonthIndex(next.getMonth());
    setSelectedDate(null);
    setShowForm(false);
  }

  function goToToday() {
    setYear(today.getFullYear());
    setMonthIndex(today.getMonth());
    setSelectedDate(todayISO);
  }

  function selectDay(day) {
    if (!day) return;
    setSelectedDate(toISODate(year, monthIndex, day));
    setShowForm(false);
    setError("");
  }

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/events/", { ...form, date: selectedDate });
      setForm(emptyForm);
      setShowForm(false);
      loadMonth();
    } catch (err) {
      const data = err.response?.data;
      setError(data ? Object.values(data).flat().join(" ") : "No se pudo crear el evento.");
    }
  }

  async function handleDelete(eventId) {
    setError("");
    try {
      await api.delete(`/events/${eventId}/`);
      loadMonth();
    } catch {
      setError("No puedes borrar este evento (solo quien lo creó o el profesor).");
    }
  }

  const selectedItems = selectedDate ? itemsByDate[selectedDate] ?? [] : [];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Calendario</h1>
        <div className="actions">
          <button className="btn-secondary" onClick={() => changeMonth(-1)}>
            ‹
          </button>
          <button className="btn-secondary" onClick={goToToday}>
            Hoy
          </button>
          <button className="btn-secondary" onClick={() => changeMonth(1)}>
            ›
          </button>
        </div>
      </div>

      <h2 className="month-title">
        {MONTHS[monthIndex]} {year}
      </h2>

      {error && <p className="error">{error}</p>}

      <div className="legend">
        <span className="legend-item">
          <i className="dot kind-EXAM" /> Examen
        </span>
        <span className="legend-item">
          <i className="dot kind-PROJECT" /> Proyecto
        </span>
        <span className="legend-item">
          <i className="dot kind-OTHER" /> Otro
        </span>
        <span className="legend-item">
          <i className="dot kind-ASSIGNMENT" /> Entrega de tarea
        </span>
      </div>

      {loading ? (
        <p>Cargando...</p>
      ) : (
        <div className="calendar">
          {WEEKDAYS.map((weekday) => (
            <div className="calendar-weekday" key={weekday}>
              {weekday}
            </div>
          ))}

          {cells.map((day, index) => {
            if (!day) return <div className="calendar-cell empty" key={`blank-${index}`} />;

            const date = toISODate(year, monthIndex, day);
            const items = itemsByDate[date] ?? [];
            const classNames = [
              "calendar-cell",
              date === todayISO ? "is-today" : "",
              date === selectedDate ? "is-selected" : "",
            ].join(" ");

            return (
              <button className={classNames} key={date} onClick={() => selectDay(day)}>
                <span className="day-number">{day}</span>
                <span className="day-items">
                  {items.slice(0, 3).map((item) => (
                    <span className={`chip kind-${item.kind}`} key={item.key}>
                      {item.title}
                    </span>
                  ))}
                  {items.length > 3 && <span className="more">+{items.length - 3} más</span>}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {selectedDate && (
        <div className="card day-panel">
          <div className="day-panel-header">
            <h3>{new Date(`${selectedDate}T00:00:00`).toLocaleDateString("es-ES", {
              weekday: "long", day: "numeric", month: "long", year: "numeric",
            })}</h3>
            {classes.length > 0 && (
              <button onClick={() => setShowForm((v) => !v)}>
                {showForm ? "Cancelar" : "+ Añadir evento"}
              </button>
            )}
          </div>

          {classes.length === 0 && (
            <p className="empty">Únete a una clase para poder añadir eventos.</p>
          )}

          {showForm && (
            <form className="form-card" onSubmit={handleCreate}>
              <select
                value={form.classroom}
                onChange={(e) => setForm({ ...form, classroom: e.target.value })}
                required
              >
                <option value="">Elige una clase...</option>
                {classes.map((c) => (
                  <option value={c.id} key={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              <select
                value={form.event_type}
                onChange={(e) => setForm({ ...form, event_type: e.target.value })}
              >
                <option value="EXAM">Examen</option>
                <option value="PROJECT">Proyecto</option>
                <option value="OTHER">Otro</option>
              </select>
              <input
                placeholder="Título (ej: Examen de la unidad 3)"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                required
              />
              <textarea
                placeholder="Detalles (opcional): temario, compañeros de grupo..."
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
              <button type="submit">Guardar</button>
            </form>
          )}

          {selectedItems.length === 0 ? (
            <p className="empty">Nada marcado este día.</p>
          ) : (
            <ul className="day-list">
              {selectedItems.map((item) => {
                const classroom = classes.find((c) => c.id === item.classroom);
                const canDelete =
                  item.editable &&
                  (item.createdBy?.id === user?.id || classroom?.teacher.id === user?.id);

                return (
                  <li key={item.key}>
                    <span className={`dot kind-${item.kind}`} />
                    <div className="day-list-text">
                      <strong>{item.title}</strong>
                      <small>
                        {item.kind === "ASSIGNMENT" ? "Entrega de tarea" : EVENT_LABELS[item.kind]}
                        {item.className && ` · ${item.className}`}
                        {item.createdBy && ` · lo añadió ${item.createdBy.first_name || item.createdBy.username}`}
                      </small>
                      {item.description && <p>{item.description}</p>}
                    </div>
                    {canDelete && (
                      <button className="btn-link danger" onClick={() => handleDelete(item.id)}>
                        Borrar
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
