"""Repetición y concurrencia exclusivamente con SQLite/PDF temporales y proveedor falso."""
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from sqlalchemy import select, func
from sqlalchemy.orm import Session

import main
from app.models.candidate_profile import CandidateProfile
from app.models.entities import Candidate, Profile, AgentLog
from app.repository import save_profile
from app.services.vacancies import ingest

client=TestClient(main.app)
ROOT=Path(__file__).resolve().parents[2]


def pdf(text='CV de prueba Python'):
    b=BytesIO();c=canvas.Canvas(b);c.drawString(72,750,text);c.save();return b.getvalue()


def upload(raw,name='cv.pdf'):
    return client.post('/api/v1/cv/upload',files={'file':(name,raw,'application/pdf')})


def generate(doc,**extra):
    return client.post(f'/api/v1/cv/{doc}/profile',json={'consent_external_processing':True,**extra})


@pytest.fixture
def provider(monkeypatch):
    fake=Mock(return_value=CandidateProfile(name='Nombre repetido',skills=['Python']))
    monkeypatch.setattr(main,'extract_candidate_profile',fake)
    return fake


def test_repeated_generation_reupload_and_new_client_preserve_edits(database,provider):
    raw=pdf();first=upload(raw).json();created=generate(first['document_id']).json();cid=created['candidate_id']
    assert client.put(f'/api/v1/profiles/{cid}',json={'name':'Editado','skills':['SQL']}).status_code==200
    again=generate(first['document_id']).json()
    assert again['candidate_id']==cid and again['profile']['name']=='Editado' and again['status']=='reused'
    # Nuevo cliente tras recarga; ningún document_id en memoria del cliente.
    with TestClient(main.app) as reloaded:
        reuploaded=reloaded.post('/api/v1/cv/upload',files={'file':('otro-nombre.pdf',raw,'application/pdf')}).json()
    assert reuploaded['document_id']==first['document_id'] and reuploaded['sha256']==first['sha256']
    assert reuploaded['saved_profile']['candidate_id']==cid
    assert reuploaded['saved_profile']['profile']['skills']==['SQL']
    assert provider.call_count==1 and len(list(main.UPLOAD_DIR.glob('*.pdf')))==1
    with Session(database) as db:
        assert db.scalar(select(func.count()).select_from(Candidate))==1
        assert db.scalar(select(func.count()).select_from(Profile))==1


def test_same_name_different_bytes_is_not_identity(provider):
    a=upload(pdf('Python')).json();b=upload(pdf('Java')).json()
    assert a['document_id']!=b['document_id'] and a['sha256']!=b['sha256']
    pa=generate(a['document_id']).json();pb=generate(b['document_id']).json()
    assert pa['profile']['name']==pb['profile']['name']
    assert pa['candidate_id']!=pb['candidate_id']


def test_simultaneous_reupload_and_generation(database,provider):
    raw=pdf();barrier=threading.Barrier(4)
    def work(_):
        barrier.wait(timeout=10)
        uploaded=upload(raw)
        assert uploaded.status_code==201
        generated=generate(uploaded.json()['document_id'])
        assert generated.status_code==200
        return uploaded.json()['document_id'],generated.json()['candidate_id']
    def slow(_):
        time.sleep(.1);return CandidateProfile(name='Concurrente')
    provider.side_effect=slow
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(work,range(4)))
    assert len(set(results))==1 and provider.call_count==1
    assert len(list(main.UPLOAD_DIR.glob('*.pdf')))==1
    with Session(database) as db:
        assert db.scalar(select(func.count()).select_from(Candidate))==1
        actions = list(db.scalars(select(AgentLog.action)))
        assert actions.count('crear') == 1
        assert actions.count('extraer_cv') == 1
        assert actions.count('reutilizar') == 3
        assert len(actions) == 5


