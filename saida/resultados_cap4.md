# Resultados para o Capítulo 4

## 1. Camada de origem (arquivos)

Campos publicados distintos: 37

| ano | nome_arquivo | encoding | n_linhas | n_colunas | sha256_12 |
|---|---|---|---|---|---|
| 2.017 | acidentes2017_todas_causas_tipos.csv | latin-1 | 342.497 | 37 | ebc393a4919e |
| 2.018 | acidentes2018_todas_causas_tipos.csv | latin-1 | 316.638 | 37 | ad5401fd04e9 |
| 2.019 | acidentes2019_todas_causas_tipos.csv | latin-1 | 324.192 | 37 | f67be7be9fac |
| 2.020 | acidentes2020_todas_causas_tipos.csv | latin-1 | 384.640 | 37 | d771a151c26b |
| 2.021 | acidentes2021_todas_causas_tipos.csv | latin-1 | 436.523 | 37 | d207a0f80e9f |
| 2.022 | acidentes2022_todas_causas_tipos.csv | latin-1 | 507.204 | 37 | 480365bfbe0e |
| 2.023 | acidentes2023_todas_causas_tipos.csv | latin-1 | 571.052 | 37 | 3405aea4cc21 |
| 2.024 | acidentes2024_todas_causas_tipos.csv | latin-1 | 603.839 | 37 | a6457e965dc3 |
| 2.025 | acidentes2025_todas_causas_tipos.csv | latin-1 | 584.010 | 37 | b48968a8017a |

## 2. Volume por ano

| ano | linhas | acidentes |
|---|---|---|
| 2.017 | 342.497 | 89.567 |
| 2.018 | 316.638 | 69.333 |
| 2.019 | 324.192 | 67.558 |
| 2.020 | 384.640 | 63.586 |
| 2.021 | 436.523 | 64.567 |
| 2.022 | 507.204 | 64.607 |
| 2.023 | 571.052 | 67.767 |
| 2.024 | 603.839 | 73.202 |
| 2.025 | 584.010 | 72.529 |

## 3. Duplicatas

| item | n |
|---|---|
| descartes (linha idêntica) | 0 |
| linhas na tabela primária | 4.070.595 |
| linhas em clean.datatran | 4.070.595 |
| acidentes (ids distintos) | 632.716 |

## 3b. Chave do TCC original (data, horário, km, BR, UF) aplicada aos dados reais

Mostra por que a chave original não identifica duplicatas nestes dados (várias pessoas por acidente).

| grupos_pela_chave | grupos_com_mais_de_um_acidente | linhas_que_a_chave_marcaria_como_duplicata |
|---|---|---|
| 632.341 | 366 | 3.438.254 |

## 4a. Textos de ausência convertidos em NULL (por campo)

| campo | texto | celulas |
|---|---|---|
| idade | NA | 740.610 |
| ilesos | NA | 387.143 |
| sexo | NA | 387.143 |
| pesid | NA | 387.143 |
| mortos | NA | 387.143 |
| estado_fisico | NA | 387.143 |
| feridos_graves | NA | 387.143 |
| feridos_leves | NA | 387.143 |
| tipo_envolvido | NA | 387.143 |
| ano_fabricacao_veiculo | NA | 144.991 |
| id_veiculo | NA | 144.991 |
| tipo_veiculo | NA | 144.991 |
| br | NA | 10.098 |
| km | NA | 10.098 |
| uop | N/A | 2.900 |
| delegacia | N/A | 1.609 |
| delegacia | NA | 298 |
| regional | NA | 298 |
| uop | NA | 298 |
| classificacao_acidente | NA | 123 |
| regional | N/A | 84 |

## 4b. NULL -> 'Ignorado' (por campo)

| campo | celulas |
|---|---|
| classificacao_acidente | 123 |
| tipo_acidente | 96 |

## 4c. Coordenadas por origem (linhas e acidentes)

Imputações de coordenada (latitude/longitude) no log: 0

