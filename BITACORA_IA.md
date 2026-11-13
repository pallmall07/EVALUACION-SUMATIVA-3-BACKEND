# Bitácora de uso de IA

## 13 de noviembre de 2026

| Solicitud | Resultado de la IA | Decisión |
| --- | --- | --- |
| Proponer requerimientos funcionales iniciales para la aplicación. | Lista de propuestas para usuarios, productos, pedidos, retiro, administración y persistencia SQL. | Se usó como orientación; los requerimientos de la evaluación tienen prioridad. |
| Apoyar el requerimiento RF-01 de modelos, administración y datos de prueba. | Ejemplos iniciales de modelos Django, configuración del Admin y carga de datos. | Se revisó contra el código. Se corrigió el comando de prueba porque solo contenía cuatro productos y no asignaba la descripción obligatoria. |
| Añadir `BITACORA_IA.md` y documentar cómo ejecutar el proyecto y las cuentas de prueba en `README.md`. | Borradores de ambos documentos. | Se corrigieron para coincidir con la estructura y configuración reales del proyecto; se reemplazaron los pasos de fixtures por el comando de gestión existente. |
| Preparar el primer avance para GitHub. | Revisión del estado Git y de los archivos del proyecto. | Se eligió un repositorio público, se conservará la estructura actual y se excluirán el entorno virtual y archivos locales generados. No se ha publicado el repositorio todavía. |

## Cambios aceptados en este avance

- Se incorporó el comando de carga con cuatro categorías, veinte productos y tres usuarios de demostración.
- Se añadió la migración inicial de los modelos.
- Se añadieron instrucciones de instalación y ejecución, dependencias y reglas de exclusión para Git.
- Las credenciales de demostración se documentan explícitamente como locales y no aptas para producción.
- Se quitó de las rutas una inclusión a `orders.urls`, que no existe todavía y bloqueaba los comandos de Django.

## Elementos descartados o pendientes

- Se descartó asumir que los ejemplos iniciales de la IA ya estaban aplicados al repositorio.
- Falta crear el repositorio en GitHub y conectarlo como remoto antes de publicar.