# Proveniência de dados na limpeza do DATATRAN (acidentes 2017–2025)

Código e resultados do Trabalho de Conclusão de Curso *Proveniência de dados na limpeza do DATATRAN: dados primários e dados de modificação em análises geoespaciais de acidentes rodoviários* (UNIVESP, Bacharelado em Ciência de Dados).

O repositório reúne os scripts numerados na ordem de execução, o esquema SQL, os arquivos de parâmetros, a lista de dependências com versões e as saídas geradas. Os dados da PRF e as bases auxiliares do IBGE e do DNIT **não** são distribuídos aqui; as instruções para obtê-los e conferi-los estão abaixo.

## Conteúdo do repositório

| Caminho | Conteúdo |
|---|---|
| `00_conferir_aux.py`, `00_inspecao.py` | Conferência das bases auxiliares e inspeção inicial dos arquivos |
| `01_ingestao.py` | Etapa 0: importação dos arquivos anuais para a tabela primária imutável |
| `02_diagnostico.py`, `02b_investigacao.py` | Etapa 1: análise exploratória e investigações complementares (somente leitura) |
| `03_duplicatas.py` a `06_validacao_geo.py` | Etapas 2 a 5: duplicatas, ausências, padronização e validação geoespacial |
| `07_resultados.py`, `07_verificar.py` | Números do Capítulo 4 e conferência dos valores do texto contra o banco |
| `08_reversibilidade.py` | Teste empírico de reversibilidade |
| `config.py`, `params.py`, `prov.py` | Configuração, parâmetros das etapas e funções de registro de proveniência |
| `consultas_item1.py` | Consultas feitas na revisão do trabalho; resultados em `saida/item1_*.csv` |
| `sql/` | `00_schema.sql` (extensões, esquemas e tabelas de proveniência), `10_views_clean.sql` (visão de distinguibilidade) e `20_acidentes_sem_br.sql` (acidentes sem número de BR) |
| `mapas/` | Mapa de equivalência de causas, em forma de rascunho (não aplicado) |
| `saida/` | Resultados e diagnósticos gerados pelos scripts |
| `auxiliares/` | Scripts usados para comparar versões e somas de verificação dos scripts executados e publicados (Seção 3.6 do TCC) |

## Ambiente utilizado

Windows, Python 3.14.7, PostgreSQL 18.6, PostGIS 3.6.2 e extensão `unaccent` 1.1. As versões das bibliotecas Python estão fixadas em `requirements.txt` (pandas 3.0.6, geopandas 1.2.0, GeoAlchemy2 0.20.0, SQLAlchemy 2.1.4, psycopg2-binary 2.9.13, entre outras).

## Instalação

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração

1. Crie um banco PostgreSQL vazio (por exemplo, `datatran`), com o PostGIS instalado no servidor, e execute uma única vez `psql -d datatran -f sql/00_schema.sql`. O arquivo cria as extensões `postgis` e `unaccent` (o usuário precisa de permissão para isso), os esquemas `raw`, `prov`, `clean` e `aux`, as tabelas e visões de proveniência e a função `aux.br_int`. A tabela primária e os gatilhos de imutabilidade **não** estão nesse arquivo: são criados pelo `01_ingestao.py`.
2. Copie `.env.example` para `.env` e preencha as credenciais. O `.env` fica fora do repositório (`.gitignore`).

Variáveis lidas por `config.py`: `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST` (padrão `localhost`), `DB_PORT` (padrão `5432`), `DATATRAN_CSV_DIR` (padrão `dados/csv`) e `DATATRAN_AUX_DIR` (padrão `dados/aux`).

`params.py` sobrescreve parâmetros do `config.py`, como a tolerância de 2 km da validação de distância.

## Dados

1. **PRF:** baixe os arquivos `acidentes{ano}_todas_causas_tipos.csv` de 2017 a 2025 em <https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf> e coloque-os em `dados/csv`.
2. **IBGE:** malha das unidades da federação, edição 2025 (`BR_UF_2025`), em `dados/aux/BR_UF_2025`.
3. **DNIT:** Sistema Nacional de Viação, versão `SNV_202607A`, em `dados/aux/SNV_Bases_Geometricas_2013-Atual`.

Os endereços completos de obtenção das bases auxiliares estão nas referências do TCC.

### Conferência dos arquivos anuais (SHA-256)

Antes de executar, confira os arquivos anuais. Os 12 primeiros caracteres da soma SHA-256 devem coincidir com os da Tabela 1 do TCC:

```powershell
Get-FileHash dados\csv\*.csv -Algorithm SHA256
```

