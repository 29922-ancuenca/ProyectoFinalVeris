# ProyectoFinalHumanas

## Estructura

- `frontend/`: templates y archivos estáticos (CSS/JS/IMG)
- `backend/`: aplicación Flask, rutas, repositorios y acceso a BD

## Ejecutar

1) Instalar dependencias:

`pip install -r requirements.txt`

2) Levantar el servidor:

`python backend/app.py`

## Base de datos

- Motor: MySQL
- Base: `humanas`
- Credenciales por defecto en [backend/config.py](backend/config.py) 

## Navegación CRUD (parámetro `d`)
Las pantallas CRUD usan un parámetro `d` en la URL con formato `base64("op/id")`.

- `new/0` crear
- `act/<id>` editar
- `det/<id>` detalle (solo lectura)
- `del/<id>` eliminar