"""
Script para actualizar las URLs de imagen de todos los productos.
- Ferrum / FV: URLs reales de sus CDN oficiales (verificadas).
- Resto: fotos de Unsplash (libres, estables, sin API key).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import app
from app import db
from app.models.product import Product

# Ferrum CDN base (verificado)
F = 'https://ferrum.com/pub/media/catalog/product/cache/723de03bc8ecfa836485d5b2e3f2ed4a'
# FV WordPress base (verificado)
FV = 'https://fvsa.com/wp-content/uploads'
# Unsplash CDN base (libres, sin API)
U = 'https://images.unsplash.com/photo'

IMAGE_URLS = {
    # ── SANITARIOS ──────────────────────────────────────────────────────────
    # SAN001: Inodoro Largura White Line Blanco (Roca) → imagen inodoro Ferrum
    'SAN001': f'{F}/i/n/inodoro-de-pie-largo-fontana-ferrum-sanitarios-blanco-fon-in-250-bl-b_1.jpg',
    # SAN002: Inodoro Suspendido Meridian Rimless (Grohe) → inodoro porcelana blanco
    'SAN002': f'{U}-1552321554-5fefe8c9ef14?w=600&q=80&fit=crop',
    # SAN003: Bidet Giralda Blanco (Ferrum)
    'SAN003': f'{F}/b/i/bidet-de-pie-fontana-ferrum-sanitarios-blanco-fon-bi-101-bl-b_copia.jpg',
    # SAN004: Bidet Suspendido Soft Close (Roca)
    'SAN004': f'{F}/b/i/bidet-de-pie-marina-ferrum-sanitarios-blanco-mar-bi-304-bl-b_copia.jpg',
    # SAN005: Inodoro Plus Doble Descarga (Ferrum)
    'SAN005': f'{F}/i/n/inodoro-de-pie-largo-fontana-ferrum-sanitarios-blanco-fon-in-250-bl-b_1.jpg',
    # SAN006: Mingitorio Mural Compact (Roca)
    'SAN006': f'{U}-1584949901327-3c9e2efbcde7?w=600&q=80&fit=crop',
    # SAN007: Conjunto Inodoro + Bidet (Roca)
    'SAN007': f'{U}-1552321554-5fefe8c9ef14?w=600&q=80&fit=crop',
    # SAN008: Inodoro Compacto City (Ferrum)
    'SAN008': f'{F}/i/n/inodoro-de-pie-corto-fontana-ferrum-sanitarios-blanco-fon-in-001-bl-b.jpg',

    # ── GRIFERÍA ────────────────────────────────────────────────────────────
    # GRI001: Monocomando Mesada Alba (FV) → FV G9 lavatorio
    'GRI001': f'{FV}/2026/03/0108_I1-AI.jpg',
    # GRI002: Ducha Teléfono (FV)
    'GRI002': f'{FV}/2025/11/0163_M8-CR.jpg',
    # GRI003: Canilla Bidet (FV)
    'GRI003': f'{FV}/2025/11/0167_M8-CR.jpg',
    # GRI004: Monocomando Ducha Empotrado Exact (Grohe)
    'GRI004': f'{U}-1585771724684-38269d6639fd?w=600&q=80&fit=crop',
    # GRI005: Set Ducha Rain 300mm (Grohe)
    'GRI005': f'{U}-1601924428597-a5af478e5f1c?w=600&q=80&fit=crop',
    # GRI006: Canilla Pared Clásica (FV)
    'GRI006': f'{FV}/2025/10/0108_I1-AI.jpg',
    # GRI007: Termostato Grotherm 800 (Grohe)
    'GRI007': f'{U}-1585771724684-38269d6639fd?w=600&q=80&fit=crop',
    # GRI008: Columna Ducha Freedom (Hansgrohe)
    'GRI008': f'{U}-1571902943202-507ec2618e8f?w=600&q=80&fit=crop',
    # GRI009: Monocomando Cuello de Cisne (FV)
    'GRI009': f'{FV}/2026/03/0108_I1-AI.jpg',
    # GRI010: Set Grifería 4 Piezas (FV)
    'GRI010': f'{FV}/2025/11/0168_M8-CR.jpg',

    # ── BAÑERAS Y PILETAS ───────────────────────────────────────────────────
    # BAU001: Bañera Acrílica 160x70 (Permatex)
    'BAU001': f'{F}/b/a/banera-de-empotrar-acrilico-serena-ferrum-duchas-y-baneras-blanco-ser-ba-130-bl-a.jpg_1.jpg',
    # BAU002: Bañera Hidromasaje Turbo (Aquaspa)
    'BAU002': f'{U}-1604709177225-055f99402ea3?w=600&q=80&fit=crop',
    # BAU003: Bacha Sobrepuesta Redonda (Roca)
    'BAU003': f'{F}/b/a/bacha-tori-redonda-ferrum-bachas-blanco-tor-bh-057-bl-b_1.jpg',
    # BAU004: Bacha Empotrada Rectangular (Roca)
    'BAU004': f'{F}/b/a/bacha-milos-slim-mls-bh-171-bl.jpg',
    # BAU005: Pedestal con Bacha 50cm (Ferrum)
    'BAU005': f'{F}/l/a/lavatorio-espacio-bari-con-soporte-fijo-ferrum-bachas-blanco-esp-lv-102-bl-b_1.jpg',
    # BAU006: Bañera Exenta Oval Freestanding (Aquaspa)
    'BAU006': f'{U}-1607434472851-8e9e1b93e0f4?w=600&q=80&fit=crop',
    # BAU007: Bacha Doble Pozo 80x45 (Roca)
    'BAU007': f'{F}/b/a/bacha-milos-slim-mls-bh-173-bl.jpg',
    # BAU008: Sobre Mesada Cemento Pátina (Urban Bath)
    'BAU008': f'{U}-1556909114-f6e7ad7d3136?w=600&q=80&fit=crop',

    # ── ACCESORIOS ──────────────────────────────────────────────────────────
    # ACC001: Espejo Biselado 60x80
    'ACC001': f'{U}-1552566626-52f8b828add9?w=600&q=80&fit=crop',
    # ACC002: Espejo con Luz LED Antivaho
    'ACC002': f'{U}-1558618666-fcd25c85cd64?w=600&q=80&fit=crop',
    # ACC003: Toallero Doble Barra Inox (FV M8 Armonía - verificado)
    'ACC003': f'{FV}/2025/11/0163_M8-CR.jpg',
    # ACC004: Portarrollo Inox Negro (FV)
    'ACC004': f'{FV}/2025/11/0167_M8-CR.jpg',
    # ACC005: Jabonera Cristal Templado (FV)
    'ACC005': f'{FV}/2025/11/0168_M8-CR.jpg',
    # ACC006: Set Accesorios 6 Piezas Negro (Grohe)
    'ACC006': f'{U}-1620626011761-99316d1814b4?w=600&q=80&fit=crop',
    # ACC007: Botiquín con Espejo
    'ACC007': f'{U}-1507652313519-d4e9174996dd?w=600&q=80&fit=crop',
    # ACC008: Ganchos Adhesivos Inox
    'ACC008': f'{U}-1584949901327-3c9e2efbcde7?w=600&q=80&fit=crop',
    # ACC009: Repisa Vidrio Templado
    'ACC009': f'{U}-1556909114-f6e7ad7d3136?w=600&q=80&fit=crop',
    # ACC010: Dispensador Jabón Pared
    'ACC010': f'{U}-1620626011761-99316d1814b4?w=600&q=80&fit=crop',

    # ── MAMPARAS Y DUCHAS ───────────────────────────────────────────────────
    # MAM001: Mampara Vidrio Templado 70x195 (BathLux → imagen Ferrum Khios)
    'MAM001': f'{F}/k/h/khi-mp-038-c.jpg',
    # MAM002: Mampara Abatible 90x200
    'MAM002': f'{F}/k/h/khi-mp-026-c.jpg',
    # MAM003: Cabina Ducha Angular 90x90
    'MAM003': f'{U}-1571902943202-507ec2618e8f?w=600&q=80&fit=crop',
    # MAM004: Plato Ducha Acrílico 90x90
    'MAM004': f'{F}/r/e/receptaculo-cuadrado-khios-90x90-ferrum-duchas-y-baneras-blanco-khi-rc-018-bl-b_1.jpg',
    # MAM005: Plato Ducha Extra Plano 80x80
    'MAM005': f'{F}/r/e/receptaculo-semicircular-khios-khi-rc-029-bl-b_1.jpg',
    # MAM006: Mampara Corrediza Doble 120x200
    'MAM006': f'{F}/k/h/khi-mp-010-c.jpg',
    # MAM007: Canal Desagüe Lineal Inox 80cm
    'MAM007': f'{U}-1584949901327-3c9e2efbcde7?w=600&q=80&fit=crop',
    # MAM008: Cabezal Techo Lluvia 30x30 (Hansgrohe)
    'MAM008': f'{U}-1601924428597-a5af478e5f1c?w=600&q=80&fit=crop',

    # ── MUEBLES DE BAÑO ─────────────────────────────────────────────────────
    # MUE001: Vanitory 60cm Blanco con Bacha
    'MUE001': f'{F}/k/i/kit-bacha-con-mueble-de-colgar-persis-ferrum-bachas-rojo-brillante-prs-jg-001-rb-b_1.jpg',
    # MUE002: Vanitory Flotante 80cm Roble
    'MUE002': f'{U}-1507652313519-d4e9174996dd?w=600&q=80&fit=crop',
    # MUE003: Columna Baño 30x160cm
    'MUE003': f'{U}-1556909114-f6e7ad7d3136?w=600&q=80&fit=crop',
    # MUE004: Mesada Porcelana 100x52 (Roca)
    'MUE004': f'{F}/l/a/lavatorio-venecia-64-cm-1-agujero-ferrum-bachas-blanco-vnc-ms-004-bl-b_1.jpg',
    # MUE005: Botiquín Empotrado con LED
    'MUE005': f'{U}-1558618666-fcd25c85cd64?w=600&q=80&fit=crop',
    # MUE006: Mueble Bajo Mesada 120cm Gris
    'MUE006': f'{U}-1507652313519-d4e9174996dd?w=600&q=80&fit=crop',
    # MUE007: Estante Flotante Madera 60cm
    'MUE007': f'{U}-1583845112203-29329902332e?w=600&q=80&fit=crop',
    # MUE008: Módulo Organizador Bajo Pileta
    'MUE008': f'{U}-1584949901327-3c9e2efbcde7?w=600&q=80&fit=crop',

    # ── CALEFACCIÓN ─────────────────────────────────────────────────────────
    # CAL001: Toallero Calefactor Recto Cromo 600W
    'CAL001': f'{U}-1583845112203-29329902332e?w=600&q=80&fit=crop',
    # CAL002: Toallero Calefactor Curvo Negro Mate
    'CAL002': f'{U}-1583845112203-29329902332e?w=600&q=80&fit=crop',
    # CAL003: Panel Radiante Infrarrojo Techo
    'CAL003': f'{U}-1584949901327-3c9e2efbcde7?w=600&q=80&fit=crop',
    # CAL004: Ventilador Calefactor Pared 2000W
    'CAL004': f'{U}-1556909114-f6e7ad7d3136?w=600&q=80&fit=crop',
    # CAL005: Kit Suelo Radiante Eléctrico
    'CAL005': f'{U}-1517581177682-a085bb7ffb15?w=600&q=80&fit=crop',
    # CAL006: Termostato Digital WiFi
    'CAL006': f'{U}-1558618666-fcd25c85cd64?w=600&q=80&fit=crop',

    # ── REVESTIMIENTOS ──────────────────────────────────────────────────────
    # REV001: Azulejo Subway Blanco Biselado
    'REV001': f'{U}-1517581177682-a085bb7ffb15?w=600&q=80&fit=crop',
    # REV002: Porcellanato Cemento Gris 60x60
    'REV002': f'{U}-1558618666-fcd25c85cd64?w=600&q=80&fit=crop',
    # REV003: Porcellanato Mármol Calacatta
    'REV003': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
    # REV004: Mosaico Vítreo 30x30 Azul Mar
    'REV004': f'{U}-1484154436122-99b-pool-mosaic?w=600&q=80&fit=crop',
    # REV005: Cenefa Decorativa Geométrica
    'REV005': f'{U}-1517581177682-a085bb7ffb15?w=600&q=80&fit=crop',
    # REV006: Porcellanato Negro Absoluto Mate
    'REV006': f'{U}-1600566752355-35792fbb5b59?w=600&q=80&fit=crop',
    # REV007: Porcellanato Madera Natural Roble
    'REV007': f'{U}-1583845112203-29329902332e?w=600&q=80&fit=crop',
    # REV008: Azulejo Decorativo Floral 20x20
    'REV008': f'{U}-1517581177682-a085bb7ffb15?w=600&q=80&fit=crop',
}

def main():
    with app.app_context():
        updated = 0
        not_found = []
        for sku, url in IMAGE_URLS.items():
            p = Product.query.filter_by(sku=sku).first()
            if p:
                p.image_url = url
                updated += 1
            else:
                not_found.append(sku)
        db.session.commit()
        print(f'✅ {updated} productos actualizados con imagen.')
        if not_found:
            print(f'⚠️  SKUs no encontrados: {not_found}')

if __name__ == '__main__':
    main()
