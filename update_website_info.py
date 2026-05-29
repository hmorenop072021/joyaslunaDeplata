import xmlrpc.client
import base64
import os

# --- CONFIGURACIÓN DE CONEXIÓN ---
URL = "http://localhost:8069"
DB = "lunadeplata"
USER = "hmorenop.072021@gmail.com"
PASSWORD = "Arena123"

def update_company_info():
    try:
        common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
        uid = common.authenticate(DB, USER, PASSWORD, {})
        if not uid:
            print("Error: Autenticación fallida.")
            return
        
        models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
        
        # 1. ACTUALIZAR INFO DE LA COMPAÑÍA
        company_ids = models.execute_kw(DB, uid, PASSWORD, 'res.company', 'search', [[]])
        if company_ids:
            company_id = company_ids[0]
            
            # Cargar Logo
            logo_path = "logo_lunadeplata.svg"
            logo_b64 = False
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    logo_b64 = base64.b64encode(f.read()).decode('utf-8')

            company_data = {
                'phone': '56965649305',
                'email': 'lopez.dv@gmail.com',
                'name': 'Lunadeplata',
            }
            if logo_b64:
                company_data['logo'] = logo_b64
            
            models.execute_kw(DB, uid, PASSWORD, 'res.company', 'write', [company_id, company_data])
            print(f"Información de compañía actualizada: {company_data['name']}")

        # 2. ACTUALIZAR INFO DEL WEBSITE (Social Links)
        website_ids = models.execute_kw(DB, uid, PASSWORD, 'website', 'search', [[]])
        if website_ids:
            for w_id in website_ids:
                # Telegram no es un campo estándar en res.company/website por defecto en Odoo core, 
                # pero podemos intentar guardarlo en un campo de notas o simplemente informar.
                # Odoo 17 suele tener campos social_*. 
                website_data = {
                    'social_instagram': 'https://www.instagram.com/danilunadeplata', # Sugerido si existe
                    # Para Telegram, a veces se usa un snippet personalizado en el footer.
                }
                # Intentamos escribir, si falla ignoramos (campos pueden no existir)
                try:
                    models.execute_kw(DB, uid, PASSWORD, 'website', 'write', [w_id, website_data])
                    print(f"Website ID {w_id} social links actualizados.")
                except:
                    pass

        print("\nActualización completada exitosamente.")
        print("Teléfono:", '56965649305')
        print("Email:", 'lopez.dv@gmail.com')
        print("Telegram: @danilunadeplata")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_company_info()
