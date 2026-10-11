"""Lista os shapefiles/geopackages de dados/aux/ e mostra CRS, quantidade de feições e colunas.
Não altera nada. Rode: python 00_conferir_aux.py"""
from pathlib import Path

import geopandas as gpd

PASTA = Path("dados/aux")
arquivos = sorted(list(PASTA.rglob("*.shp")) + list(PASTA.rglob("*.gpkg")) + list(PASTA.rglob("*.geojson")))

if not arquivos:
    print(f"Nenhum arquivo .shp/.gpkg/.geojson encontrado em {PASTA.resolve()}")
    print("Descompacte os .zip do IBGE e do DNIT dentro dessa pasta e rode de novo.")

for f in arquivos:
    print("=" * 80)
    print("ARQUIVO:", f)
    try:
        d = gpd.read_file(f)
    except Exception as e:
        print("  erro ao ler:", str(e).splitlines()[0])
        continue
    print("CRS:", d.crs)
    print("FEIÇÕES:", len(d))
    print("TIPOS DE GEOMETRIA:", d.geom_type.value_counts().to_dict())
    print("COLUNAS:", list(d.columns))
    print(d.drop(columns="geometry").head(3).T)