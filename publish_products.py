import xmlrpc.client
import sys

# --- CONFIGURACIÓN DE CONEXIÓN ---
URL = "http://localhost:8069"
DB = "lunadeplata"
USER = "hmorenop.072021@gmail.com"
PASSWORD = "Arena123"

def publish_all_products():
    try:
        common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
        uid = common.authenticate(DB, USER, PASSWORD, {})
        if not uid:
            print("Error: Autenticación fallida.")
            sys.exit(1)
        models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
        
        # 1. Buscar todos los productos que NO estén publicados
        product_ids = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search', [[('is_published', '=', False)]])
        
        if product_ids:
            print(f"Publicando {len(product_ids)} productos...")
            # 2. Actualizarlos todos a is_published = True
            models.execute_kw(DB, uid, PASSWORD, 'product.template', 'write', [product_ids, {'is_published': True}])
            print("¡Todos los productos han sido publicados con éxito!")
        else:
            print("Todos los productos ya estaban publicados.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    publish_all_products()
