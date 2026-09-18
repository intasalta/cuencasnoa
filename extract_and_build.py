import os
import re
import json
import glob
import unicodedata
import pymupdf
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FIGURES_DIR = os.path.join(ASSETS_DIR, 'figures')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# Replacements to guarantee perfect Spanish text
REPLACEMENTS = [
    ('r\ufffdo', 'río'), ('R\ufffdo', 'Río'),
    ('h\ufffdricas', 'hídricas'), ('h\ufffdrico', 'hídrico'), ('h\ufffdricos', 'hídricos'),
    ('No\ufffd', 'Noé'),
    ('S\ufffdntesis', 'Síntesis'), ('s\ufffdntesis', 'síntesis'),
    ('Caracter\ufffdsticas', 'Características'), ('caracter\ufffdsticas', 'características'),
    ('morfol\ufffdgicas', 'morfológicas'), ('morfol\ufffdgica', 'morfológica'), ('morfolog\ufffda', 'morfología'),
    ('informaci\ufffdn', 'información'), ('direcci\ufffdn', 'dirección'), ('ubicaci\ufffdn', 'ubicación'),
    ('extensi\ufffdn', 'extensión'), ('regi\ufffdn', 'región'), ('inundaci\ufffdn', 'inundación'),
    ('clasificaci\ufffdn', 'clasificación'), ('elevaci\ufffdn', 'elevación'), ('vegetaci\ufffdn', 'vegetación'),
    ('formaci\ufffdn', 'formación'), ('evapotranspiraci\ufffdn', 'evapotranspiración'),
    ('precipitaci\ufffdn', 'precipitación'), ('poblaci\ufffdn', 'población'), ('rep\ufffdblica', 'república'),
    ('l\ufffdmite', 'límite'), ('l\ufffdmites', 'límites'),
    ('par\ufffdmetros', 'parámetros'), ('par\ufffdmetro', 'parámetro'),
    ('chaque\ufffda', 'chaqueña'), ('chaque\ufffdo', 'chaqueño'),
    ('Urue\ufffda', 'Urueña'), ('urue\ufffda', 'urueña'),
    ('Ica\ufffdo', 'Icaño'), ('ica\ufffdo', 'icaño'),
    ('Chu\ufffdas', 'Chuñas'), ('chu\ufffdas', 'chuñas'),
    ('monta\ufffda', 'montaña'), ('monta\ufffdas', 'montañas'),
    ('monta\ufffdosa', 'montañosa'), ('monta\ufffdoso', 'montañoso'),
    ('a\ufffdo', 'año'), ('a\ufffdos', 'años'),
    ('peque\ufffda', 'pequeña'), ('peque\ufffdo', 'pequeño'),
    ('Fiambal\ufffd', 'Fiambalá'), ('Hualf\ufffdn', 'Hualfín'),
    ('Bel\ufffdn', 'Belén'), ('Guanch\ufffdn', 'Guanchín'),
    ('Sal\ufffd', 'Salí'), ('m\ufffdx', 'máx'), ('m\ufffdn', 'mín'),
    ('m\ufffdximo', 'máximo'), ('m\ufffdnimo', 'mínimo'),
    ('per\ufffdmetro', 'perímetro'), ('\ufffdndice', 'índice'),
    ('funci\ufffdn', 'función'), ('aplicaci\ufffdn', 'aplicación'),
    ('aguas cal\ufffdentes', 'aguas calientes'),
    ('Chug-chug', 'Chuj-chuj'),
    ('\ufffd', '')
]

def clean_text(text):
    if not text:
        return ""
    for orig, rep in REPLACEMENTS:
        text = text.replace(orig, rep)
    return text

