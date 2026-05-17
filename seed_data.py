"""
seed_data.py — Inicialización de base de datos para Garage Abierto
Crea tablas, usuario admin, categorías, proveedores, productos, clientes y empleados.
"""
import os
import sys
from datetime import date, datetime, timezone, timedelta
import random

os.environ.setdefault('FLASK_APP', 'run.py')

from run import app
from app import db
from app.models.user import User
from app.models.product import Product, Category
from app.models.supplier import Supplier
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.sale import Sale, SaleItem

with app.app_context():
    db.create_all()
    print("✅ Tablas creadas / verificadas.")

    # ── USERS ──────────────────────────────────────────────
    if not User.query.filter_by(email='admin@garageabierto.com').first():
        admin = User(name='Administrador', email='admin@garageabierto.com', role='admin')
        admin.set_password('Admin123!')
        db.session.add(admin)
        print("✅ Admin creado: admin@garageabierto.com / Admin123!")
    else:
        admin = User.query.filter_by(email='admin@garageabierto.com').first()

    if not User.query.filter_by(email='ana@garageabierto.com').first():
        seller1 = User(name='Ana García', email='ana@garageabierto.com', role='seller')
        seller1.set_password('Vendedor123!')
        db.session.add(seller1)
        print("✅ Vendedora creada: ana@garageabierto.com / Vendedor123!")

    if not User.query.filter_by(email='luis@garageabierto.com').first():
        seller2 = User(name='Luis Torres', email='luis@garageabierto.com', role='seller')
        seller2.set_password('Vendedor123!')
        db.session.add(seller2)

    db.session.commit()

    # ── CATEGORIES ──────────────────────────────────────────
    cats_data = [
        ('Sanitarios',       'bi-toilet',               '#2196F3'),
        ('Grifería',         'bi-droplet-half',          '#00BCD4'),
        ('Bañeras y Piletas','bi-water',                '#3F51B5'),
        ('Accesorios',       'bi-tools',                '#9C27B0'),
        ('Mamparas y Duchas','bi-house-door',           '#009688'),
        ('Muebles de Baño',  'bi-layout-sidebar-reverse','#FF9800'),
        ('Calefacción',      'bi-thermometer-half',     '#F44336'),
        ('Revestimientos',   'bi-grid-3x3',             '#795548'),
    ]
    cats = {}
    for name, icon, color in cats_data:
        cat = Category.query.filter_by(name=name).first()
        if not cat:
            cat = Category(name=name, icon=icon, color=color)
            db.session.add(cat)
            db.session.flush()
        cats[name] = cat

    db.session.commit()
    print(f"✅ {len(cats)} categorías creadas.")

    # ── SUPPLIERS ────────────────────────────────────────────
    suppliers_data = [
        ('Cerámicas del Sur S.A.',   'Marcos Ibáñez',   '011-4523-8800', 'ventas@ceramicasdelsur.com.ar',  'Av. Belgrano 2350, CABA',        '30-71234567-8'),
        ('AquaFlow Importaciones',   'Silvia Romero',   '011-4112-5500', 'info@aquaflow.com.ar',            'Tucumán 890, Rosario',            '30-68765432-1'),
        ('BathLux Argentina',        'Jorge Pereyra',   '011-4788-3300', 'contacto@bathlux.com.ar',         'Calle 13 Nro. 450, La Plata',    '30-62345678-9'),
        ('Termo Hogar S.A.',         'Patricia Suárez',  '011-4399-7700', 'ventas@termohogar.com.ar',        'Corrientes 5500, CABA',           '30-59876543-2'),
        ('Revest Pro',               'Daniel Castro',   '011-4612-1200', 'daniel@revestpro.com.ar',         'San Martín 1200, Quilmes',        '20-34567890-3'),
        ('Import & Bath SRL',        'Claudia Rivas',   '011-4234-9900', 'importbath@gmail.com',            'Av. Rivadavia 8800, CABA',        '30-75432198-4'),
    ]
    supps = {}
    for name, contact, phone, email, address, cuit in suppliers_data:
        s = Supplier.query.filter_by(name=name).first()
        if not s:
            s = Supplier(name=name, contact_name=contact, phone=phone,
                         email=email, address=address, cuit=cuit)
            db.session.add(s)
            db.session.flush()
        supps[name] = s

    db.session.commit()
    print(f"✅ {len(supps)} proveedores creados.")

    # ── PRODUCTS ─────────────────────────────────────────────
    products_data = [
        # SKU, Name, Brand, Desc, Category, Supplier, Price, Cost, Stock, MinStock, Featured
        # SANITARIOS
        ('SAN001','Inodoro Largura White Line Blanco','Roca',
         'Inodoro de porcelana blanca de alta resistencia, doble descarga 3/6L, salida horizontal.',
         'Sanitarios','Cerámicas del Sur S.A.',85000,54000,15,5,True),
        ('SAN002','Inodoro Suspendido Meridian Rimless','Grohe',
         'Inodoro suspendido sin reborde para máxima higiene, incluye asiento soft-close.',
         'Sanitarios','Import & Bath SRL',185000,118000,6,3,True),
        ('SAN003','Bidet Giralda Blanco','Ferrum',
         'Bidet de línea clásica, porcelana sanitaria blanca, con tapa incluida.',
         'Sanitarios','Cerámicas del Sur S.A.',45000,28500,12,4,False),
        ('SAN004','Bidet Suspendido Soft Close','Roca',
         'Bidet suspendido con asiento de cierre suave, porcelana premium.',
         'Sanitarios','Cerámicas del Sur S.A.',98000,62000,5,3,False),
        ('SAN005','Inodoro Plus Doble Descarga + Mochila','Ferrum',
         'Inodoro de piso con mochila baja, descarga dual 3/6L, estilo moderno.',
         'Sanitarios','Cerámicas del Sur S.A.',72000,46000,18,6,False),
        ('SAN006','Mingitorio Mural Compact','Roca',
         'Mingitorio de pared para locales comerciales, porcelana blanca brillante.',
         'Sanitarios','Cerámicas del Sur S.A.',65000,41000,4,2,False),
        ('SAN007','Conjunto Inodoro + Bidet Rimless Premium','Roca',
         'Kit completo inodoro y bidet de línea premium con salida horizontal, tapa incluida.',
         'Sanitarios','Cerámicas del Sur S.A.',215000,136000,7,3,True),
        ('SAN008','Inodoro Compacto City Blanco','Ferrum',
         'Inodoro de tamaño compacto ideal para baños pequeños, eficiencia hídrica.',
         'Sanitarios','Cerámicas del Sur S.A.',62000,39000,10,4,False),
        # GRIFERÍA
        ('GRI001','Monocomando Mesada Alba Cromado','FV',
         'Monocomando de mesada con aireador incorporado, manija larga, cuerpo bronce.',
         'Grifería','AquaFlow Importaciones',28000,16800,25,8,False),
        ('GRI002','Ducha Teléfono Cromada con Flexible','FV',
         'Conjunto ducha teléfono + flexible 1.5m, conexión 1/2", acabado cromado.',
         'Grifería','AquaFlow Importaciones',15000,9000,30,10,False),
        ('GRI003','Canilla Bidet Flexible Cromada','FV',
         'Canilla de bidet con flexible de acero, cuello de cisne corto, cuerpo bronce.',
         'Grifería','AquaFlow Importaciones',12000,7200,40,12,False),
        ('GRI004','Monocomando Ducha Empotrado Exact','Grohe',
         'Monocomando ducha a empotrar con cartucho cerámico, apto para caudal variable.',
         'Grifería','AquaFlow Importaciones',58000,36000,10,4,True),
        ('GRI005','Set Ducha Rain 300mm Lluvia','Grohe',
         'Cabezal lluvia 300mm + brazo de techo + flexible + ducha manual. Kit completo.',
         'Grifería','Import & Bath SRL',98000,62000,7,3,True),
        ('GRI006','Canilla Pared Clásica Bimetal','FV',
         'Canilla de pared para bañera o pileta, bimetal cromado, doble comando.',
         'Grifería','AquaFlow Importaciones',24000,14400,20,6,False),
        ('GRI007','Termostato Ducha Grotherm 800','Grohe',
         'Grifo termostático de ducha con control de temperatura y caudal independientes.',
         'Grifería','Import & Bath SRL',128000,82000,4,2,True),
        ('GRI008','Columna Ducha Completa Freedom','Hansgrohe',
         'Columna ducha con panel LED, 3 funciones, cabezal lluvia + ducha lateral + teléfono.',
         'Grifería','Import & Bath SRL',195000,124000,3,2,True),
        ('GRI009','Monocomando Pileta Cuello de Cisne Alto','FV',
         'Monocomando de alto diseño con cuello de cisne, ideal para bachas sobre-encimera.',
         'Grifería','AquaFlow Importaciones',34000,20400,16,5,False),
        ('GRI010','Set Grifería Baño 4 Piezas Completo','FV',
         'Kit monocomando mesada + ducha + canilla bidet + accesorio. Diseño uniforme.',
         'Grifería','AquaFlow Importaciones',72000,45000,9,3,False),
        # BAÑERAS Y PILETAS
        ('BAU001','Bañera Acrílica Estándar 160x70 Blanca','Permatex',
         'Bañera de acrílico sanitario reforzado con fibra de vidrio, incluye desagüe.',
         'Bañeras y Piletas','Import & Bath SRL',188000,118000,5,2,True),
        ('BAU002','Bañera Hidromasaje Turbo 170x80 Blanca','Aquaspa',
         'Hidromasaje con 8 jets de agua + 6 de aire, iluminación LED, control digital.',
         'Bañeras y Piletas','Import & Bath SRL',498000,318000,2,1,True),
        ('BAU003','Bacha Sobrepuesta Redonda 40cm Blanca','Roca',
         'Bacha de porcelana sobre encimera, diseño moderno, diámetro 40cm.',
         'Bañeras y Piletas','Cerámicas del Sur S.A.',56000,35000,12,4,True),
        ('BAU004','Bacha Empotrada Rectangular 60x40','Roca',
         'Bacha a empotrar en mesada, porcelana blanca, con desbordadero y tapa metálica.',
         'Bañeras y Piletas','Cerámicas del Sur S.A.',38000,24000,16,5,False),
        ('BAU005','Pedestal con Bacha 50cm Blanco','Ferrum',
         'Conjunto pedestal + bacha de porcelana 50cm, incluye grifería monocomando.',
         'Bañeras y Piletas','Cerámicas del Sur S.A.',75000,47000,8,3,False),
        ('BAU006','Bañera Exenta Oval Freestanding Premium','Aquaspa',
         'Bañera independiente diseño ovalado, acrílico de 10mm, patas doradas incluidas.',
         'Bañeras y Piletas','Import & Bath SRL',825000,525000,1,1,True),
        ('BAU007','Bacha Rectangular Doble Pozo 80x45','Roca',
         'Bacha de doble pozo a empotrar, ideal para vanitorios de 80cm o más.',
         'Bañeras y Piletas','Cerámicas del Sur S.A.',68000,43000,7,3,False),
        ('BAU008','Sobre Mesada Cemento Pátina 60cm','Urban Bath',
         'Sobre mesada artesanal de microcemento pátina gris, resistente al agua.',
         'Bañeras y Piletas','BathLux Argentina',128000,82000,4,2,True),
        # ACCESORIOS
        ('ACC001','Espejo Baño Biselado 60x80 sin Marco','BathStyle',
         'Espejo de vidrio biselado 5mm, sin marco, listo para colgar horizontal o vertical.',
         'Accesorios','Import & Bath SRL',38000,22000,20,6,False),
        ('ACC002','Espejo con Luz LED 80x60 Antivaho','TouchLux',
         'Espejo retroiluminado LED, función antivaho, touch dimmer, temperatura regulable.',
         'Accesorios','Import & Bath SRL',88000,55000,9,3,True),
        ('ACC003','Toallero Doble Barra Inox 60cm','BathStyle',
         'Toallero de doble barra en acero inoxidable 304, soporte mural, acabado cepillado.',
         'Accesorios','AquaFlow Importaciones',19000,11500,28,8,False),
        ('ACC004','Portarrollo Papel Higiénico Inox Negro','BathStyle',
         'Portarrollo de pared en acero inoxidable con acabado negro mate, fijación mural.',
         'Accesorios','AquaFlow Importaciones',9000,5400,45,15,False),
        ('ACC005','Jabonera Cristal Templado Empotrada','BathStyle',
         'Jabonera a empotrar en azulejo, cristal templado 8mm, bordes cromados.',
         'Accesorios','AquaFlow Importaciones',12500,7500,32,10,False),
        ('ACC006','Set Accesorios 6 Piezas Negro Mate Premium','Grohe',
         'Juego completo: toallero, portarrollo, jabonera, ganchos x2, portarrollos repuesto.',
         'Accesorios','Import & Bath SRL',68000,43000,13,4,True),
        ('ACC007','Botiquín con Espejo Doble Puerta 60x70','BathStyle',
         'Botiquín espejado de empotrar, doble puerta, 3 estantes interiores ajustables.',
         'Accesorios','BathLux Argentina',58000,37000,10,3,False),
        ('ACC008','Set Ganchos Adhesivos Inox x4','BathStyle',
         'Juego de 4 ganchos de acero inoxidable con adhesivo industrial, sin perforación.',
         'Accesorios','AquaFlow Importaciones',10000,6000,48,15,False),
        ('ACC009','Repisa Vidrio Templado 60cm Cromada','BathStyle',
         'Repisa de vidrio templado 8mm con soportes cromados, carga máxima 15kg.',
         'Accesorios','AquaFlow Importaciones',26000,15600,16,5,False),
        ('ACC010','Dispensador Jabón Líquido Pared Inox','BathStyle',
         'Dispensador mural de 300ml en acero inoxidable, recarga fácil por la parte superior.',
         'Accesorios','AquaFlow Importaciones',18500,11000,24,8,False),
        # MAMPARAS Y DUCHAS
        ('MAM001','Mampara Vidrio Templado 8mm 70x195','BathLux',
         'Mampara fija de vidrio templado 8mm transparente, perfil de aluminio anodizado.',
         'Mamparas y Duchas','BathLux Argentina',128000,81000,7,3,False),
        ('MAM002','Mampara Abatible 90x200 Vidrio Esmerilado','BathLux',
         'Mampara batiente 90x200 en vidrio esmerilado, bisagras de latón cromado.',
         'Mamparas y Duchas','BathLux Argentina',158000,100000,5,2,True),
        ('MAM003','Cabina Ducha Angular 90x90 Completa','Aquaspa',
         'Cabina integral angular con techo, 2 puertas corredizas, base incluida.',
         'Mamparas y Duchas','Import & Bath SRL',295000,188000,2,1,True),
        ('MAM004','Plato Ducha Acrílico 90x90 Blanco','Permatex',
         'Plato de ducha en acrílico reforzado, antideslizante, desagüe central.',
         'Mamparas y Duchas','Import & Bath SRL',56000,35000,11,4,False),
        ('MAM005','Plato Ducha Extra Plano 80x80 5cm','Permatex',
         'Plato ultra-plano 5cm de altura, acabado pizarra antideslizante, desagüe lineal.',
         'Mamparas y Duchas','Import & Bath SRL',78000,49000,7,3,False),
        ('MAM006','Mampara Corrediza Doble 120x200','BathLux',
         'Mampara de 2 puertas corredizas, riel inferior + superior, vidrio templado 6mm.',
         'Mamparas y Duchas','BathLux Argentina',198000,126000,4,2,True),
        ('MAM007','Canal Desagüe Lineal Inox 80cm','DrainPro',
         'Canal de desagüe lineal en acero inoxidable, tapa perforada, sifón incluido.',
         'Mamparas y Duchas','AquaFlow Importaciones',34000,20400,14,5,False),
        ('MAM008','Cabezal Techo Lluvia Empotrado 30x30','Hansgrohe',
         'Cabezal de techo a empotrar 30x30cm, función lluvia, acero inoxidable.',
         'Mamparas y Duchas','Import & Bath SRL',48000,30000,9,3,True),
        # MUEBLES DE BAÑO
        ('MUE001','Vanitory 60cm Blanco con Bacha Incluida','BathLux',
         'Vanitory suspenso 60cm con bacha oval integrada, cajón soft-close, MDF lacado.',
         'Muebles de Baño','BathLux Argentina',188000,120000,7,3,True),
        ('MUE002','Vanitory Flotante 80cm Roble Natural','BathLux',
         'Vanitory flotante doble cajón, enchapado roble natural, tirador de cuero.',
         'Muebles de Baño','BathLux Argentina',248000,158000,4,2,True),
        ('MUE003','Columna Baño 30x160cm Blanca','BathLux',
         'Columna alta de almacenamiento, 2 puertas + 1 cajón, bisagras silenciosas.',
         'Muebles de Baño','BathLux Argentina',98000,62000,5,2,False),
        ('MUE004','Mesada Porcelana Blanca 100x52','Roca',
         'Mesada de porcelana con cubeta integrada y desbordadero, para mueble de 100cm.',
         'Muebles de Baño','Cerámicas del Sur S.A.',128000,81000,6,2,False),
        ('MUE005','Botiquín Empotrado Espejo 40x70','BathLux',
         'Botiquín a empotrar con puerta espejada, luz LED interior, 3 estantes.',
         'Muebles de Baño','BathLux Argentina',58000,37000,9,3,False),
        ('MUE006','Mueble Bajo Mesada 120cm Gris Ceniza','BathLux',
         'Mueble de 120cm sin bacha, 4 cajones de cierre suave, estructura MDF hidrófugo.',
         'Muebles de Baño','BathLux Argentina',288000,184000,3,2,False),
        ('MUE007','Estante Flotante Madera 60cm','BathLux',
         'Repisa de madera natural tratada 60x20cm, soportes de acero, 20kg de carga.',
         'Muebles de Baño','BathLux Argentina',38000,24000,14,5,False),
        ('MUE008','Módulo Organizador Bajo Pileta','BathLux',
         'Módulo de 2 cajones organizadores para instalar bajo pileta de pedestal.',
         'Muebles de Baño','BathLux Argentina',46000,29000,11,4,False),
        # CALEFACCIÓN
        ('CAL001','Toallero Calefactor Recto 60x120 600W Cromo','Termo Hogar',
         'Toallero calefactor eléctrico, resistencia oculta, termostato, IP44.',
         'Calefacción','Termo Hogar S.A.',128000,81000,7,3,True),
        ('CAL002','Toallero Calefactor Curvo 50x100 Negro Mate','Termo Hogar',
         'Toallero de diseño curvo en negro mate, 450W, con interruptor de pared.',
         'Calefacción','Termo Hogar S.A.',158000,100000,4,2,True),
        ('CAL003','Panel Radiante Infrarrojo 800W Techo','Termo Hogar',
         'Panel de calefacción infrarroja para techo de baño, 800W, ultrafino 2cm.',
         'Calefacción','Termo Hogar S.A.',188000,120000,3,2,False),
        ('CAL004','Ventilador Calefactor Pared 2000W','Termo Hogar',
         'Calefactor de pared con ventilador, 2 velocidades, termostato regulable, IP21.',
         'Calefacción','Termo Hogar S.A.',78000,49000,9,4,False),
        ('CAL005','Kit Suelo Radiante Eléctrico 2m²','Termo Hogar',
         'Manta calefactora para bajo porcellanato, 200W/m², termostato programable incluido.',
         'Calefacción','Termo Hogar S.A.',98000,62000,5,2,True),
        ('CAL006','Termostato Digital Programable WiFi','Termo Hogar',
         'Termostato inteligente con control por app, pantalla táctil, 7 programas semanales.',
         'Calefacción','Termo Hogar S.A.',36000,22000,14,5,False),
        # REVESTIMIENTOS
        ('REV001','Azulejo Subway Blanco Biselado 7.5x15 (caja 1m²)','CeráArt',
         'Azulejo de estilo metro biselado, blanco brillante, ideal para baños vintage/moderno.',
         'Revestimientos','Revest Pro',16000,9600,75,20,False),
        ('REV002','Porcellanato Cemento Gris 60x60 (caja 1.44m²)','PorcelAr',
         'Porcellanato rectificado imitación cemento, gris medio, antideslizante clase 3.',
         'Revestimientos','Revest Pro',33000,19800,42,12,False),
        ('REV003','Porcellanato Mármol Blanco Calacatta 60x120','PorcelAr',
         'Porcellanato gran formato imitación mármol Calacatta, pulido brillante, rectificado.',
         'Revestimientos','Revest Pro',56000,33600,28,8,True),
        ('REV004','Mosaico Vítreo 30x30 Azul Mar (caja)','MosaicArt',
         'Mosaico de vidrio azul marino brillante, teselados de 2.5cm, ideal en duchas.',
         'Revestimientos','Revest Pro',29000,17400,22,6,False),
        ('REV005','Cenefa Decorativa Geométrica 8x60','CeráArt',
         'Cenefa decorativa para separar zonas, motivos geométricos, compatible con subway.',
         'Revestimientos','Revest Pro',12500,7500,58,15,False),
        ('REV006','Porcellanato Negro Absoluto Mate 60x60','PorcelAr',
         'Porcellanato negro mate antireflejo, rectificado, apto piso/pared, resistencia alta.',
         'Revestimientos','Revest Pro',39000,23400,33,10,False),
        ('REV007','Porcellanato Madera Natural Roble 20x120','PorcelAr',
         'Imitación madera roble, aspecto táctil, ideal para duchas tipo spa.',
         'Revestimientos','Revest Pro',46000,27600,26,8,True),
        ('REV008','Azulejo Decorativo Floral 20x20 (caja)','CeráArt',
         'Azulejo artesanal con motivos florales, ideal como paño decorativo en baños.',
         'Revestimientos','Revest Pro',23000,13800,18,5,False),
    ]

    products_map = {}
    created_count = 0
    for row in products_data:
        sku, name, brand, desc, cat_name, sup_name, price, cost, stock, min_stock, featured = row
        if Product.query.filter_by(sku=sku).first():
            p = Product.query.filter_by(sku=sku).first()
        else:
            p = Product(
                sku=sku,
                name=name,
                brand=brand,
                description=desc,
                category_id=cats[cat_name].id,
                supplier_id=supps[sup_name].id,
                price=price,
                cost_price=cost,
                stock=stock,
                min_stock=min_stock,
                featured=featured,
            )
            db.session.add(p)
            created_count += 1
        products_map[sku] = p

    db.session.commit()
    print(f"✅ {created_count} productos creados ({len(products_data)} total).")

    # ── CUSTOMERS ────────────────────────────────────────────
    customers_data = [
        ('Constructora Horizonte S.A.',    '011-4523-6600', 'compras@horizonteconst.com.ar',  'Av. Corrientes 4500, CABA',       '30-72345678-5'),
        ('Arq. María González',            '15-3344-8899',  'mgonzalez.arq@gmail.com',        'Av. Santa Fe 2200, CABA',         '20-28765432-4'),
        ('Reformas Norte SRL',             '011-4788-1122', 'ventas@reformasnorte.com.ar',    'Pueyrredón 880, Palermo',         '30-69876543-1'),
        ('Carlos Pérez',                   '15-5544-3322',  'carlosperez22@hotmail.com',      'Rivadavia 5600, Flores',          '20-25678901-6'),
        ('Hotel Boutique Palermo',         '011-4831-9900', 'mantenimiento@hotelboutique.com', 'Thames 2100, Palermo Soho',       '30-71256789-0'),
        ('Obra Social Municipal',          '011-4300-5500', 'infraestructura@obrasocia.gob.ar','Brasil 330, San Telmo',           '30-59012345-7'),
        ('Estudio Diseño Interior DG',     '15-6677-8890',  'proyectos@estudiodg.com',        'Honduras 5530, Palermo',          '20-35678901-3'),
        ('Martina López',                  '15-2233-4455',  'martinalopez@gmail.com',         'Nazca 1200, Caballito',           '20-31234567-2'),
        ('Constructora Del Plata',         '011-4612-3344', 'presupuestos@delplata.com',      'Av. Directorio 2800, CABA',       '30-68901234-9'),
        ('Colegio San Martín',             '011-4781-5678', 'administracion@colegiosm.edu.ar','Cabildo 1500, Belgrano',          '30-55678901-8'),
    ]
    for name, phone, email, address, cuit in customers_data:
        if not Customer.query.filter_by(email=email).first():
            c = Customer(name=name, phone=phone, email=email, address=address, cuit_dni=cuit)
            db.session.add(c)

    db.session.commit()
    print(f"✅ Clientes creados.")

    # ── EMPLOYEES ────────────────────────────────────────────
    employees_data = [
        ('Roberto Sánchez',   'Gerente General',       450000, '15-3300-1122', 'rsanchez@garageabierto.com', '28345678', date(2019, 3, 15)),
        ('Ana García',        'Vendedora Senior',       285000, '15-4411-2233', 'ana@garageabierto.com',       '31234567', date(2020, 6, 1)),
        ('Luis Torres',       'Vendedor',               268000, '15-5522-3344', 'luis@garageabierto.com',      '33456789', date(2021, 2, 14)),
        ('Patricia Ruiz',     'Encargada de Depósito',  238000, '15-6633-4455', 'pruiz@garageabierto.com',     '26789012', date(2020, 9, 20)),
        ('Diego Morales',     'Administrativo Contable',298000, '15-7744-5566', 'dmorales@garageabierto.com',  '30123456', date(2022, 1, 3)),
    ]
    for name, position, salary, phone, email, dni, hire_date in employees_data:
        if not Employee.query.filter_by(email=email).first():
            e = Employee(name=name, position=position, salary=salary, phone=phone,
                         email=email, dni=dni, hire_date=hire_date)
            db.session.add(e)

    db.session.commit()
    print(f"✅ Empleados creados.")

    # ── SAMPLE SALES ─────────────────────────────────────────
    if Sale.query.count() == 0:
        users = User.query.all()
        customers = Customer.query.all()
        all_products = Product.query.filter(Product.stock > 0).all()
        payment_methods = ['efectivo', 'tarjeta', 'transferencia', 'efectivo', 'efectivo']

        random.seed(42)
        sales_created = 0
        for i in range(30):
            days_ago = random.randint(0, 89)
            sale_date = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(8, 19))
            seller = random.choice(users)
            customer = random.choice(customers) if random.random() > 0.35 else None
            payment = random.choice(payment_methods)
            discount = random.choice([0, 0, 0, 5, 10])

            num_items = random.randint(1, 4)
            selected = random.sample(all_products, min(num_items, len(all_products)))

            subtotal = 0.0
            items = []
            for prod in selected:
                qty = random.randint(1, 3)
                unit_price = float(prod.price)
                sub = unit_price * qty
                subtotal += sub
                items.append((prod, qty, unit_price, sub))

            total = subtotal * (1 - discount / 100)

            sale = Sale(
                customer_id=customer.id if customer else None,
                user_id=seller.id,
                subtotal=round(subtotal, 2),
                discount=discount,
                total=round(total, 2),
                payment_method=payment,
                status='completed',
                created_at=sale_date,
            )
            db.session.add(sale)
            db.session.flush()

            for prod, qty, unit_price, sub in items:
                si = SaleItem(
                    sale_id=sale.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=unit_price,
                    subtotal=round(sub, 2),
                )
                db.session.add(si)

            sales_created += 1

        db.session.commit()
        print(f"✅ {sales_created} ventas de ejemplo creadas.")
    else:
        print("ℹ️  Ya existen ventas, omitiendo seed de ventas.")

    print("\n🎉 Base de datos inicializada correctamente.")
    print("━" * 50)
    print("  Admin:     admin@garageabierto.com / Admin123!")
    print("  Vendedora: ana@garageabierto.com / Vendedor123!")
    print("  Vendedor:  luis@garageabierto.com / Vendedor123!")
    print("━" * 50)
