import xmlrpc.client
import os
import base64
import shutil
import re
import urllib.parse
import sys
import subprocess

# === CONFIGURACIÓN ===
CONFIG = {
    "URL": "http://localhost:8069",
    "DB": "lunadeplata",
    "USER": "hmorenop.072021@gmail.com",
    "PASS": "Arena123",
    "PHONE": "56965649305",
    "EMAIL": "lopez.dv@gmail.com",
    "INSTA": "https://www.instagram.com/danilunadeplata",
    "GITHUB_REPO": "https://github.com/hmorenop072021/joyaslunaDeplata.git"
}

PATHS = {
    "BASE": "/home/oem/Lunadeplata",
    "TEMPLATE": "/home/oem/Lunadeplata/catalog_aj/aj",
    "PUBLIC": "/home/oem/Lunadeplata/catalog_public",
    "IMAGES": "/home/oem/Lunadeplata/catalog_public/images"
}

ITEMS_PER_PAGE = 12

CATEGORY_RULES = {
    'Anillos': ['anillo', 'ring', 'solitario', 'alianza', 'sin fin', 'cintillo'],
    'Aros y Pendientes': ['aro', 'pendiente', 'zarcillo', 'caravana', 'earring', 'argolla'],
    'Collares y Cadenas': ['collar', 'cadena', 'gargantilla', 'necklace', 'dije', 'colgante', 'medalla'],
    'Pulseras': ['pulsera', 'brazalete', 'esclava', 'bracelet', 'tobillera'],
    'Relojes': ['reloj', 'watch'],
    'Sets y Conjuntos': ['set', 'conjunto', 'duo', 'trio']
}

