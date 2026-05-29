import xmlrpc.client
import re

# --- CONFIGURACIÓN ODOO ---
URL = "http://localhost:8069"
DB = "lunadeplata"
USER = "hmorenop.072021@gmail.com"
PASSWORD = "Arena123"

# --- MOTOR DE CATEGORIZACIÓN ---
CATEGORY_MAP = {
    'Anillos': ['anillo', 'ring', 'solitario', 'alianza', 'sin fin', 'cintillo'],
    'Aros y Pendientes': ['aro', 'pendiente', 'zarcillo', 'caravana', 'earring', 'argolla'],
    'Collares y Cadenas': ['collar', 'cadena', 'gargantilla', 'necklace', 'dije', 'colgante', 'medalla'],
    'Pulseras': ['pulsera', 'brazalete', 'esclava', 'bracelet', 'tobillera'],
    'Relojes': ['reloj', 'watch'],
    'Sets y Conjuntos': ['set', 'conjunto', 'duo', 'trio']
}

def classify_product(name, description):
    text = f"{name} {description}".lower()
    for category, keywords in CATEGORY_MAP.items():
        if any(kw in text for kw in keywords):
            return category
    return 'Joyas Exclusivas'

def sync_categories():
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid = common.authenticate(DB, USER, PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

    print("🔍 Obteniendo productos y categorías actuales...")
    
    # 1. Obtener todos los productos publicados
    products = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_read', [
        [('sale_ok', '=', True)],
        ['id', 'name', 'website_description']
    ])

    # 2. Cache de categorías existentes en Odoo para evitar duplicados
    existing_categs = models.execute_kw(DB, uid, PASSWORD, 'product.public.category', 'search_read', [[], ['name']])
    categ_name_to_id = {c['name']: c['id'] for c in existing_categs}

    print(f"📦 Procesando {len(products)} productos...")

    updates_count = 0
    for p in products:
        desc_clean = re.sub('<[^<]+?>', '', p['website_description'] or "")
        target_category = classify_product(p['name'], desc_clean)

        # Crear categoría si no existe
        if target_category not in categ_name_to_id:
            print(f"🆕 Creando nueva categoría en Odoo: {target_category}")
            new_id = models.execute_kw(DB, uid, PASSWORD, 'product.public.category', 'create', [{
                'name': target_category
            }])
            categ_name_to_id[target_category] = new_id

        target_id = categ_name_to_id[target_category]

        # Actualizar el producto en Odoo
        models.execute_kw(DB, uid, PASSWORD, 'product.template', 'write', [
            [p['id']], 
            {'public_categ_ids': [(6, 0, [target_id])]} # Reemplazar categorías actuales por la inteligente
        ])
        updates_count += 1
        if updates_count % 50 == 0:
            print(f"✅ {updates_count} productos actualizados...")

    print(f"\n🚀 ¡Sincronización completada! {updates_count} joyas categorizadas en Odoo.")

if __name__ == "__main__":
    try:
        sync_categories()
    except Exception as e:
        print(f"❌ Error durante la sincronización: {e}")
