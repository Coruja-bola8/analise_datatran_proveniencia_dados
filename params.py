"""Parâmetros v2 (dados reais: acidentes2017-2025_todas_causas_tipos, 37 campos, uma linha por pessoa/veículo/causa).
Importado DEPOIS de config.py, então estes valores prevalecem. Não altera DB_URL, ANOS nem PADRAO_ARQUIVO."""

# Etapa 3a: textos que representam ausência/não aplicável. Convertidos em NULL (o texto original vai para o log).
# 'NÃO INFORMADO' e 'IGNORADO' ficam de fora: são categorias declaradas pela PRF, não símbolos de ausência.
TOKENS_AUSENCIA = ["NA", "N/A"]

# Etapa 3c: campos categóricos do acidente em que NULL vira 'Ignorado'
# (campos de pessoa/veículo NÃO entram: lá o NA significa 'não aplicável', não 'desconhecido')
CAMPOS_CATEGORICOS_IGNORADO = ["tipo_acidente", "classificacao_acidente", "condicao_metereologica",
                               "tracado_via", "tipo_pista", "uso_solo", "fase_dia", "sentido_via"]

# Etapa 4
CAMPOS_PADRONIZAR = ["causa_acidente", "tipo_acidente", "classificacao_acidente", "fase_dia", "sentido_via",
                     "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo", "municipio",
                     "dia_semana", "tipo_veiculo", "tipo_envolvido", "estado_fisico", "sexo",
                     "regional", "delegacia", "uop"]
CAMPOS_CONJUNTO = ["tracado_via"]   # valor = conjunto separado por ';' -> ordena os componentes