def clean_table_figure_refs(text):
    """Strips references to Cuadros and Figuras so the text reads like clean narrative prose"""
    if not text:
        return ""
    
    # Remove parenthetical references: (Cuadro 1), (Cuadro 1a), (Cuadros 1a y 1b), (Fig. 1), (Figura 2), etc.
    text = re.sub(r'\s*\([Cc]uadros?\s*[\d\w\s,y\-a-b]+\)', '', text)
    text = re.sub(r'\s*\([Ff]iguras?\s*[\d\w\s,y\-a-b]+\)', '', text)
    text = re.sub(r'\s*\([Ff]igs?\.?\s*[\d\w\s,y\-a-b]+\)', '', text)
    text = re.sub(r'\s*\(ver\s+[^)]+\)', '', text)
    
    # Remove sentences purely pointing to tables or figures
    text = re.sub(r'[^.]*?\b(?:se\s+muestra|se\s+observa|puede\s+observarse|se\s+presenta)\s+en\s+(?:el\s+)?(?:los\s+)?cuadros?\s+[\d\w\s,y\-a-b]+[^.]*\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'El\s+cuadro\s+[\d\w]+\s+y\s+la\s+figura\s+[\d\w]+\s+muestran[^.]*\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'En\s+los\s+cuadros\s+[\d\w\s,ya-b]+\s+se\s+muestran[^.]*\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'En\s+los\s+cuadros\s+[\d\w\s,ya-b]+\s+se\s+pueden\s+identificar[^.]*\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'En\s+el\s+cuadro\s+[\d\w\s,ya-b]+\s+se\s+presentan[^.]*\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCuadros?\s+[\d\w\s,y\-a-b]+\.?', '', text, flags=re.IGNORECASE)
    
    # Clean up double punctuation or awkward whitespace
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r'\s+\.', '.', text)
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_pdf_sintesis(pdf_path, is_macro=False):
    if not os.path.exists(pdf_path):
        return ""
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return ""

    narrative_paragraphs = []
    collecting = False
    
    for page_idx, page in enumerate(doc):
        text = clean_text(page.get_text())
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        page_stops = False
        current_para = []
        
        for line in lines:
            line_lower = line.lower()
            if 'sntesis descriptiva' in line_lower or 'síntesis descriptiva' in line_lower:
                collecting = True
                continue
            if not collecting:
                continue
                
            # Stop headings for subbasins or macros
            if is_macro:
                if line_lower.startswith(('cuadro 1:', 'cuadro 1 ', 'figura 1:')) or 'superficie y per' in line_lower:
                    page_stops = True
                    break
            else:
                if line_lower.startswith(('caractersticas morfolgicas', 'características morfológicas', 'estaciones de aforo', 'cuadro 1a:', 'cuadro 1:', 'cuadro 2a:')) or \
                   'c a u d a l e s   m e d i o s' in line_lower or 'c a u d a l e s  m e d i o s' in line_lower:
                    page_stops = True
                    break
                
            if any(h in line for h in ['EEA Salta', 'Paoli H', '2011 -', 'Salta, Argentina', 'Salta,  Argentina']):
                continue
            if line.startswith(('Cuenca ', 'Subcuenca ', 'Cuenca:')):
                continue
            if line.lower().startswith(('figura ', 'mapa ')) and len(line) < 100:
                continue
                
            current_para.append(line)
            
        if current_para:
            narrative_paragraphs.append(" ".join(current_para))
        if page_stops:
            break
            
    full = " ".join(narrative_paragraphs)
    full = clean_table_figure_refs(full)
    
    # If text is very long (> 2200 chars), synthesize by taking complete sentences up to ~1800 chars
    if len(full) > 2200:
        sentences = [s.strip() for s in re.split(r'(?<=\.)\s+', full) if len(s.strip()) > 15]
        selected = []
        cur_len = 0
        for s in sentences:
            if any(skip in s.lower() for skip in ['período 19', 'estación de aforo', 'aforados', 'derrames']):
                continue
            selected.append(s)
            cur_len += len(s)
            if cur_len > 1800:
                break
        full = " ".join(selected)

    if full and not full.endswith('.'):
        full += '.'

    return full

