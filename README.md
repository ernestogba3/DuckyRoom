# DuckyRoom 🦆

Un clon educativo de Google Classroom, hecho para **aprender** construyendo:
backend con **Django + Django REST Framework** y frontend con **React + Vite**,
comunicándose vía una API JSON con autenticación JWT.

## Qué hace

- **Cuentas con rol** de profesor o estudiante, con login por JWT.
- **Clases** con un código de 6 caracteres para invitar, como en Classroom.
- **Tablón de anuncios** que publica el profesor.
- **Tareas y entregas**, con puntos y nota.
- **Calendario con vista mensual** de exámenes y proyectos, con los eventos
  de todas tus clases juntos.

## ¿Por qué esta arquitectura?

Backend y frontend están separados y se comunican solo por HTTP/JSON. Esto es
lo que se usa en la mayoría de apps reales en producción, y te permite:

- Escalar cada parte por separado (el frontend puede vivir en un CDN, el
  backend en varios servidores detrás de un balanceador).
- Reemplazar el frontend en el futuro (app móvil, otro framework) sin tocar
  el backend.
- Entender claramente la frontera entre "datos y reglas de negocio" (backend)
  y "presentación e interacción" (frontend).

```
DuckyRoom/
├── backend/     Django + DRF → expone la API en /api/
│   ├── accounts/     Usuario personalizado con roles (profesor/estudiante) + JWT
│   └── classrooms/   Clases, anuncios, tareas, entregas y calendario
├── frontend/    React + Vite → consume la API
│   └── src/
│       ├── api/       Cliente axios con manejo automático de JWT
│       ├── context/    Estado global de autenticación
│       ├── pages/       Login, Registro, Dashboard, Detalle de clase, Calendario
│       └── components/  Navbar, rutas protegidas
└── docker-compose.yml   Para correr todo junto con Postgres
```

## Modelo de datos (backend/classrooms/models.py)

- **ClassRoom**: una clase, con un `code` único de 6 caracteres para
  invitar estudiantes (como Google Classroom).
- **Announcement**: anuncios que el profesor publica en el tablón.
- **Assignment**: tareas con puntos y fecha de entrega.
- **Submission**: la entrega de un estudiante para una tarea (única por
  estudiante+tarea).
- **CalendarEvent**: exámenes, proyectos u otros eventos con fecha. Los puede
  crear **cualquier miembro** de la clase (profesor o estudiante), para poder
  apuntar los proyectos que haces con tus compañeros, y los ve toda la clase.
  Solo quien lo creó, o el profesor, puede borrarlo.

Los permisos (`classrooms/permissions.py`) controlan quién puede hacer qué:
solo el profesor de una clase puede crear tareas o anuncios; solo el dueño
de una entrega o el profesor de la clase pueden verla/calificarla; y en el
calendario cualquier miembro crea eventos, pero solo los borra quien los creó
(o el profesor).

## El calendario

La vista mensual está en `frontend/src/pages/Calendar.jsx` y la cuadrícula
está construida a mano, sin librerías de calendario, para que se pueda leer
y entender entera. Dos detalles que merece la pena mirar:

- **La semana empieza en lunes.** `Date.getDay()` devuelve 0 para domingo,
  así que se gira con `(primerDia.getDay() + 6) % 7` para saber cuántas
  casillas vacías van delante del día 1.
- **Las fechas se construyen a mano** con `toISODate(año, mes, día)` en vez
  de `toISOString()`. `toISOString()` convierte a UTC, y en España un evento
  a medianoche se mostraría el día anterior.

El backend filtra por mes con `?month=YYYY-MM`, así que cada vez que cambias
de mes solo se piden los eventos de ese mes en lugar de traerlos todos.

Además de los eventos que creas tú, el calendario muestra automáticamente las
**fechas de entrega de las tareas** (`Assignment.due_date`), para no tener que
apuntarlas dos veces.

## Cómo correrlo localmente (sin Docker)

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser   # opcional, para entrar a /admin/
python manage.py runserver
```

La API queda en `http://127.0.0.1:8000/api/`. El panel de administración
de Django (útil para ver/editar datos directamente) en
`http://127.0.0.1:8000/admin/`.

### 2. Frontend

En otra terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Abre `http://localhost:5173`.

### 3. Con Docker (opcional, usa Postgres en vez de SQLite)

```bash
docker compose up --build
```

## Flujo básico de uso

1. Regístrate eligiendo el rol **Profesor**.
2. Crea una clase → se genera un código de 6 caracteres.
3. Regístrate (en otra sesión/navegador) como **Estudiante** y únete con
   ese código.
4. El profesor publica anuncios y crea tareas; el estudiante las entrega
   desde la pestaña "Trabajo de clase".
5. En **Calendario** (barra superior) tienes la vista mensual con los
   exámenes y proyectos de todas tus clases. Haz clic en un día para
   marcar algo nuevo. Las fechas de entrega de las tareas aparecen solas.

## Tests

```bash
cd backend
venv\Scripts\python.exe manage.py test    # en Linux/Mac: python manage.py test
```

Están en `backend/classrooms/tests.py` y cubren sobre todo los permisos, que
es donde es fácil equivocarse: que un estudiante no pueda publicar anuncios ni
crear tareas, que no veas eventos de clases en las que no estás, que no puedas
borrar el evento de otra persona, y que el filtro `?month=` funcione.

## Endpoints principales de la API

| Método | Endpoint                          | Descripción                          |
|--------|------------------------------------|---------------------------------------|
| POST   | `/api/auth/register/`             | Crear cuenta                          |
| POST   | `/api/auth/token/`                | Login (devuelve access + refresh)     |
| POST   | `/api/auth/token/refresh/`        | Renovar el access token               |
| GET    | `/api/auth/me/`                   | Usuario autenticado actual            |
| GET/POST | `/api/classrooms/`              | Listar / crear clases                 |
| POST   | `/api/classrooms/join/`           | Unirse a una clase con un código      |
| GET/POST | `/api/announcements/?classroom=<id>` | Anuncios de una clase           |
| GET/POST | `/api/assignments/?classroom=<id>`   | Tareas de una clase             |
| POST   | `/api/assignments/<id>/submit/`   | Entregar una tarea (como estudiante)  |
| GET/POST | `/api/events/`                  | Exámenes y proyectos del calendario   |
| GET    | `/api/events/?month=YYYY-MM`      | Eventos de un mes (lo usa la vista mensual) |
| GET/PATCH | `/api/submissions/`             | Ver / calificar entregas              |

## Ideas para seguir aprendiendo y extender el proyecto

- **Más tests**: ya hay tests de permisos en `classrooms/tests.py`. Añade los
  que faltan: entregar dos veces la misma tarea, calificar siendo estudiante...
- **Vista semanal o de agenda** en el calendario, reutilizando el mismo
  endpoint `/api/events/`.
- **Avisos de lo que viene**: una lista de "próximos exámenes" en el
  dashboard, filtrando eventos por fecha futura.
- **Subida de archivos**: `Submission.attachment` ya soporta archivos;
  falta un `<input type="file">` en el frontend.
- **Calificaciones**: construye una vista para que el profesor vea todas
  las entregas de una tarea y las califique.
- **Websockets/polling**: notificaciones en tiempo real cuando se publica
  un anuncio.
- **Roles múltiples**: un usuario que es profesor en una clase y
  estudiante en otra.
- **Despliegue**: prueba desplegar el backend en Railway/Render y el
  frontend en Vercel/Netlify, apuntando `VITE_API_URL` a la URL del backend.
