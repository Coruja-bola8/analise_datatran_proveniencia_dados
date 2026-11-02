"""Lista as sessões abertas no banco e quem está bloqueando quem (somente leitura)."""
import pandas as pd
from sqlalchemy import create_engine, text
from config import *

SQL = """
SELECT pid, state, wait_event_type, wait_event,
       now() - query_start AS ha_quanto_tempo,
       pg_blocking_pids(pid) AS bloqueada_por,
       left(query, 90) AS consulta
FROM pg_stat_activity
WHERE datname = current_database() AND pid <> pg_backend_pid()
ORDER BY query_start
"""

pd.set_option("display.width", 250, "display.max_colwidth", 95, "display.max_columns", 20)
eng = create_engine(DB_URL)
with eng.connect() as conn:
    df = pd.read_sql(text(SQL), conn)
print(df.to_string(index=False) if len(df) else "Nenhuma outra sessão aberta.")