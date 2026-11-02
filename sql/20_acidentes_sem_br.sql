SELECT (aux.br_int(c.br) IS NULL) AS sem_br, count(*) AS linhas,
       count(DISTINCT c.id) AS acidentes
FROM clean.geo_linha g JOIN clean.datatran c USING (rid)
WHERE g.validacao_geo = 'OK_SEM_GEOM_RODOVIA'
GROUP BY 1;

SELECT aux.br_int(c.br) AS br, count(*) AS linhas
FROM clean.geo_linha g JOIN clean.datatran c USING (rid)
WHERE g.validacao_geo = 'OK_SEM_GEOM_RODOVIA' AND aux.br_int(c.br) IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC;