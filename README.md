# CRM de practica

## Requisitos

- Python 3.10+
- Node.js 18+
- Angular CLI (`npm install -g @angular/cli`)

## Backend (Django)

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

El backend corre en `http://localhost:8000`.

## Frontend (Angular)

```bash
cd frontend
npm install
ng serve
```

O con proxy para que `/api` redirija al backend:

```bash
cd frontend
ng serve --proxy-config proxy.conf.json
```

El frontend corre en `http://localhost:4200`.



```base de datos sqlite dentro del backend
```