| coord_status | linhas | acidentes |
|---|---|---|
| OBSERVADA | 4.070.595 | 632.716 |

## 5. Padronização: valores distintos antes e depois

Registro por valor em prov.transformacao_valor; por linha apenas nas fusões.

| campo | distintos_brutos | distintos_apos | pares_alterados | celulas_alteradas | celulas_em_fusao |
|---|---|---|---|---|---|
| causa_acidente | 92 | 91 | 92 | 4.070.595 | 15.652 |
| tipo_acidente | 21 | 22 | 22 | 4.070.595 | 0 |
| classificacao_acidente | 4 | 4 | 4 | 4.070.595 | 0 |
| fase_dia | 4 | 4 | 4 | 4.070.595 | 0 |
| sentido_via | 3 | 3 | 3 | 4.070.595 | 0 |
| condicao_metereologica | 10 | 10 | 10 | 4.070.595 | 0 |
| tipo_pista | 3 | 3 | 3 | 4.070.595 | 0 |
| tracado_via | 1.328 | 384 | 1.328 | 4.070.595 | 852.577 |
| uso_solo | 2 | 2 | 2 | 4.070.595 | 0 |
| municipio | 2.156 | 2.156 | 1 | 661 | 0 |
| dia_semana | 7 | 7 | 7 | 4.070.595 | 0 |
| tipo_veiculo | 26 | 25 | 25 | 3.925.604 | 0 |
| tipo_envolvido | 6 | 5 | 5 | 3.683.452 | 0 |
| estado_fisico | 6 | 5 | 5 | 3.683.452 | 0 |
| sexo | 5 | 4 | 4 | 3.683.452 | 0 |
| regional | 31 | 29 | 1 | 6 | 0 |
| delegacia | 158 | 156 | 0 | 0 | 0 |
| uop | 442 | 440 | 0 | 0 | 0 |

## 6a. Validação geoespacial (linhas)

| resultado | linhas |
|---|---|
| OK | 4.014.009 |
| DIST_RODOVIA | 36.960 |
| OK_SEM_GEOM_RODOVIA | 10.030 |
| UF_INCOMPATIVEL | 9.413 |
| FORA_BRASIL | 183 |

## 6b. Validação geoespacial (acidentes)

| resultado | acidentes |
|---|---|
| OK | 621.669 |
| DIST_RODOVIA | 8.069 |
| UF_INCOMPATIVEL | 1.529 |
| OK_SEM_GEOM_RODOVIA | 1.396 |
| FORA_BRASIL | 53 |

## 6c. Acidentes com coordenadas divergentes entre as linhas do mesmo id

| ids_com_conflito | acidentes |
|---|---|
| 3 | 632.716 |

## 7. Precisão decimal da latitude por ano (acidentes)

| ano | sem_decimais | dec_1a3 | dec_4a5 | dec_6a7 | dec_8mais | acidentes |
|---|---|---|---|---|---|---|
| 2.017 | 264 | 2.421 | 32.629 | 13.794 | 40.459 | 89.567 |
| 2.018 | 117 | 1.359 | 11.922 | 25.167 | 30.768 | 69.333 |
| 2.019 | 17 | 580 | 6.606 | 19.957 | 40.398 | 67.558 |
| 2.020 | 31 | 315 | 4.353 | 17.946 | 40.941 | 63.586 |
| 2.021 | 22 | 404 | 8.749 | 17.596 | 37.796 | 64.567 |
| 2.022 | 26 | 330 | 4.395 | 18.605 | 41.251 | 64.607 |
| 2.023 | 14 | 724 | 34.770 | 14.352 | 17.907 | 67.767 |
| 2.024 | 23 | 403 | 5.126 | 21.071 | 46.579 | 73.202 |
| 2.025 | 37 | 978 | 7.285 | 29.408 | 34.821 | 72.529 |

## 8. Inventário do registro de modificações

