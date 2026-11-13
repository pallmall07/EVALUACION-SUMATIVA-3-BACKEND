# Cafetería Fiores

Aplicación web en Django para la evaluación de Cafetería Fiores. Incluye modelos de categorías, productos y pedidos, autenticación por rol, catálogo de clientes, carrito en sesión y confirmación de pedidos. La base de datos configurada por defecto es SQLite, una base de datos SQL.

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

Abre `http://127.0.0.1:8000/login/` para iniciar sesión. La ruta raíz redirige al panel correspondiente al rol; el menú muestra el usuario conectado y su rol. La sesión expira tras 30 minutos de inactividad. El catálogo del cliente permite buscar por nombre y filtrar por categoría activa; muestra precios en CLP y marca como agotados los productos sin stock.

El cliente puede editar y quitar productos, vaciar el carrito y confirmar un pedido con una hora de retiro entre 08:00 y 18:00, al menos 20 minutos después de la hora actual. La confirmación revisa todo el stock antes de crear pedido y detalles; si falta stock, no crea el pedido ni descuenta productos parcialmente.

El encargado también puede entrar al panel de Django Admin desde el enlace del menú o en `http://127.0.0.1:8000/admin/`. Los clientes no pueden acceder a las rutas reservadas al encargado. El comando de datos de prueba se puede volver a ejecutar sin duplicar categorías ni productos.

## Usuarios de prueba

El comando `load_test_data` crea estas cuentas. Todas usan la contraseña `FioresDemo2026!`:

| Usuario | Rol |
| --- | --- |
| `encargado` | Administrador del sitio |
| `cliente1` | Cliente |
| `cliente2` | Cliente |

Son credenciales públicas de demostración; no deben reutilizarse fuera de una base de datos local de prueba.

## Alcance del avance

El proyecto está en desarrollo. La gestión del catálogo desde páginas propias del encargado (RF-04) sigue pendiente. No usar la configuración actual para desplegar en producción.