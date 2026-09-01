import requests
import base64
import time

# 1. Separación y ordenación estricta de la comunidad neustónica
neuston = [
    ("Dosima fascicularis", "Arthropoda", 462187),
    ("Glaucus atlanticus", "Mollusca", 50498),
    ("Janthina janthina", "Mollusca", 121654),
    ("Lepas anatifera", "Arthropoda", 69949),
    ("Lepas anserifera", "Arthropoda", 48778),
    ("Lepas pectinata", "Arthropoda", 329099),
    ("Physalia physalis", "Cnidaria", 117302),
    ("Porpita porpita", "Cnidaria", 59683),
    ("Velella velella", "Cnidaria", 59698)
]

# 2. Resto de especies (manteniendo la homogeneización taxonómica a nivel de filo)
otros = [
    ("Actinia equina", "Cnidaria", 130085),
    ("Anemonia viridis", "Cnidaria", 118895),
    ("Aplysia punctata", "Mollusca", 57663),
    ("Arenicola marina", "Annelida", 208364),
    ("Ascophyllum nodosum", "Ochrophyta", 68770),
    ("Carcinus maenas", "Arthropoda", 52523),
    ("Chamelea gallina", "Mollusca", 448229),
    ("Chrysaora hysoscella", "Cnidaria", 360314),
    ("Chthamalus stellatus", "Arthropoda", 210292),
    ("Codium tomentosum", "Chlorophyta", 326210),
    ("Corallina officinalis", "Rhodophyta", 123632),
    ("Coryphoblennius galerita", "Chordata", 118692),
    ("Delesseria sanguinea", "Rhodophyta", 542730),
    ("Dictyota dichotoma", "Ochrophyta", 51024),
    ("Donax trunculus", "Mollusca", 59392),
    ("Ensis siliqua", "Mollusca", 332435),
    ("Fucus vesiculosus", "Ochrophyta", 48216),
    ("Gelidium corneum", "Rhodophyta", 790283),
    ("Gobius paganellus", "Chordata", 118706),
    ("Gracilaria gracilis", "Rhodophyta", 345393),
    ("Halichondria panicea", "Porifera", 186854),
    ("Labrus bergylta", "Chordata", 103911),
    ("Lipophrys pholis", "Chordata", 210294),
    ("Littorina littorea", "Mollusca", 81606),
    ("Muraena helena", "Chordata", 118590),
    ("Mytilus galloprovincialis", "Mollusca", 81648),
    ("Ophiothrix fragilis", "Echinodermata", 326334),
    ("Pachygrapsus marmoratus", "Arthropoda", 59283),
    ("Pagurus bernhardus", "Arthropoda", 152975),
    ("Paracentrotus lividus", "Echinodermata", 48032),
    ("Patella vulgata", "Mollusca", 154706),
    ("Pelagia noctiluca", "Cnidaria", 256089),
    ("Pollicipes pollicipes", "Arthropoda", 332554),
    ("Pomatoschistus microps", "Chordata", 110042),
    ("Rhizostoma pulmo", "Cnidaria", 319371),
    ("Sargassum muticum", "Ochrophyta", 130177),
    ("Scorpaena notata", "Chordata", 118630),
    ("Serranus cabrilla", "Chordata", 118675),
    ("Symphodus melops", "Chordata", 113533),
    ("Tripterygion delaisi", "Chordata", 118642),
    ("Ulva lactuca", "Chlorophyta", 67423)
]

# Concatenar ambas listas
datos = neuston + otros

# 3. Plantilla HTML
html_content = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    body { font-family: 'Helvetica', 'Arial', sans-serif; margin: 20px; font-size: 11pt; color: #333; }
    h1 { text-align: center; font-size: 16pt; border-bottom: 2px solid #333; padding-bottom: 10px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: middle; }
    th { background-color: #f4f4f4; font-weight: bold; }
    .species-name { font-style: italic; }
    .img-container { text-align: center; width: 80px; }
    img { max-width: 80px; max-height: 80px; border-radius: 4px; object-fit: cover; }
    @media print {
        th, td { page-break-inside: avoid; }
    }
</style>
</head>
<body>
<h1>Set of recorded species: neuston (bold) and baseline </h1>
<table>
    <thead>
        <tr>
            <th>Scientific name</th>
            <th>Phylum</th>
            <th>Taxon ID (iNat)</th>
            <th>Image</th>
        </tr>
    </thead>
    <tbody>
"""

headers = {'User-Agent': 'EcologiaMarina_Script/1.1 (contacto_academico)'}
neuston_names = [sp[0] for sp in neuston]

# 4. Peticiones a la API de iNaturalist y lógica de formato
for name, phylum, taxon_id in datos:
    url = f"https://api.inaturalist.org/v1/taxa/{taxon_id}"
    img_tag = '<em>Sin imagen</em>'
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            res_json = resp.json()
            results = res_json.get("results", [])
            
            if results and results[0].get("default_photo"):
                photo_url = results[0]["default_photo"].get("square_url") or results[0]["default_photo"].get("medium_url")
                
                if photo_url:
                    img_resp = requests.get(photo_url, headers=headers, timeout=10)
                    if img_resp.status_code == 200:
                        img_b64 = base64.b64encode(img_resp.content).decode('utf-8')
                        mime_type = "image/jpeg" if ".jpg" in photo_url or ".jpeg" in photo_url else "image/png"
                        img_tag = f'<img src="data:{mime_type};base64,{img_b64}" alt="{name}">'
    except Exception as e:
        img_tag = f'<em>Error API</em>'
        print(f"Fallo de conexión o timeout en {name}: {e}")

    # Condicional para aplicar negrita a las especies del neuston
    display_name = f"<strong>{name}</strong>" if name in neuston_names else name

    html_content += f"""
        <tr>
            <td class="species-name">{display_name}</td>
            <td>{phylum}</td>
            <td>{taxon_id}</td>
            <td class="img-container">{img_tag}</td>
        </tr>
    """
    print(f"Procesado: {name} ({phylum})")
    
    # 5. Limitador de peticiones
    time.sleep(1.2) 

html_content += """
    </tbody>
</table>
</body>
</html>
"""

# 6. Exportación local
archivo_salida = "species_inaturalist.html"
with open(archivo_salida, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\\nProceso completado. La jerarquía y el formato en negrita se han aplicado a la comunidad neustónica. Abre '{archivo_salida}' en un navegador para imprimir a PDF.")