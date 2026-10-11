-- Distinguibilidade (Seção 3.3 / 4.4): origem da coordenada obtida SÓ a partir do registro de modificações
CREATE OR REPLACE VIEW clean.v_coord_origem AS
SELECT c.rid, c.latitude_num, c.longitude_num,
  CASE
    WHEN EXISTS (SELECT 1 FROM prov.modificacao m WHERE m.rid = c.rid AND m.operacao = 'IMPUTACAO'
                 AND m.campo IN ('latitude','longitude')) THEN 'DERIVADA'
    WHEN EXISTS (SELECT 1 FROM prov.modificacao m WHERE m.rid = c.rid AND m.operacao = 'MARCACAO'
                 AND m.campo = 'coord_status' AND m.valor_novo = 'IRRECUPERAVEL') THEN 'IRRECUPERAVEL'
    ELSE 'OBSERVADA'
  END AS origem_coord,
  EXISTS (SELECT 1 FROM prov.modificacao m WHERE m.rid = c.rid AND m.campo = 'validacao_geo') AS reprovada_validacao
FROM clean.datatran c;
