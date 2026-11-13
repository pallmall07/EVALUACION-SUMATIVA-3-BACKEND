# Cafetería Fiores
# Cafetería Fiores

Aplicación web en Django para el avance de evaluación de Cafetería Fiores. Este avance incluye los modelos de categorías, productos y pedidos, su administración en Django Admin y un comando para cargar datos de prueba. La base de datos configurada por defecto es SQLite, una base de datos SQL.

## Requisitos

- Python 3.12
- Dependencias indicadas en `requirements.txt`

## Preparación

Desde la carpeta que contiene `manage.py`, crea y activa un entorno virtual e instala las dependencias:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En Windows, si PowerShell no permite activar el entorno, ejecuta sus comandos de Python usando `.\.venv\Scripts\python.exe`.

## Base de datos y datos de prueba

```powershell
python manage.py makemigrations orders
python manage.py migrate
python manage.py load_test_data
python manage.py runserver
```

Abre `http://127.0.0.1:8000/admin/` para acceder al panel de administración. El comando de datos de prueba se puede volver a ejecutar sin duplicar categorías ni productos.

## Usuarios de prueba

El comando `load_test_data` crea estas cuentas. Todas usan la contraseña `FioresDemo2026!`:

| Usuario | Rol |
| --- | --- |
| `encargado` | Administrador del sitio |
| `cliente1` | Cliente |
| `cliente2` | Cliente |

Son credenciales públicas de demostración; no deben reutilizarse fuera de una base de datos local de prueba.

## Alcance del avance

El proyecto está en desarrollo. Las funciones de navegación de menú y creación de pedidos para clientes aún no están implementadas en este avance. No usar la configuración actual para desplegar en producción.