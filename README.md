# Proveniência de dados no DATATRAN (acidentes2017-2025_todas_causas_tipos)
O repositório reúne os scripts numerados na ordem de execução, o esquema SQL, os arquivos de parâmetros, a lista de dependências com versões.

Para reproduzir o trabalho, criam-se o banco e o esquema, obtêm-se os nove arquivos anuais e as duas bases auxiliares, conferem-se as somas SHA-256 dos arquivos anuais com a Tabela 1 e executam-se os scripts na ordem deste README.

As credenciais do banco ficam em um arquivo .env fora do repositório. Os dados e as bases auxiliares não são distribuídos no repositório.

Antes de iniciar configure seu usuario e senha Postgre
Crie o arquivo .env usando o .env.example como modelo e use suas credenciais do banco de dados Postgre.
Ordem de execução:
1. Faça o download da malha rodoviária no site do IBGE e DNIT (IBGE, edição 2025; DNIT, versão SNV_202607A) e cole na pasta datatran_prov\dados\aux -
2. Faça o download dos dados abertos da PRF pelo portal https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf
3. Selecione os anos que serão analisados e cole todos arquivos na pasta datatran_prov\dados\csv
4. `01_ingestao.py`                      Etapa 1: inserir os dados
5. `python 03_duplicatas.py --refazer`   Etapa 2: duplicatas exatas (linha idêntica)
6. `python 04_ausentes.py`               Etapa 3: 'NA'/'N/A' -> NULL; imputação de coordenadas (se houver ausência); 'Ignorado'
7. `python 05_padronizacao.py`           Etapa 4: padronização (+ mapas/<campo>.csv, opcional)
8. `python 06_validacao_geo.py`          Etapa 5: validação + clean.acidente (precisa de dados/aux: IBGE e DNIT)
9. `python 07_resultados.py`             números do Capítulo 4 -> saida/resultados_cap4.md
10. `python 08_reversibilidade.py`        teste empírico de reversibilidade

Para refazer desde a Etapa 4: `python 03_duplicatas.py --refazer` (apaga o log das etapas 2-5).
`params.py` sobrescreve parâmetros do `config.py`. O `config.py` continua com DB_URL, ANOS, PADRAO_ARQUIVO e caminhos IBGE/DNIT.
`mapas/causa_acidente.RASCUNHO.csv` é uma PROPOSTA a ser revisada pelo grupo; renomeie para `causa_acidente.csv` para aplicá-la.

DADOS
Hashes das bases auxiliares completos (SHA-256)
Arquivo	          SHA-256
BR_UF_2025.shp	  23A9B54FC2DBFBE46298D3152ED4CCFDB60F9E7F178B00C50526741ECBE142D7
BR_UF_2025.dbf	  4AAB0C0312C79F20D42ABF1FC4F3FBF6565CDA03E288FD82B033ECE18A018AF6
SNV_202607A.shp	  1247033F6234D44BBAE0F679167A187ED0D52ACE86F57196C3FC4E1445D534DB
SNV_202607A.dbf	  CF10B04114872670EC385243B2D6D65DEC8978B4A72E8368CE48EDBA4F95CEB0
