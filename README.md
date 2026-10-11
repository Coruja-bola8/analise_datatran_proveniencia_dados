# Proveniência de dados no DATATRAN (acidentes2017-2025_todas_causas_tipos)

Ordem de execução (já feitas: 01, 02, 02b):
1. `python 03_duplicatas.py --refazer`   Etapa 2: duplicatas exatas (linha idêntica)
2. `python 04_ausentes.py`               Etapa 3: 'NA'/'N/A' -> NULL; imputação de coordenadas (se houver ausência); 'Ignorado'
3. `python 05_padronizacao.py`           Etapa 4: padronização (+ mapas/<campo>.csv, opcional)
4. `python 06_validacao_geo.py`          Etapa 5: validação + clean.acidente (precisa de dados/aux: IBGE e DNIT)
5. `python 07_resultados.py`             números do Capítulo 4 -> saida/resultados_cap4.md
6. `python 08_reversibilidade.py`        teste empírico de reversibilidade

Para refazer desde a Etapa 2: `python 03_duplicatas.py --refazer` (apaga o log das etapas 2-5).
`params.py` sobrescreve parâmetros do `config.py`. O `config.py` continua com DB_URL, ANOS, PADRAO_ARQUIVO e caminhos IBGE/DNIT.
`mapas/causa_acidente.RASCUNHO.csv` é uma PROPOSTA a ser revisada pelo grupo; renomeie para `causa_acidente.csv` para aplicá-la.
