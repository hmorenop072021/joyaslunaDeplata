# 💎 Proyecto Catálogo Lunadeplata

Este documento detalla el estado actual del catálogo boutique automatizado sincronizado entre **Odoo** y **Cloudflare Pages**.

## 🚀 Arquitectura del Sistema
1.  **Backend (Odoo 17):** Fuente de verdad para productos, precios, fotos y atributos.
2.  **Generador (Python):** Script `generate_static_catalog.py` que extrae datos vía XML-RPC y construye un sitio estático profesional.
3.  **Publicación (GitHub):** Repositorio `joyaslunaDeplata` que recibe los archivos del generador.
4.  **Hosting (Cloudflare Pages):** Publica automáticamente el contenido del repositorio.

## 🛠️ Trabajo Realizado

### 🎨 Diseño y UX
- **Estética Boutique:** Marca de agua difuminada con el logo de la empresa y paleta de colores de lujo.
- **Interactividad Pro:** Efecto de lupa (Zoom 1.6x) estilo Odoo en detalles de producto y galería de imágenes dinámica.
- **Navegación:** Menú por categorías inteligentes, paginación de 12 joyas por página y tarjetas con sombras suaves.
- **Idioma:** 100% Español profesional con textos persuasivos sobre los beneficios de la Plata 925.

### 🧠 Inteligencia de Datos
- **Categorización Automática:** Script `sync_odoo_categories.py` que clasifica las joyas en Odoo (Anillos, Aros, etc.) basándose en el nombre y descripción.
- **Filtros de Negocio:** Se excluyen conceptos administrativos como "Ad-Valorem", "Flete" o productos con precio $0.
- **Optimización:** Carga de imágenes con `lazy loading` y eliminación total de scripts de terceros innecesarios (Loader, Swiper).

### ⚙️ Automatización (GitHub)
- El script de generación realiza automáticamente el `git add`, `commit` y `push --force` a la rama `main`.

## 📍 Datos de Configuración
- **URL Odoo:** `http://localhost:8069` (Docker local)
- **Repo GitHub:** `https://github.com/hmorenop072021/joyaslunaDeplata.git`
- **Contacto:** WhatsApp `+56965649305` | Instagram `@danilunadeplata`

## ⚠️ Tarea Pendiente Crítica
**Corregir el despliegue en Cloudflare:**
Actualmente el despliegue falla porque Cloudflare intenta ejecutar un comando de "Worker" (`npx wrangler deploy`).
**Solución:**
1. Entrar al panel de **Cloudflare Pages > joyaslunadeplata > Settings > Build & deployments**.
2. **Build command:** Debe quedar totalmente **VACÍO**.
3. **Build output directory:** Debe ser un punto `.` o dejarse vacío.
4. Reintentar el despliegue (Retry deployment).

## 🔄 Cómo actualizar el catálogo
Para sincronizar cambios realizados en Odoo hacia la web, ejecutar:
```bash
python3 /home/oem/Lunadeplata/generate_static_catalog.py
```
*(Asegúrate de que los contenedores de Odoo estén arriba).*

---
**Documento generado el 29 de Marzo de 2026.**
