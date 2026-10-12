"""Parâmetros do pipeline. Cada bloco indica a seção do TCC de onde veio."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")

DIR_CSV = Path(os.getenv("DATATRAN_CSV_DIR", "dados/csv"))
DIR_AUX = Path(os.getenv("DATATRAN_AUX_DIR", "dados/aux"))
DIR_SAIDA = Path("saida")
DIR_MAPAS = Path("mapas")

# Seção 3.2: arquivos anuais 2017-2025 (a Introdução/1.2/1.6 dizem 2017-2025: inconsistência do TCC)
ANOS = list(range(2017, 2026))
PADRAO_ARQUIVO = "acidentes{ano}_todas_causas_tipos.csv"
# Seção 3.3: endereço de download de cada arquivo. PREENCHA com a URL real usada.
URL_POR_ANO = {ano: "" for ano in ANOS}

# Etapa 2 (3.4): critério de duplicata. O TCC fala em "rodovia" = campo br.
CHAVE_DUPLICATA = ["data_inversa", "horario", "km", "br", "uf"]

# Etapa 3 (3.4): imputação pela mediana de registros com mesma rodovia e mesmo km.
# (Obs.: br+km sem uf pode misturar trechos de estados diferentes. Teste depois com ["br","uf","km"].)
CHAVE_IMPUTACAO = ["br", "km"]
CAMPOS_CATEGORICOS_IGNORADO = ["condicao_metereologica", "tracado_via", "tipo_pista",
                               "uso_solo", "fase_dia", "sentido_via"]

# Etapa 4: campos de texto padronizados (UPPER, TRIM, sem acento). O TCC só relata causa e tipo.
CAMPOS_PADRONIZAR = ["causa_acidente", "tipo_acidente", "classificacao_acidente", "fase_dia",
                     "sentido_via", "condicao_metereologica", "tipo_pista", "tracado_via",
                     "uso_solo", "municipio", "dia_semana"]

# Etapa 5 / Seção 3.5
LAT_LIM = (-33.75, 5.27)
LON_LIM = (-73.99, -28.85)
TOLERANCIA_M = 2000
UF_ARQUIVO = DIR_AUX / "BR_UF_2025" / "BR_UF_2025.shp"          # malha IBGE 2022
UF_COL_SIGLA = "SIGLA_UF"
RODOVIAS_ARQUIVO = DIR_AUX / "SNV_Bases_Geometricas_2013-Atual" / "SNV_202607A.shp"  # geometria DNIT 2023
RODOVIAS_COL_BR = "vl_br"                         # coluna com o número da BR (ajuste ao seu arquivo)