| operacao | regra | etapa | modificacoes | linhas_afetadas |
|---|---|---|---|---|
| IMPUTACAO | categoria_ignorado | E3_ausentes | 219 | 218 |
| PADRONIZACAO | token_ausencia_para_nulo | E3_ausentes | 4.298.533 | 801.081 |
| PADRONIZACAO | padronizacao_com_fusao | E4_padronizacao | 868.229 | 864.866 |
| MARCACAO | validacao_geoespacial | E5_validacao_geo | 46.556 | 46.556 |

## 8b. Registro por valor da padronização

| regra | pares_valor | celulas | pares_em_fusao |
|---|---|---|---|
| upper_trim_unaccent+mapa | 1.516 | 55.682.577 | 1.197 |

## 9. Distinguibilidade: origem da coordenada obtida SÓ pelo log vs coord_status

| origem_coord | linhas | divergentes_de_coord_status |
|---|---|---|
| OBSERVADA | 4.070.595 | 0 |

## 10. Atividades registradas (modelo PROV)

| id_atividade | etapa | script | versao | hash_script | inicio | fim | n_linhas_afetadas |
|---|---|---|---|---|---|---|---|
| 1 | E0_ingestao | 01_ingestao.py | sem-git | eedbe15474 | 2026-10-10 00:38:10.088616+00:00 | 2026-10-10 00:38:33.917774+00:00 | 342.497 |
| 2 | E0_ingestao | 01_ingestao.py | sem-git | eedbe15474 | 2026-10-10 00:38:38.109810+00:00 | 2026-10-10 00:39:04.958903+00:00 | 316.638 |
| 3 | E0_ingestao | 01_ingestao.py | sem-git | eedbe15474 | 2026-10-10 00:39:11.025791+00:00 | 2026-10-10 00:39:35.395203+00:00 | 324.192 |
| 4 | E0_ingestao | 01_ingestao.py | sem-git | eedbe15474 | 2026-10-10 00:39:40.885240+00:00 | 2026-10-10 00:40:11.646615+00:00 | 384.640 |
| 5 | E0_ingestao | 01_ingestao.py | sem-git | eedbe15474 | 2026-10-10 00:40:17.626201+00:00 | 2026-10-10 00:40:51.949070+00:00 | 436.523 |
| 6 | E0_ingestao | 01_ingestao.py | sem-git | eedbe15474 | 2026-10-10 00:40:58.803236+00:00 | 2026-10-10 00:41:40.438289+00:00 | 507.204 |
| 7 | E0_ingestao | 01_ingestao.py | sem-git | eedbe15474 | 2026-10-10 00:41:48.724694+00:00 | 2026-10-10 00:42:34.531253+00:00 | 571.052 |
| 8 | E0_ingestao | 01_ingestao.py | sem-git | eedbe15474 | 2026-10-10 00:42:42.928483+00:00 | 2026-10-10 00:43:30.227548+00:00 | 603.839 |
| 9 | E0_ingestao | 01_ingestao.py | sem-git | eedbe15474 | 2026-10-10 00:43:38.177492+00:00 | 2026-10-10 00:44:28.770914+00:00 | 584.010 |
| 10 | E2_duplicatas | 03_duplicatas.py | sem-git | d29c7887f5 | 2026-10-10 12:32:35.768491+00:00 | 2026-10-10 12:38:13.613800+00:00 | 0 |
| 11 | E3_ausentes | 04_ausentes.py | sem-git | 4416c68239 | 2026-10-10 12:43:07.035066+00:00 | 2026-10-10 13:08:47.327931+00:00 |  |
| 15 | E4_padronizacao | 05_padronizacao.py | sem-git | 393778bc9d | 2026-10-10 22:20:25.927300+00:00 | 2026-10-10 22:55:56.152621+00:00 | 4.070.595 |
| 17 | E5_validacao_geo | 06_validacao_geo.py | sem-git | 4e633c9c0f | 2026-10-10 23:46:20.734890+00:00 | 2026-10-11 00:11:39.765529+00:00 |  |
