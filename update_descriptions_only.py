import csv
import xmlrpc.client
import sys

# --- CONFIGURACIÓN DE CONEXIÓN ---
URL = "http://localhost:8069"
DB = "lunadeplata"
USER = "hmorenop.072021@gmail.com"
PASSWORD = "Arena123"
CSV_FILE = "products-+56983126243.csv"

def get_odoo_connection():
    try:
        common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
        uid = common.authenticate(DB, USER, PASSWORD, {})
        if not uid:
            print("Error: Autenticación fallida.")
            sys.exit(1)
        models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
        return uid, models
    except Exception as e:
        print(f"Error de conexión: {e}")
        sys.exit(1)

def update_descriptions():
    uid, models = get_odoo_connection()
    
    with open(CSV_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        products = list(reader)
        total = len(products)
        
        print(f"Actualizando descripciones para {total} productos (sin imágenes)...")

        for index, row in enumerate(products, 1):
            try:
                sku = row.get('id', '').strip()
                name = row.get('name', '').strip()
                raw_desc = row.get('description', '').strip()
                price = row.get('price', '0.00')

                # 1. GENERAR HTML (Para la parte inferior)
                detailed_description = f"""
                    <div class="product_details_html" style="font-family: Arial, sans-serif;">
                        <h2 style="color: #4b4b4b;">{name}</h2>
                        <hr/>
                        <p><strong>Referencia/SKU:</strong> {sku}</p>
                        <p><strong>Precio Catálogo:</strong> ${float(price):,.0f}</p>
                        <p style="margin-top: 15px; color: #666;">{raw_desc}</p>
                        <ul style="margin-top: 10px; color: #888; font-size: 12px;">
                            <li>Garantía de Calidad - Lunadeplata</li>
                            <li>Joyas de Alta Calidad</li>
                        </ul>
                    </div>
                """

                # 2. BUSCAR PRODUCTO POR SKU
                product_ids = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search', [[
                    ('default_code', '=', sku)
                ]])

                if product_ids:
                    product_id = product_ids[0]
                    # ACTUALIZAR SOLO DESCRIPCIONES
                    models.execute_kw(DB, uid, PASSWORD, 'product.template', 'write', [product_id, {
                        'website_description': detailed_description,
                        'description_sale': raw_desc[:1000] # Texto plano para evitar HTML visible arriba
                    }])
                    if index % 10 == 0 or index == total:
                        print(f"[{index}/{total}] Actualizado: {name}")
                else:
                    print(f"[{index}/{total}] Saltado (no encontrado): {sku} - {name}")

            except Exception as e:
                print(f"Error en {sku}: {e}")

    print("\n¡Descripciones actualizadas con éxito!")

if __name__ == "__main__":
    update_descriptions()
