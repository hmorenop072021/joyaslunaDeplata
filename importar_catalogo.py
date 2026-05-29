import csv
import xmlrpc.client
import sys
import os
import base64
import requests

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

def download_image_as_base64(url):
    if not url or url.strip() == "" or url == '""':
        return False
    try:
        response = requests.get(url.strip('"'), timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        pass
    return False

def import_products():
    uid, models = get_odoo_connection()
    
    with open(CSV_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        products = list(reader)
        total = len(products)
        
        print(f"Iniciando Importación Avanzada (Descripciones HTML + Multi-Imagen) de {total} productos...")

        for index, row in enumerate(products, 1):
            try:
                sku = row.get('id', '').strip()
                name = row.get('name', '').strip()
                raw_desc = row.get('description', '').strip()
                price = row.get('price', '0.00')

                # 1. GENERAR DESCRIPCIÓN DETALLADA (HTML)
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

                # 2. BUSCAR O CREAR PRODUCTO
                existing_ids = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search', [[
                    '|', ('default_code', '=', sku), ('name', '=', name)
                ]])

                product_data = {
                    'name': name,
                    'list_price': float(price) if price else 0.0,
                    'website_description': detailed_description, # HTML para la web (se renderiza abajo)
                    'description_sale': raw_desc[:1000], # Texto plano para descripción corta/ventas
                    'default_code': sku,
                    'sale_ok': True,
                    'is_published': True,
                    'type': 'consu',
                }

                # 3. IMAGEN PRINCIPAL (image_url)
                img1 = download_image_as_base64(row.get('image_url', ''))
                if img1:
                    product_data['image_1920'] = img1

                if existing_ids:
                    product_id = existing_ids[0]
                    models.execute_kw(DB, uid, PASSWORD, 'product.template', 'write', [product_id, product_data])
                    status = "Actualizado"
                else:
                    product_id = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'create', [product_data])
                    status = "Creado"

                # 4. IMÁGENES EXTRA (image_url2, 3, 4)
                # Primero limpiamos las imágenes extra anteriores para no duplicar si re-ejecutamos
                models.execute_kw(DB, uid, PASSWORD, 'product.image', 'unlink', [
                    models.execute_kw(DB, uid, PASSWORD, 'product.image', 'search', [[('product_tmpl_id', '=', product_id)]])
                ])

                for col in ['image_url2', 'image_url3', 'image_url4']:
                    url_extra = row.get(col, '')
                    img_extra_b64 = download_image_as_base64(url_extra)
                    if img_extra_b64:
                        models.execute_kw(DB, uid, PASSWORD, 'product.image', 'create', [{
                            'name': f"{name} - {col}",
                            'image_1920': img_extra_b64,
                            'product_tmpl_id': product_id
                        }])

                print(f"[{index}/{total}] {status}: {name} (Desc. + Multi-Imagen)")

            except Exception as e:
                print(f"Error en {name}: {e}")

    print("\n¡Catálogo enriquecido con éxito!")

if __name__ == "__main__":
    import_products()