# Explicit 1-to-1 mapping for the 85 GeoJSON features
EXPLICIT_PDF_MAP = {
    0: '1_2_PIL_Sansai_yavi.pdf',
    1: '5_1_PUNA_Pozuelos.pdf',
    2: '1_1_PIL_Grande_SanJuan.pdf',
    3: '5_3_PUNA_Vilama.pdf',
    4: '5_7_PUNA_Del_Rincon.pdf',
    5: '5_11_PUNA_Pocitos.pdf',
    6: '4_2_AJ_ Calchaqui_Sup.pdf',
    7: '5_13_Puna_Tolillar.pdf',
    8: '4_5_AJ_Arias_Arenales.pdf',
    9: '4_6_AJ_Chicoana.pdf',
    10: '4_3_AJ_Luracatao.pdf',
    11: '4_4_AJ_Blanco.pdf',
    12: '4_9_AJ_Calchaqui_Med.pdf',
    13: '5_19_PUNA_Laguna_Blanca.pdf',
    14: '4_11_AJ_Santa_Maria_EO.pdf',
    15: '5_18_PUNA_Carachi_Pampa.pdf',
    16: '5_4_PUNA_Zapaleri.pdf',
    17: '5_8_PUNA_Incahuasi.pdf',
    18: '2_7_AB_GrandeTarija.pdf',
    19: '2_5_AB_Blanco.pdf',
    20: '3_2_MLF_Ledesma.pdf',
    21: '3_4_MLF_Negro_SanFco_Sup.pdf',
    22: '3_5_MLF_San_Lorenzo.pdf',
    23: '3_3_MLF_Mojotoro.pdf',
    24: '2_2_AB_LosToldos_lipeo.pdf',
    25: '5_2_PUNA_Salinas_Grandes.pdf',
    26: '3_1_MLF_Grande_Perico.pdf',
    27: '4_1_AJ_Rosario Toro.pdf',
    28: '5_12_PUNA_Centenario.pdf',
    29: '5_17_PUNA_HMuerto.pdf',
    30: '4_10_AJ_Guasamayo.pdf',
    31: '2_1_AB_Condado.pdf',
    32: '2_3_AB_PescadoSuperior.pdf',
    33: '2_4_AB_Iruya.pdf',
    34: '3_6_MLF_San_Fco_Inf.pdf',
    35: '6_2_SAS_Norte_Quebrada_Colorada.pdf',
    36: '8_2_JMI_Medio.pdf',
    37: '8_3_JMI_Medina.pdf',
    38: '2_6_AB_Colorado.pdf',
    39: '7_1_BI_RioSeco.pdf',
    40: '9_2_DS_Chico.pdf',
    41: '4_8_AJ_Calchaqui_Inf.pdf',
    42: '9_3_DS_Marapa.pdf',
    43: '14_3_D_Ambargasta.pdf',
    44: '4_7_AJ_LasConchas_Guachipas.pdf',
    45: '4_11_AJ_Santa_Maria_EO.pdf',
    46: '14_1_D_Saladillo.pdf',
    47: '9_1_DS_Sali_Sup.pdf',
    48: '12_2_RHU_Uruena.pdf',
    49: '12_1_RHU_RosarioHorcones.pdf',
    50: '10_2_JS_salado.pdf',
    51: '15_3_SP_hualfin.pdf',
    52: '15_4_SP_san_fernando.pdf',
    53: '13_3_ACS_Cazadero.pdf',
    54: '13_5_ACS_Guanchin.pdf',
    55: '15_6_SP_aguasalada_amanao.pdf',
    56: '15_1_SP_belen.pdf',
    57: '13_6_ACS_Colorado.pdf',
    58: '13_7_ACS_Salado.pdf',
    59: '13_2_ACS_de_las_lozas.pdf',
    60: '15_5_SP_laguna_brava.pdf',
    61: '6_1_SAS_Itiyuro.pdf',
    62: '13_8_ACS_Abaucan_fiambala.pdf',
    63: '16_1_SG_del_valle.pdf',
    64: '14_2_D_Icano.pdf',
    65: '11_sinaporte_surestesalta.pdf',
    66: '6_3_SAS_Norte_Del_Rio_Muerto.pdf',
    67: '1_3_PIL_Pilcomay.pdf',
    68: '7_4_BI_Bermejito.pdf',
    69: '7_5_BI_LajitasSur.pdf',
    70: '7_3_BI_Bermejo.pdf',
    71: '7_2_BI_DeLasChunas.pdf',
    72: '8_1_JMI_Juramento_Inferior.pdf',
    73: '10_1_JS_SaladoET.pdf',
    74: '15_7_SP_pipanaco.pdf',
    75: '15_2_SP_campo_belen.pdf',
    76: '13_4_ACS_Laguna_verde.pdf',
    77: '16_2_SG_carrizal.pdf',
    78: '5_6_PUNA_Jama.pdf',
    79: '5_10_PUNA_Arizaro.pdf',
    80: '5_16_PUNA_Antofalla.pdf',
    81: '5_5_PUNA_Cauchari.pdf',
    82: '5_9_PUNA_Llullaillaco.pdf',
    83: '5_14_PUNA_AguasCalientes.pdf',
    84: '13_1_ACS_Salitral.pdf'
}

