"""Escenarios en SQLite temporal. Los modelos de extracción son dobles de prueba."""
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import func, select, inspect
from sqlalchemy.orm import Session

import main
from app.config import BACKEND_DIR, check_database, resolve_database_url
from app.models.candidate_profile import CandidateProfile
from app.models.entities import Candidate, Profile, Vacancy, Application, Reminder, AgentLog
from app.services.applications import TRANSITIONS
from app.services.matching import score, WEIGHTS
from app.services.vacancies import ingest, normalize_records, DATASET

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / 'backend/app/data/vacancies_escenarios.json'
FIXTURES = json.loads((ROOT / 'docs/demo_escenarios/perfiles_ficticios.json').read_text())
client = TestClient(main.app)


@pytest.fixture
def scenarios(database):
    with Session(database) as db:
        assert ingest(db, SCENARIOS) == 10
        db.commit()
    return database


def test_new_migrated_database_empty(database):
    assert {'candidates', 'profiles', 'vacancies', 'applications', 'reminders', 'agent_logs', 'alembic_version'} <= set(inspect(database).get_table_names())
    with Session(database) as db:
        for model in (Candidate, Profile, Vacancy, Application, Reminder, AgentLog):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_scenario_ingestion_exact_and_idempotent(scenarios):
    with Session(scenarios) as db:
        assert ingest(db, SCENARIOS) == 10
        db.commit()
        assert set(db.scalars(select(Vacancy.id))) == {f'escenarios-v{i:02}' for i in range(1, 11)}
        assert db.scalar(select(func.count()).select_from(Candidate)) == 0
        assert db.scalar(select(func.count()).select_from(AgentLog).where(AgentLog.candidate_id.is_not(None))) == 0
    data = client.get('/api/v1/vacancies').json()
    assert len(data) == 10 and all(v['source'] == 'demo' for v in data)
    for v in data:
        assert client.get('/api/v1/vacancies/'+v['id']).status_code == 200


@pytest.mark.parametrize('item', FIXTURES, ids=lambda x: x['candidate'])
def test_matching_and_pdf(item):
    records = normalize_records({'records': json.loads(SCENARIOS.read_text())})['normalized']
    p = CandidateProfile.model_validate(item['profile'])
    ranking = sorted((score(p,v) for v in records), key=lambda r: -r['score'])
    assert ranking[0]['vacancy']['id'] == item['target_vacancy']
    assert ranking[0]['score'] >= 90
    assert ranking[0]['score'] > ranking[1]['score']
    assert sum(r['score'] >= 90 for r in ranking) == 1
    assert WEIGHTS == dict(skills=45, role=20, work_mode=15, location=10, salary=10)
    # El nombre y las empresas no pueden alterar la puntuación.
    changed = p.model_copy(update={'name':'Otro nombre', 'work_experience':[], 'years_experience':50})
    assert [score(changed,v)['score'] for v in records] == [score(p,v)['score'] for v in records]
    pdf = PdfReader(ROOT/'docs/demo_escenarios/cvs'/item['pdf'])
    assert len(pdf.pages) == 1
    text = pdf.pages[0].extract_text()
    assert p.name in text and p.email in text and p.target_role in text
    assert all(s in text for s in p.skills)
    assert 'FICTICIO' in text