class CatalogGenerator:
    def __init__(self):
        self.template_cache = None
        self.categories = set()
        self.models = None
        self.uid = None

    def connect_odoo(self):
        try:
            common = xmlrpc.client.ServerProxy(f"{CONFIG['URL']}/xmlrpc/2/common")
            self.uid = common.authenticate(CONFIG['DB'], CONFIG['USER'], CONFIG['PASS'], {})
            if not self.uid: raise Exception("Error de credenciales")
            self.models = xmlrpc.client.ServerProxy(f"{CONFIG['URL']}/xmlrpc/2/object")
            print("🚀 Conexión con Odoo establecida")
        except Exception as e: print(f"❌ Error Odoo: {e}"); sys.exit(1)

    def classify(self, name, desc):
        text = f"{name} {desc}".lower()
        for cat, keywords in CATEGORY_RULES.items():
            if any(kw in text for kw in keywords): return cat
        return 'Joyas Exclusivas'

    def format_money(self, val):
        return f"${int(val):,}".replace(",", ".")

    def get_products(self):
        print("📦 Cargando joyas publicadas...")
        domain = [
            ('is_published', '=', True),
            ('name', 'not ilike', 'Ad-Valorem'),
            ('list_price', '>', 0)
        ]
        prods = self.models.execute_kw(CONFIG['DB'], self.uid, CONFIG['PASS'], 'product.template', 'search_read', [
            domain,
            ['id', 'name', 'list_price', 'website_description', 'image_1920', 'default_code', 'attribute_line_ids']
        ])
        for p in prods:
            extra = self.models.execute_kw(CONFIG['DB'], self.uid, CONFIG['PASS'], 'product.image', 'search_read', [[('product_tmpl_id', '=', p['id'])], ['image_1920']])
            p['extra_images'] = [img['image_1920'] for img in extra if img['image_1920']]
            p['smart_cat'] = self.classify(p['name'], re.sub('<[^<]+?>', '', p['website_description'] or ""))
            p['props'] = []
            if p.get('attribute_line_ids'):
                lines = self.models.execute_kw(CONFIG['DB'], self.uid, CONFIG['PASS'], 'product.template.attribute.line', 'read', [p['attribute_line_ids'], ['attribute_id', 'value_ids']])
                for l in lines:
                    vals = self.models.execute_kw(CONFIG['DB'], self.uid, CONFIG['PASS'], 'product.attribute.value', 'read', [l['value_ids'], ['name']])
                    p['props'].append(f"<b>{l['attribute_id'][1]}:</b> {', '.join([v['name'] for v in vals])}")
        return prods

    def save_img(self, b64, prefix, pid, idx=0):
        if not b64: return "img.png"
        fname = f"{prefix}_{pid}_{idx}.png"
        fpath = os.path.join(PATHS["IMAGES"], fname)
        if not os.path.exists(fpath):
            try:
                with open(fpath, "wb") as f: f.write(base64.b64decode(b64))
            except: return "img.png"
        return fname

    def get_template(self):
        if not self.template_cache:
            with open(os.path.join(PATHS["TEMPLATE"], "index.html"), "r") as f: t = f.read()
            t = re.sub(r'<div class="loader_bg">.*?</div>', '', t, flags=re.DOTALL)
            t = re.sub(r'<div id="(contact|clients)".*?<!-- end \1 -->', '', t, flags=re.DOTALL | re.IGNORECASE)
            t = t.replace('images/cac.png', '')
            t = re.sub(r'<link.*?swiper\.min\.css.*?>', '', t)
            t = re.sub(r'<img src="images/4.png".*?>', '', t)
            t = re.sub(r'<form>.*?</form>', '', t, flags=re.DOTALL)
            t = re.sub(r'<div class="menu-area">.*?</div>', '{{MENU_AREA}}', t, flags=re.DOTALL)
            self.template_cache = t
        return self.template_cache

    def build_base(self, is_index=False):
        html = self.get_template()
        extra_css = f"""
        <style>
            body {{ background: linear-gradient(rgba(255,255,255,0.96), rgba(255,255,255,0.96)), url('images/logo.png') fixed center no-repeat; background-size: 30%; }}
            .product-card {{ border: none; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); background: #fff; transition: 0.3s; height: 100%; overflow: hidden; }}
            .product-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.08); }}
            .product-price {{ color: #d4af37; font-weight: bold; font-size: 24px; }}
            .btn-wa {{ background: #25d366; color: #fff !important; font-weight: bold; border-radius: 50px; padding: 12px 30px; display: inline-flex; align-items: center; gap: 10px; text-decoration: none; }}
            .zoom-img-container {{ position: relative; overflow: hidden; border-radius: 12px; border: 1px solid #eee; background: #fff; max-height: 400px; margin: 0 auto; }}
            .zoom-img-container img {{ width: 100%; max-height: 400px; transition: transform 0.2s; object-fit: contain; }}
            .thumb-gallery img {{ width: 70px; height: 70px; object-fit: cover; border: 2px solid #eee; border-radius: 8px; cursor: pointer; transition: 0.2s; }}
            .thumb-gallery img.active {{ border-color: #d4af37; }}
            .logo-main {{ max-width: 220px; mix-blend-mode: multiply; }}
            .sort-bar-boutique {{ background: #fff; padding: 15px; border-radius: 12px; border: 1px solid #eee; display: flex; align-items: center; gap: 15px; margin-bottom: 30px; justify-content: flex-end; }}
            .btn-sort {{ background: #fdfdfd; border: 1px solid #ddd; padding: 6px 18px; border-radius: 20px; cursor: pointer; font-size: 14px; transition: 0.3s; }}
            .btn-sort:hover, .btn-sort.active {{ border-color: #d4af37; color: #d4af37; background: #fffdf5; }}
            .pagination-container {{ margin-top: 50px; text-align: center; border-top: 1px solid #eee; padding-top: 30px; }}
            .pagination-nav {{ display: inline-flex; gap: 10px; }}
            .pagination-nav a {{ padding: 10px 20px; border: 1px solid #ddd; border-radius: 8px; color: #555; text-decoration: none; background: #fff; transition: 0.3s; }}
            .pagination-nav a:hover {{ border-color: #d4af37; color: #d4af37; }}
            .pagination-nav a.active {{ background: #d4af37; color: #fff; border-color: #d4af37; pointer-events: none; }}
        </style>"""
        html = html.replace('</head>', f'{extra_css}</head>')
        if is_index:
            html = html.replace('{{MENU_AREA}}', '')
        else:
            m = f'<div class="menu-area"><nav class="main-menu"><ul class="menu-area-main"><li><a href="index.html">Inicio</a></li>'
            for c in sorted(list(self.categories)):
                slug = c.lower().replace(' ', '_').translate(str.maketrans('áéíóú', 'aeiou'))
                m += f'<li><a href="{slug}_1.html">{c}</a></li>'
            m += f'<li><a href="{CONFIG["INSTA"]}" target="_blank"><i class="fa fa-instagram"></i></a></li></ul></nav></div>'
            html = html.replace('{{MENU_AREA}}', m)
        html = html.replace('images/logo.png', 'images/logo.png' if is_index else 'images/logo_lunadeplata.svg')
        html = html.replace('Free Multipurpose Responsive', 'Elegancia que Perdura').replace('Landing Page 2019', 'Joyas de Plata para momentos inolvidables')
        html = html.replace('Call Now', 'WhatsApp').replace('(+1)1234567890', f'+{CONFIG["PHONE"]}')
        html = html.replace('© 2019 All Rights Reserved.', '© 2026 Lunadeplata')
        return html

    def publish_github(self):
        print("🚀 Sincronizando con GitHub...")
        os.chdir(PATHS["PUBLIC"])
        
        # Crear .gitignore para evitar que Cloudflare intente subir archivos pesados de Git
        with open(".gitignore", "w") as f:
            f.write(".git/\n")
            
        try:
            if not os.path.exists(".git"):
                subprocess.run(["git", "init"], check=True)
                subprocess.run(["git", "remote", "add", "origin", CONFIG["GITHUB_REPO"]], check=True)
                subprocess.run(["git", "branch", "-M", "main"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Sincronización automática Lunadeplata"], capture_output=True)
            subprocess.run(["git", "push", "origin", "main", "--force"], check=True)
            print("✅ Catálogo publicado en GitHub con éxito.")
        except Exception as e: print(f"❌ Error Git: {e}")

    def generate(self):
        if not os.path.exists(PATHS["PUBLIC"]): os.makedirs(PATHS["PUBLIC"])
        # No borrar .git si existe
        for item in os.listdir(PATHS["PUBLIC"]):
            if item != ".git":
                path = os.path.join(PATHS["PUBLIC"], item)
                if os.path.isdir(path): shutil.rmtree(path)
                else: os.remove(path)
        os.makedirs(PATHS["IMAGES"])
        for f in ['css', 'js', 'fonts']:
            src = os.path.join(PATHS["TEMPLATE"], f)
            if os.path.exists(src): shutil.copytree(src, os.path.join(PATHS["PUBLIC"], f))
        for l in ["logo_lunadeplata.svg", "logo.png"]:
            p = os.path.join(PATHS["BASE"], l)
            if os.path.exists(p): shutil.copy(p, os.path.join(PATHS["IMAGES"], l))

        self.connect_odoo()
        prods = self.get_products()
        self.categories = set(p['smart_cat'] for p in prods)

        # INDEX
        idx_html = self.build_base(is_index=True)
        idx_cont = '<div class="titlepage"><h2>Nuestras Colecciones</h2><div class="row">'
        for c in sorted(list(self.categories)):
            slug = c.lower().replace(' ', '_').translate(str.maketrans('áéíóú', 'aeiou'))
            idx_cont += f'<div class="col-md-4 mb-4"><a href="{slug}_1.html" style="text-decoration:none;"><div class="product-card" style="padding:40px; text-align:center;"><h3 style="color:#d4af37; font-weight:bold;">{c}</h3><span class="btn btn-outline-warning btn-sm">Explorar</span></div></a></div>'
        idx_cont += '</div></div>'
        idx_html = re.sub(r'<div id="jewellery" class="Best">.*?<!-- end Best -->', f'<div class="Best"><div class="container">{idx_cont}</div></div></div>', idx_html, flags=re.DOTALL)
        idx_html = idx_html.replace('<h1>Jewellery</h1>', '<h1>Lunadeplata</h1>').replace('Contact Us', 'Ver Catálogo')
        with open(os.path.join(PATHS["PUBLIC"], "index.html"), "w") as f: f.write(idx_html)

        # CATEGORÍAS
        for c in self.categories:
            c_prods = sorted([p for p in prods if p['smart_cat'] == c], key=lambda x: x['name'])
            slug = c.lower().replace(' ', '_').translate(str.maketrans('áéíóú', 'aeiou'))
            total = (len(c_prods) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            for n in range(1, total + 1):
                page_html = self.build_base()
                sort_ui = '<div class="sort-bar-boutique"><span>Ordenar precio:</span><button class="btn-sort" onclick="sortPage(\'asc\', this)">↑ Menor</button><button class="btn-sort" onclick="sortPage(\'desc\', this)">↓ Mayor</button></div>'
                grid = f'<div class="titlepage"><h2>{c}</h2>{sort_ui}<div class="row" id="p-grid">'
                for p in c_prods[(n-1)*ITEMS_PER_PAGE : n*ITEMS_PER_PAGE]:
                    mimg = self.save_img(p['image_1920'], "m", p['id'])
                    grid += f'<div class="col-md-4 mb-4 p-item" data-price="{p["list_price"]}"><div class="product-card"><a href="product_{p["id"]}.html"><img src="images/{mimg}" loading="lazy"></a><div class="p-3 text-center"><h5>{p["name"]}</h5><p class="product-price">{self.format_money(p["list_price"])}</p><a href="product_{p["id"]}.html" class="btn btn-outline-dark btn-sm">Ver Detalles</a></div></div></div>'
                grid += '</div>'
                if total > 1:
                    grid += '<div class="pagination-container"><div class="pagination-nav">'
                    for pl in range(1, total + 1): grid += f'<a href="{slug}_{pl}.html" {"class=\'active\'" if pl==n else ""}>{pl}</a>'
                    grid += '</div></div>'
                page_html = re.sub(r'<div id="jewellery" class="Best">.*?<!-- end Best -->', f'<div class="Best"><div class="container">{grid}</div></div></div>', page_html, flags=re.DOTALL)
                page_html = re.sub(r'<section class="slider_section">.*?</section>', '', page_html, flags=re.DOTALL)
                page_html = page_html.replace('</body>', """<script>
                function sortPage(o, btn){
                    const g=document.getElementById('p-grid'), i=Array.from(g.getElementsByClassName('p-item'));
                    document.querySelectorAll('.btn-sort').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    i.sort((a,b)=> {
                        const pa=parseFloat(a.dataset.price), pb=parseFloat(b.dataset.price);
                        return o==='asc'?pa-pb:pb-pa;
                    }).forEach(el=>g.appendChild(el));
                }</script></body>""")
                with open(os.path.join(PATHS["PUBLIC"], f"{slug}_{n}.html"), "w") as f: f.write(page_html)

        # DETALLES
        for p in prods:
            det_html = self.build_base()
            mimg = self.save_img(p['image_1920'], "m", p['id'])
            wa = urllib.parse.quote(f"Hola Lunadeplata! Me interesa: {p['name']} (SKU: {p['default_code'] or 'S/R'})")
            gal = f'<div class="zoom-img-container" id="zbox"><img src="images/{mimg}" id="mview" style="transition: opacity 0.2s;"></div><div class="thumb-gallery d-flex mt-3 gap-2 flex-wrap">'
            gal += f'<img src="images/{mimg}" class="active" onclick="chg(this)">'
            for i, b in enumerate(p['extra_images'][:3]):
                ex = self.save_img(b, "e", p['id'], i)
                gal += f'<img src="images/{ex}" onclick="chg(this)">'
            gal += '</div>'
            cont = f'''<div class="container mt-5 mb-5"><div class="row">
                <div class="col-md-6 mb-4">{gal}</div>
                <div class="col-md-6">
                    <h2 style="font-weight:bold; color:#333;">{p['name']}</h2><hr>
                    <div style="background:rgba(212, 175, 55, 0.03); padding:20px; border-radius:10px; border:1px solid #f9eecd; margin-bottom:20px;">
                        <p><b>Referencia:</b> {p['default_code'] or "S/R"}</p><p>{"<br>".join(p['props'])}</p>
                    </div>
                    <h3 class="product-price" style="font-size:36px; margin:20px 0;">{self.format_money(p['list_price'])}</h3>
                    <a href="https://wa.me/{CONFIG["PHONE"]}?text={wa}" target="_blank" class="btn-wa"><i class="fa fa-whatsapp"></i> Consultar Disponibilidad</a>
                    <div class="mt-4" style="line-height:1.6; color:#555;">{p['website_description'] or ""}</div>
                </div>
            </div></div>'''
            det_html = re.sub(r'<div id="jewellery" class="Best">.*?<!-- end Best -->', f'<div class="Best">{cont}</div>', det_html, flags=re.DOTALL)
            det_html = re.sub(r'<section class="slider_section">.*?</section>', '', det_html, flags=re.DOTALL)
            det_html = det_html.replace('</body>', """<script>
            function chg(el){ 
                const m = document.getElementById('mview'); m.style.opacity = '0';
                setTimeout(() => { m.src = el.src; m.style.opacity = '1'; }, 150);
                document.querySelectorAll('.thumb-gallery img').forEach(i=>i.classList.remove('active'));
                el.classList.add('active');
            }
            document.getElementById('zbox').onmousemove=(e)=>{
                const i=document.getElementById('mview'), b=e.currentTarget;
                i.style.transformOrigin=`${(e.offsetX/b.offsetWidth)*100}% ${(e.offsetY/b.offsetHeight)*100}%`;
                i.style.transform="scale(1.6)";
            };
            document.getElementById('zbox').onmouseleave=()=>{ document.getElementById('mview').style.transform="scale(1)"; };
            </script></body>""")
            with open(os.path.join(PATHS["PUBLIC"], f"product_{p['id']}.html"), "w") as f: f.write(det_html)
        
        self.publish_github()

if __name__ == "__main__":
    gen = CatalogGenerator()
    gen.generate()