| Ano | SHA-256 (12 primeiros caracteres) |
|---|---|
| 2017 | ebc393a4919e |
| 2018 | ad5401fd04e9 |
| 2019 | f67be7be9fac |
| 2020 | d771a151c26b |
| 2021 | d207a0f80e9f |
| 2022 | 480365bfbe0e |
| 2023 | 3405aea4cc21 |
| 2024 | a6457e965dc3 |
| 2025 | b48968a8017a |

### Bases auxiliares (SHA-256 completo)

| Arquivo | SHA-256 |
|---|---|
| `BR_UF_2025.shp` | `23A9B54FC2DBFBE46298D3152ED4CCFDB60F9E7F178B00C50526741ECBE142D7` |
| `BR_UF_2025.dbf` | `4AAB0C0312C79F20D42ABF1FC4F3FBF6565CDA03E288FD82B033ECE18A018AF6` |
| `SNV_202607A.shp` | `1247033F6234D44BBAE0F679167A187ED0D52ACE86F57196C3FC4E1445D534DB` |
| `SNV_202607A.dbf` | `CF10B04114872670EC385243B2D6D65DEC8978B4A72E8368CE48EDBA4F95CEB0` |

## Ordem de execução

Execute a partir da raiz do projeto, com o ambiente virtual ativo.

| Passo | Comando | Etapa |
|---|---|---|
| 1 | `python 01_ingestao.py` | Etapa 0: ingestão dos arquivos anuais; cria `raw.datatran_primario` e, ao final, os gatilhos que a tornam imutável |
| 2 | `python 02_diagnostico.py` | Etapa 1: diagnóstico (opcional; somente leitura) |
| 3 | `python 03_duplicatas.py --refazer` | Etapa 2: duplicatas exatas (linha idêntica) |
| 4 | `python 04_ausentes.py` | Etapa 3: `NA` e `N/A` em nulo; imputação de coordenadas, se houver ausência; categoria "Ignorado" |
| 5 | `python 05_padronizacao.py` | Etapa 4: padronização (usa `mapas/<campo>.csv`, se existir) |
| 6 | `python 06_validacao_geo.py` | Etapa 5: validação geoespacial e criação de `clean.acidente` (exige `dados/aux`) |
| 7 | `python 07_resultados.py` | Números do Capítulo 4, gravados em `saida/resultados_cap4.md` |
| 8 | `python 08_reversibilidade.py` | Teste empírico de reversibilidade |

Opcionais: `python 07_verificar.py` confere os valores citados no TCC contra o banco, e `sql/10_views_clean.sql`, executado depois da Etapa 5, cria a visão que classifica a origem de cada coordenada apenas a partir do registro de modificações (distinguibilidade, Seção 4.4).

**Atenção ao `--refazer`.** O comando `python 03_duplicatas.py --refazer` apaga o registro de proveniência das Etapas 2 a 5. As etapas 3 a 5 não podem ser repetidas sem isso, porque o registro assume execução em lote único. Não o execute em um banco cujo resultado você queira preservar.

A tabela primária é imutável: o banco bloqueia, por gatilho, atualização, exclusão e `TRUNCATE` nela. O bloqueio é por gatilho, e não por permissão: o proprietário da tabela pode desabilitá-lo. Em um computador comum, as Etapas 2 a 5 levaram cerca de uma hora e meia, e o registro de modificações ocupou cerca de 2,4 GB.

O arquivo `mapas/causa_acidente.RASCUNHO.csv` é uma proposta de equivalência entre versões da classificação de causas, ainda não revisada e **não aplicada** nos resultados do TCC. Para aplicá-la, renomeie-o para `causa_acidente.csv`.

## Controle de versão e reprodutibilidade

O desenvolvimento e a execução ocorreram em uma pasta local sem Git. Os scripts foram publicados neste repositório em 11 de outubro de 2026, depois da execução. Por isso:

- Cada execução foi registrada no banco com o nome do script e a soma SHA-256 do seu conteúdo (calculada sobre arquivos com final de linha LF), e o campo de versão vale `sem-git`.
- O commit `e049ec8`, marcado com a tag **`v1.0-execucao`**, preserva as versões executadas dos cinco scripts principais (`01_ingestao`, `03_duplicatas`, `04_ausentes`, `05_padronizacao` e `06_validacao_geo`).
- Os módulos `config.py`, `params.py` e `prov.py` e os arquivos SQL foram publicados em commits posteriores e não tinham soma registrada no banco; suas versões de execução não puderam ser identificadas.
- Os commits posteriores à tag acrescentam documentação, dependências, scripts auxiliares e consultas da revisão do trabalho.

Para comparar um script executado com a versão atual:

```powershell
git diff v1.0-execucao main -- 03_duplicatas.py
```

O README, as dependências e as pastas `sql/` e `auxiliares/` foram acrescentados depois da tag. Para reproduzir o trabalho, use a versão atual da branch `main`.