def test_simultaneous_generation_across_api_processes(database,tmp_path):
    doc=upload(pdf()).json()['document_id']
    env=os.environ.copy();env.update(WORKINT_DATABASE_URL=str(database.url),WORKINT_UPLOAD_DIR=str(main.UPLOAD_DIR),GROQ_API_KEY='')
    counter=tmp_path/'calls.txt'
    program='''import json,sys,time
from pathlib import Path
from fastapi.testclient import TestClient
import main
from app.models.candidate_profile import CandidateProfile
from groq._base_client import SyncAPIClient
SyncAPIClient.request=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError("Groq real prohibido"))
def fake(text):
 with Path(sys.argv[2]).open("a") as f:f.write("call\\n")
 time.sleep(.2)
 return CandidateProfile(name="Proceso simulado")
main.extract_candidate_profile=fake
with TestClient(main.app) as c:
 r=c.post(f"/api/v1/cv/{sys.argv[1]}/profile",json={"consent_external_processing":True})
 print(json.dumps({"status":r.status_code,"body":r.json()}))
'''
    def work(_):
        result=subprocess.run([sys.executable,'-c',program,doc,str(counter)],cwd=ROOT/'backend',env=env,capture_output=True,text=True,check=True,timeout=30)
        return json.loads(result.stdout.strip().splitlines()[-1])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(work,range(2)))
    assert [r['status'] for r in results]==[200,200]
    assert results[0]['body']['candidate_id']==results[1]['body']['candidate_id']
    assert counter.read_text().splitlines()==['call']


def test_existing_duplicates_are_preserved(database,provider):
    raw=pdf();ids=['a'*32,'b'*32];candidates=[]
    for doc in ids:(main.UPLOAD_DIR/f'{doc}.pdf').write_bytes(raw)
    with Session(database) as db:
        for i,doc in enumerate(ids):
            record=save_profile(db,CandidateProfile(name=f'Existente {i}'),'groq',doc)
            db.commit();candidates.append(record.candidate_id)
    data=upload(raw).json()
    assert data['document_id']==ids[0]
    assert data['saved_profile']['candidate_id']==candidates[0]
    assert generate(ids[1]).json()['candidate_id']==candidates[1]
    assert len(client.get('/api/v1/profiles').json())==2
    assert all((main.UPLOAD_DIR/f'{doc}.pdf').read_bytes()==raw for doc in ids)
    provider.assert_not_called()


def test_explicit_regeneration_preserves_relations_and_protects_edits(database,provider):
    doc=upload(pdf()).json()['document_id'];created=generate(doc).json();cid=created['candidate_id']
    with Session(database) as db:
        ingest(db,ROOT/'backend/app/data/vacancies_escenarios.json');db.commit()
    application=client.post('/api/v1/applications',json={'candidate_id':cid,'vacancy_id':'escenarios-v01','confirmed':True}).json()
    app_before=client.get(f'/api/v1/profiles/{cid}/applications').json()
    reminders=client.get(f'/api/v1/profiles/{cid}/reminders').json()
    logs=client.get(f'/api/v1/profiles/{cid}/activity').json()
    assert generate(doc,regenerate=True).status_code==409
    assert provider.call_count==1
    provider.return_value=CandidateProfile(name='Regenerado')
    regenerated=generate(doc,regenerate=True,expected_updated_at=created['updated_at'])
    assert regenerated.status_code==200 and regenerated.json()['candidate_id']==cid
    assert regenerated.json()['status']=='regenerated'
    assert client.get(f'/api/v1/profiles/{cid}/applications').json()==app_before
    assert client.get(f'/api/v1/profiles/{cid}/reminders').json()==reminders
    updated_logs=client.get(f'/api/v1/profiles/{cid}/activity').json()
    assert updated_logs[:len(logs)] == logs
    assert {l['action'] for l in updated_logs[len(logs):]} == {'regenerar', 'extraer_cv'}
    # Una segunda solicitud con la misma versión no regenera ni pisa datos.
    assert generate(doc,regenerate=True,expected_updated_at=created['updated_at']).status_code==409
    assert provider.call_count==2
    # Edición durante el proveedor: debe ganar la edición, no una respuesta tardía.
    def edit_during_extraction(_):
        assert client.put(f'/api/v1/profiles/{cid}',json={'name':'Edición concurrente'}).status_code==200
        return CandidateProfile(name='No debe sobrescribir')
    provider.side_effect=edit_during_extraction
    response=generate(doc,regenerate=True,expected_updated_at=regenerated.json()['updated_at'])
    assert response.status_code==409
    assert client.get(f'/api/v1/profiles/{cid}').json()['profile']['name']=='Edición concurrente'
    assert client.get(f'/api/v1/profiles/{cid}/applications').json()==app_before
    assert application['candidate_id']==cid