MACRO_INFO = {
    1.0: {"id": "4_AJ", "name": "Alta Cuenca del Río Juramento", "pdf": "4_AJ.pdf", "color": "#0284c7"},
    2.0: {"id": "8_JMI", "name": "Juramento Medio Inferior", "pdf": "8_JMI.pdf", "color": "#0369a1"},
    3.0: {"id": "10_JS", "name": "Juramento - Salado", "pdf": "10_JS.pdf", "color": "#075985"},
    4.0: {"id": "5_PUNA", "name": "Cerradas de la Puna", "pdf": "5_PUNA.pdf", "color": "#d97706"},
    5.0: {"id": "3_MLF", "name": "Mojotoro - Lavayén - San Francisco", "pdf": "3_MLF.pdf", "color": "#059669"},
    6.0: {"id": "2_AB", "name": "Alta Río Bermejo", "pdf": "2_AB.pdf", "color": "#16a34a"},
    8.0: {"id": "7_BI", "name": "Bermejo Inferior", "pdf": "7_BI.pdf", "color": "#0d9488"},
    9.0: {"id": "6_SAS_Norte", "name": "Sin Aporte Significativo - Noreste de Salta", "pdf": "6_SAS_Norte.pdf", "color": "#64748b"},
    12.0: {"id": "1_PIL", "name": "Pilcomayo", "pdf": "1_PIL.pdf", "color": "#7c3aed"},
    14.0: {"id": "11_sinaporte_surestesalta", "name": "Sin Aporte Significativo - Sureste de Salta", "pdf": "11_sinaporte_surestesalta.pdf", "color": "#475569"},
    16.0: {"id": "14_D", "name": "Dulce", "pdf": "14_D.pdf", "color": "#ea580c"},
    17.0: {"id": "9_DS", "name": "Dulce Superior", "pdf": "9_DS.pdf", "color": "#c2410c"},
    19.0: {"id": "12_RHU", "name": "Rosario Horcones - Urueña", "pdf": "12_RHU.pdf", "color": "#db2777"},
    20.0: {"id": "13_ACS", "name": "Abaucán", "pdf": "13_ACS.pdf", "color": "#c026d3"},
    21.0: {"id": "13_ACS", "name": "Abaucán", "pdf": "13_ACS.pdf", "color": "#c026d3"},
    22.0: {"id": "15_SP", "name": "Salar del Pipanaco", "pdf": "15_SP.pdf", "color": "#b45309"},
    90.0: {"id": "16_SG", "name": "Salinas Grandes", "pdf": "16_SG.pdf", "color": "#65a30d"}
}

def get_relief_class(slope):
    try:
        s = float(slope)
        if s < 2: return "Llano o casi llano"
        if s < 5: return "Suavemente ondulado"
        if s < 10: return "Ondulado"
        if s < 15: return "Fuertemente ondulado"
        if s < 25: return "Colinado / Quebrado"
        if s < 45: return "Escarpado / Montañoso"
        return "Muy escarpado"
    except:
        return "N/D"

def get_gravelius_interpretation(kc):
    try:
        k = float(kc)
        if k < 1.25: return "Casi circular (Mayor concentración de crecidas)"
        if k < 1.50: return "Oval-redonda a oval-oblonga"
        if k < 1.75: return "Oval-oblonga a alargada"
        return "Fuertemente alargada (Baja concentración de crecidas)"
    except:
        return "N/D"

def get_horton_interpretation(kf):
    try:
        f = float(kf)
        if f > 0.6: return "Forma ancha / compacta (Picos rápidos)"
        if f >= 0.3: return "Forma moderadamente ensanchada"
        return "Forma alargada (Caudales pico amortiguados)"
    except:
        return "N/D"

