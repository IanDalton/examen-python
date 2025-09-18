# Book&Byte Exam Autograder

Este repositorio ahora incluye un portal estático en Next.js y un backend en FastAPI para gestionar los envíos de los alumnos y ejecutar las pruebas automáticas proporcionadas en la carpeta `tests`.

## Estructura

```
backend/        # FastAPI + Pytest runner
frontend/       # Aplicación Next.js estática
submissions/    # Carpeta generada con las entregas (ignoradas por git)
```

## Puesta en marcha

1. **Backend**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
   El backend escucha en `http://localhost:8000` y expone:
   - `POST /api/submit`: recibe `student_name` y un archivo `.py`, guarda la entrega, ejecuta Pytest y devuelve el puntaje y el detalle de los tests.
   - `GET /api/logs`: devuelve el historial agregado de fallos acumulados.

2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   La interfaz estará disponible en `http://localhost:3000`. Puedes configurar otra URL del backend estableciendo la variable `NEXT_PUBLIC_BACKEND_URL` antes de construir o ejecutar la app.

3. **Build estático**
   ```bash
   npm run build
   ```
   El resultado exportado quedará en `frontend/out` listo para servir en cualquier hosting estático.

## Flujo de calificación

1. El alumno completa su nombre y adjunta su archivo `bookbyte.py`.
2. El backend guarda una copia en `submissions/<timestamp>_<nombre>.py`.
3. Se crea un entorno temporal donde se colocan los tests oficiales y el archivo enviado.
4. Se ejecuta `pytest` y se recopila el resultado individual de cada test.
5. El puntaje se calcula como `tests_aprobados / tests_totales * 100`.
6. Los fallos se registran en `backend/failure_log.json` sumando cuántas veces falló cada test.
7. El frontend muestra el detalle al alumno y actualiza el historial global para el docente.

## Notas

- Solo se aceptan archivos `.py`.
- El backend necesita acceso a la carpeta `tests` en la raíz del repositorio.
- El historial de fallos se conserva mientras no se elimine `backend/failure_log.json`.