@pytest.mark.parametrize('item', FIXTURES, ids=lambda x: x['candidate'])
def test_pdf_to_hired_with_mock_and_restart(scenarios, item, tmp_path, monkeypatch):
    monkeypatch.setattr(main,'UPLOAD_DIR',tmp_path/'uploads')
    extractor = Mock(return_value=CandidateProfile.model_validate(item['profile']))
    monkeypatch.setattr(main,'extract_candidate_profile',extractor)
    pdf = ROOT/'docs/demo_escenarios/cvs'/item['pdf']
    uploaded = client.post('/api/v1/cv/upload',files={'file':(pdf.name,pdf.read_bytes(),'application/pdf')})
    assert uploaded.status_code == 201
    doc = uploaded.json()['document_id']
    assert client.post(f'/api/v1/cv/{doc}/profile', json={'consent_external_processing':False}).status_code == 403
    extractor.assert_not_called()
    generated = client.post(f'/api/v1/cv/{doc}/profile',json={'consent_external_processing':True})
    assert generated.status_code == 200
    cid = generated.json()['candidate_id']
    assert item['profile']['name'] in extractor.call_args.args[0]
    result = client.get(f'/api/v1/profiles/{cid}/recommendations').json()
    assert len(result)==10 and result[0]['vacancy']['id']==item['target_vacancy']
    payload = dict(candidate_id=cid,vacancy_id=item['target_vacancy'],confirmed=False)
    assert client.post('/api/v1/applications',json=payload).status_code==403
    payload['confirmed']=True
    applied = client.post('/api/v1/applications',json=payload)
    assert applied.status_code==201
    app=applied.json();aid=app['id']
    assert app['status']=='postulado' and app['evidence']['confirmed'] is True
    assert client.post('/api/v1/applications',json=payload).status_code==409
    evidence=app['evidence']
    for status in ('en_revision','entrevista','contratado'):
        response=client.patch(f'/api/v1/applications/{aid}',json={'status':status})
        assert response.status_code==200
        assert response.json()['status']==status and response.json()['evidence']==evidence
    assert response.json()['allowed_transitions']==[]
    assert 'terminado con contratación' in response.json()['next_step']
    reminders=client.get(f'/api/v1/profiles/{cid}/reminders').json()
    assert len(reminders)==1 and not reminders[0]['pending']
    logs=client.get(f'/api/v1/profiles/{cid}/activity').json()
    changes=[x['reason'] for x in logs if x['action']=='cambio_estado']
    assert len(changes)==3
    assert 'entrevista → contratado' in changes[-1]
    assert {x['agent'] for x in logs} >= {'perfil','vacantes','postulacion','seguimiento'}
    # Nuevo intérprete carga de nuevo la API y su motor, contra la MISMA base temporal.
    env=os.environ.copy()
    env.update(WORKINT_DATABASE_URL=str(scenarios.url), WORKINT_UPLOAD_DIR=str(tmp_path/'uploads'), GROQ_API_KEY='')
    program='''import json,sys
from fastapi.testclient import TestClient
import main
with TestClient(main.app) as c:
 cid=sys.argv[1]
 print(json.dumps({"applications":c.get(f"/api/v1/profiles/{cid}/applications").json(),"reminders":c.get(f"/api/v1/profiles/{cid}/reminders").json(),"activity":c.get(f"/api/v1/profiles/{cid}/activity").json()}))
'''
    restarted=subprocess.run([sys.executable,'-c',program,cid],cwd=ROOT/'backend',env=env,text=True,capture_output=True,check=True)
    saved=json.loads(restarted.stdout.strip().splitlines()[-1])
    assert saved['applications'][0]['status']=='contratado'
    assert saved['applications'][0]['evidence']==evidence
    assert saved['reminders'][0]['pending'] is False
    assert len(saved['activity'])==len(logs)


@pytest.mark.parametrize('current', list(TRANSITIONS))
@pytest.mark.parametrize('requested', list(TRANSITIONS))
def test_all_state_transitions(scenarios,current,requested):
    cid=client.post('/api/v1/profiles',json=FIXTURES[0]['profile']).json()['candidate_id']
    app=client.post('/api/v1/applications',json=dict(candidate_id=cid,vacancy_id='escenarios-v01',confirmed=True)).json()
    aid=app['id']
    path={'postulado':[], 'en_revision':['en_revision'], 'entrevista':['en_revision','entrevista'], 'contratado':['en_revision','entrevista','contratado'], 'descartado':['descartado']}[current]
    for status in path:
        assert client.patch(f'/api/v1/applications/{aid}',json={'status':status}).status_code==200
    response=client.patch(f'/api/v1/applications/{aid}',json={'status':requested})
    allowed={'postulado':{'en_revision','descartado'}, 'en_revision':{'entrevista','descartado'}, 'entrevista':{'contratado','descartado'}, 'contratado':set(), 'descartado':set()}
    assert response.status_code==(200 if requested in allowed[current] else 409)
    saved=client.get(f'/api/v1/profiles/{cid}/applications').json()[0]
    expected=requested if requested in allowed[current] else current
    assert saved['status']==expected
    reminder=client.get(f'/api/v1/profiles/{cid}/reminders').json()[0]
    assert reminder['pending']==(expected not in {'contratado','descartado'})


def test_configuration_independent_of_cwd_and_historical_guard(monkeypatch,tmp_path):
    monkeypatch.chdir(tmp_path)
    assert resolve_database_url('sqlite:///workint_escenarios.db') == f'sqlite:///{BACKEND_DIR / "workint_escenarios.db"}'
    monkeypatch.setenv('WORKINT_SCENARIOS','1')
    with pytest.raises(RuntimeError,match='histórica'):
        check_database('sqlite:///workint.db')
    assert str(tmp_path) in check_database(f'sqlite:///{tmp_path / "test.db"}')


def test_scenarios_reject_historical_dataset(tmp_path):
    from alembic import command
    from alembic.config import Config
    from app.database import make_engine
    url=f'sqlite:///{tmp_path / "workint_escenarios.db"}'
    config=Config(str(ROOT/'backend/alembic.ini'));config.attributes['database_url']=url
    command.upgrade(config,'head')
    engine=make_engine(url)
    try:
        with Session(engine) as db:
            with pytest.raises(ValueError,match='exclusivamente'):
                ingest(db,DATASET)
            assert db.scalar(select(func.count()).select_from(Vacancy))==0
    finally:
        engine.dispose()