def extract_standard_three_maps(pdf_path, subbasin_id):
    if not os.path.exists(pdf_path):
        return []

    rendered_list = []
    try:
        doc = pymupdf.open(pdf_path)
        found_pages = {}

        for page_num in range(len(doc)):
            txt = doc[page_num].get_text().lower()
            for line in txt.split('\n'):
                line = line.strip()
                if 'figura ' in line or 'mapa ' in line:
                    if any(w in line for w in ['subcuenca', 'cuenca', 'ubicaci']) and 'flujo' not in line and 'pendiente' not in line:
                        if 'ubicacion' not in found_pages:
                            found_pages['ubicacion'] = (page_num, 'Mapa de Delimitación y Ubicación')
                    elif any(w in line for w in ['flujo', 'flujos', 'direcci']):
                        if 'flujos' not in found_pages:
                            found_pages['flujos'] = (page_num, 'Mapa de Dirección de Flujos')
                    elif 'pendiente' in line:
                        if 'pendiente' not in found_pages:
                            found_pages['pendiente'] = (page_num, 'Mapa de Pendientes (%)')

        if 'ubicacion' not in found_pages and len(doc) >= 2:
            found_pages['ubicacion'] = (1, 'Mapa de Delimitación y Ubicación')
        if 'flujos' not in found_pages and len(doc) >= 4:
            found_pages['flujos'] = (3, 'Mapa de Dirección de Flujos')
        if 'pendiente' not in found_pages and len(doc) >= 5:
            found_pages['pendiente'] = (4, 'Mapa de Pendientes (%)')

        order = ['ubicacion', 'flujos', 'pendiente']
        for key in order:
            if key in found_pages:
                page_idx, map_title = found_pages[key]
                fname = f"{subbasin_id}_{key}.jpg"
                fpath = os.path.join(FIGURES_DIR, fname)
                
                if not os.path.exists(fpath):
                    pix = doc[page_idx].get_pixmap(dpi=105)
                    pix.save(fpath)
                    try:
                        im = Image.open(fpath)
                        im.save(fpath, 'JPEG', quality=75, optimize=True)
                    except:
                        pass

                rendered_list.append({
                    "key": key,
                    "page": page_idx + 1,
                    "file": f"assets/figures/{fname}",
                    "title": map_title
                })

    except Exception as e:
        print(f"Error rendering maps for {pdf_path}: {e}")

    return rendered_list

