# Arcadia Courts

Arcadia Courts is a Django web application for renting football and futsal courts with a glassmorphism-inspired UI, real-time availability checks, and AJAX-driven booking flows. It is optimised for mobile-first responsiveness and adheres to Shneiderman’s 8 Golden Rules through consistent design patterns, progressive feedback, and undoable actions.

## Features

- **Landing & discovery** – Search by name, surface type, price range, and preferred date or time with instant, debounce-backed results.
- **Court detail pages** – Seven-day availability strip with 60-minute slots, maintenance blocks, and live booking states.
- **AJAX bookings** – Create soft-held bookings (10 minute countdown), confirm mock payments, cancel with undo, and view receipts.
- **User dashboards** – Manage pending and confirmed bookings with inline actions and status chips.
- **Favorites** – Toggle quick access to preferred courts with optimistic UI feedback.
- **Admin ready** – Default Django admin enabled for managing courts, maintenance windows, and bookings.
- **Seed command** – `python manage.py seed_demo` populates demo courts, bookings, and a demo user (demo/demo12345).

## Technology Stack

- Python 3.11+, Django 5.x, SQLite (development) with optional PostgreSQL support via environment variables.
- Vanilla HTML templates, CSS, and JavaScript (`fetch` API, no SPA frameworks).
- Whitenoise for static asset serving, Inter typeface, and reusable JS modules for API, UI utilities, availability, and toasts.

## Getting Started

1. **Clone & install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

3. **Load demo data (optional but recommended)**
   ```bash
   python manage.py seed_demo
   ```
   This creates six sample courts, maintenance windows, assorted bookings, and a demo user (`demo/demo12345`).

4. **Run the development server**
   ```bash
   python manage.py runserver
   ```

5. **Access the app**
   - Public site: http://127.0.0.1:8000/
   - Admin dashboard: http://127.0.0.1:8000/admin/ (create a superuser via `python manage.py createsuperuser`).

## Running Tests

Unit tests cover booking overlap logic, hold expirations, price calculations, and the availability endpoint.

```bash
python manage.py test bookings
```

## Configuration Notes

- Timezone defaults to `Asia/Jakarta`; update `TIME_ZONE` in `TK_PBP/settings.py` if required.
- Currency formatting uses Indonesian Rupiah (IDR) with thousand separators.
- CSRF tokens are enforced for all POST endpoints. The frontend uses a shared `csrfFetch` helper to attach the token header automatically.
- Static assets are collected into `staticfiles/` for production via `collectstatic` and served locally with Whitenoise.

## Project Structure

```
accounts/         Authentication views and forms (login/register/logout)
bookings/         Booking models, APIs, dashboard, and tests
core/             Landing page, shared templates, static assets, seed command
courts/           Court catalogue, availability logic, favorites
payments/         Mock payment service and receipt view
templates/        Base template consumed by all pages
```

## Demo Credentials

- **Demo user:** `demo`
- **Password:** `demo12345`

Feel free to extend the mock payment workflow, integrate a real provider, or customise the UI tokens under `core/static/core/css/main.css`.
