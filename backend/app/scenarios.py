"""Inspección de solo lectura de la base activa de escenarios."""
import json
import sqlite3
from pathlib import Path
from sqlalchemy.engine import make_url
from app.config import DATABASE_URL, UPLOAD_DIR, VACANCIES_PATH, check_database


def report():
    print(f'Base efectiva: {check_database(DATABASE_URL)}')
    path = Path(make_url(DATABASE_URL).database).resolve()
    if path.name != 'workint_escenarios.db':
        raise RuntimeError('Se esperaba workint_escenarios.db; operación detenida')
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
        counts = {t:db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ('candidates','profiles','vacancies','applications','reminders')}
        counts['eventos_candidatos'] = db.execute('SELECT count(*) FROM agent_logs WHERE candidate_id IS NOT NULL').fetchone()[0]
        counts['eventos_tecnicos'] = db.execute('SELECT count(*) FROM agent_logs WHERE candidate_id IS NULL').fetchone()[0]
        counts['alembic_version'] = db.execute('SELECT version_num FROM alembic_version').fetchone()[0]
        counts['vacancy_ids'] = [r[0] for r in db.execute('SELECT id FROM vacancies ORDER BY id')]
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
    print(f'Directorio de nuevos PDF: {UPLOAD_DIR}')
    print(f'Dataset configurado: {VACANCIES_PATH}')
    print(json.dumps(counts,ensure_ascii=False,indent=2))
    return counts


if __name__ == '__main__':
    report()