def run():
    print("==========================================================")
    print("Iniciando extracción y sistematización mejorada de cuencas")
    print("==========================================================")

    # 1. Process Macrocuencas
    print("\n1. Procesando 16 Macrocuencas...")
    processed_macros = {}
    for code, info in MACRO_INFO.items():
        if info["id"] not in processed_macros:
            sintesis = parse_pdf_sintesis(info["pdf"], is_macro=True)
            processed_macros[info["id"]] = {
                "id": info["id"],
                "code": code,
                "name": info["name"],
                "pdf": info["pdf"],
                "color": info["color"],
                "sintesis": sintesis,
                "subcuencas_count": 0,
                "superficie_total": 0.0
            }
            print(f"  * {info['name']}: {len(sintesis)} caracteres (PDF: {info['pdf']})")

    # 2. Process Subcuencas
    print("\n2. Procesando 85 Subcuencas desde cuencasnoa_js.geojson...")
    with open('cuencasnoa_js.geojson', 'r', encoding='utf-8', errors='replace') as f:
        geo_data = json.load(f)

    features = geo_data['features']
    processed_subcuencas = []
    web_features = []

    for idx, feat in enumerate(features):
        props = feat['properties']
        geom = feat['geometry']

        sub_id = f"sub_{idx:02d}"
        nom = clean_text(props.get('Nombre_1', f'Subcuenca {idx+1}'))
        cod_macro = props.get('Cod_Macro_', 0.0)
        macro_meta = MACRO_INFO.get(cod_macro, {
            "id": "macro_other", "name": clean_text(props.get('Nom_Macro_', 'Otras')), "pdf": "", "color": "#64748b"
        })
        
        pdf_file = EXPLICIT_PDF_MAP.get(idx, "")
        sintesis = parse_pdf_sintesis(pdf_file, is_macro=False)
        rendered_maps = extract_standard_three_maps(pdf_file, sub_id)

        # Morphological numbers
        sup = float(props.get('Superficie', 0) or 0)
        perim = float(props.get('Perimetro', 0) or 0)
        alt_max = float(props.get('Alt_max', 0) or 0)
        alt_min = float(props.get('Alt_min', 0) or 0)
        alt_med = float(props.get('Alt_med', 0) or 0)
        alt_ds = str(props.get('Alt_DS', '')).replace(',', '.')
        pend_med = float(props.get('Pendien_Me', 0) or 0)
        pend_max = float(props.get('Pend_Max', 0) or 0)
        pend_ds = str(props.get('Pendien_DS', '')).replace(',', '.')
        kc = float(props.get('Ind_Compac', 0) or 0)
        kf = float(props.get('Factor_For', 0) or 0)
        long_ax = float(props.get('MAX_LongAx', 0) or 0)
        ancho_med = float(props.get('Ancho_Medi', 0) or 0)

        if macro_meta["id"] in processed_macros:
            processed_macros[macro_meta["id"]]["subcuencas_count"] += 1
            processed_macros[macro_meta["id"]]["superficie_total"] += sup

        sub_record = {
            "id": sub_id,
            "idx": idx,
            "nombre": nom,
            "macro_id": macro_meta["id"],
            "macro_nombre": macro_meta["name"],
            "macro_color": macro_meta["color"],
            "macro_pdf": macro_meta["pdf"],
            "pdf_origen": pdf_file,
            "catalogo_url": "https://geo-nodo01.inta.gob.ar/catalogue/#/document/64",
            "morfometria": {
                "superficie_km2": round(sup, 2),
                "perimetro_km": round(perim, 2),
                "longitud_eje_km": round(long_ax, 2),
                "ancho_medio_km": round(ancho_med, 2),
                "altitud_min_m": round(alt_min, 1),
                "altitud_med_m": round(alt_med, 1),
                "altitud_max_m": round(alt_max, 1),
                "altitud_ds_m": alt_ds,
                "desnivel_m": round(alt_max - alt_min, 1),
                "pendiente_media_pct": round(pend_med, 2),
                "pendiente_max_pct": round(pend_max, 2),
                "pendiente_ds_pct": pend_ds,
                "relieve_clase": get_relief_class(pend_med),
                "gravelius_kc": round(kc, 3),
                "gravelius_interpretacion": get_gravelius_interpretation(kc),
                "horton_kf": round(kf, 3),
                "horton_interpretacion": get_horton_interpretation(kf)
            },
            "sintesis_pdf": sintesis if sintesis else "La presente unidad hidrográfica contiene información morfométrica y cartográfica sistematizada del informe técnico.",
            "figuras_renderizadas": rendered_maps
        }

        processed_subcuencas.append(sub_record)

        def round_coords(coords):
            if isinstance(coords[0], (int, float)):
                return [round(coords[0], 5), round(coords[1], 5)]
            return [round_coords(c) for c in coords]

        clean_geom = {
            "type": geom["type"],
            "coordinates": round_coords(geom["coordinates"])
        }

        web_features.append({
            "type": "Feature",
            "id": sub_id,
            "properties": {
                "id": sub_id,
                "idx": idx,
                "nombre": nom,
                "macro_id": macro_meta["id"],
                "macro_nombre": macro_meta["name"],
                "color": macro_meta["color"],
                "superficie": round(sup, 1),
                "alt_med": round(alt_med, 0),
                "pend_med": round(pend_med, 1),
                "relieve": get_relief_class(pend_med),
                "kc": round(kc, 2)
            },
            "geometry": clean_geom
        })

        if (idx + 1) % 15 == 0 or idx == len(features) - 1:
            print(f"  * Procesadas {idx+1}/{len(features)} subcuencas...")

    for m in processed_macros.values():
        m["superficie_total"] = round(m["superficie_total"], 2)

    final_data = {
        "metadata": {
            "titulo": "Cuencas Hídricas de las Provincias del NOA",
            "institucion": "INTA EEA Salta",
            "autores": [
                {"nombre": "Paoli, Héctor", "rol": "Ing. Agrónomo - INTA EEA Salta"},
                {"nombre": "Elena, Hernán", "rol": "Lic. en Recursos Naturales - INTA EEA Salta"},
                {"nombre": "Mosciaro, Javier", "rol": "Ing. en Recursos Naturales - INTA EEA Salta"},
                {"nombre": "Ledesma, Fernando", "rol": "Ing. Agrónomo - INTA EEA Salta"},
                {"nombre": "Noé, Yanina", "rol": "Ing. en Recursos Naturales - INTA EEA Salta"}
            ],
            "documento_oficial_url": "https://geo-nodo01.inta.gob.ar/catalogue/#/document/64",
            "anio": "2011",
            "total_subcuencas": len(processed_subcuencas),
            "total_macrocuencas": len(processed_macros)
        },
        "macrocuencas": list(processed_macros.values()),
        "subcuencas": processed_subcuencas
    }

    data_json_path = os.path.join(DATA_DIR, 'cuencas_data.json')
    with open(data_json_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Base de datos JSON actualizada: {data_json_path}")

if __name__ == '__main__':
    run()
