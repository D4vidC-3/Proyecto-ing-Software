"""Aceptación de carga y generación: almacenamiento y proveedor aislados."""
from io import BytesIO
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from groq import APIConnectionError
from PIL import Image
from pypdf import PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from sqlalchemy import select, func
from sqlalchemy.orm import Session

import main
from app.models.entities import Candidate, Profile, AgentLog
from app.models.candidate_profile import CandidateProfile
from app.services.pdf_extractor import extract_pdf_text, PDFValidationError
from app.services.profile_gaps import profile_gaps

client = TestClient(main.app)


def pdf_bytes(kind='text'):
    buffer = BytesIO()
    if kind in ('blank','encrypted'):
        writer=PdfWriter();writer.add_blank_page(width=612,height=792)
        if kind=='encrypted': writer.encrypt('test-password')
        writer.write(buffer)
    else:
        pdf=canvas.Canvas(buffer)
        if kind=='image':
            pdf.drawImage(ImageReader(Image.new('RGB',(20,20),'white')),72,700,width=80,height=80)
        else:
            pdf.drawString(72,750,'Sofia de prueba Python' if kind=='text' else '  ... ---  ')
        pdf.save()
    return buffer.getvalue()


def upload(data, name='cv.pdf', mime='application/pdf'):
    return client.post('/api/v1/cv/upload',files={'file':(name,data,mime)})


CASES=[
    ('blank','cv.pdf','application/pdf',422,'No se encontró texto útil'),
    ('image','cv.pdf','application/pdf',422,'No se encontró texto útil'),
    ('punctuation','cv.pdf','application/pdf',422,'No se encontró texto útil'),
    ('empty','cv.pdf','application/pdf',422,'vacío'),
    ('corrupt','cv.pdf','application/pdf',422,'dañado'),
    ('png','imagen.png','image/png',415,'Formato no permitido'),
    ('txt','cv.txt','text/plain',415,'Formato no permitido'),
    ('png','renombrado.pdf','application/pdf',422,'cabecera PDF válida'),
    ('encrypted','cv.pdf','application/pdf',422,'contraseña'),
]


def content(kind):
    return {'empty':b'','corrupt':b'%PDF-1.7\nINVALID','png':b'\x89PNG\r\n\x1a\n','txt':b'CV en texto'}.get(kind) if kind in {'empty','corrupt','png','txt'} else pdf_bytes(kind)


@pytest.mark.parametrize('kind,name,mime,status,message',CASES)
def test_reject_before_storage_and_without_groq(database,monkeypatch,kind,name,mime,status,message):
    provider=Mock();monkeypatch.setattr(main,'extract_candidate_profile',provider)
    before=set(main.UPLOAD_DIR.iterdir())
    result=upload(content(kind),name,mime)
    assert result.status_code==status
    assert message in result.json()['detail']
    assert 'document_id' not in result.json()
    assert set(main.UPLOAD_DIR.iterdir())==before
    provider.assert_not_called()
    with Session(database) as db:
        for model in (Candidate,Profile,AgentLog):
            assert db.scalar(select(func.count()).select_from(model))==0


@pytest.mark.parametrize('kind', ['blank','image','empty','corrupt','png','punctuation'])
@pytest.mark.parametrize('endpoint',['extract','profile'])
def test_direct_api_revalidates_existing_files_without_deleting(monkeypatch,kind,endpoint):
    provider=Mock();monkeypatch.setattr(main,'extract_candidate_profile',provider)
    path=main.UPLOAD_DIR/('a'*32+'.pdf');raw=content(kind);path.write_bytes(raw)
    result=client.post(f'/api/v1/cv/{"a"*32}/{endpoint}',json={'consent_external_processing':True})
    assert result.status_code==422
    provider.assert_not_called()
    assert path.read_bytes()==raw
    assert client.get('/api/v1/profiles').json()==[]


def test_limits_shared_by_upload_and_direct_api(monkeypatch):
    provider=Mock();monkeypatch.setattr(main,'extract_candidate_profile',provider)
    monkeypatch.setattr(main,'MAX_FILE_SIZE',100)
    assert client.get('/api/v1/cv/limits').json()=={'max_size_bytes':100}
    raw=pdf_bytes();assert len(raw)>100
    response=upload(raw)
    assert response.status_code==413 and '100 bytes' in response.json()['detail']
    assert not list(main.UPLOAD_DIR.iterdir())
    (main.UPLOAD_DIR/('b'*32+'.pdf')).write_bytes(raw)
    for endpoint in ('extract','profile'):
        assert client.post(f'/api/v1/cv/{"b"*32}/{endpoint}',json={'consent_external_processing':True}).status_code==413
    provider.assert_not_called()


def test_valid_and_incomplete_pdf_consent_and_gaps(monkeypatch):
    provider=Mock(return_value=CandidateProfile(name='Sofia de prueba',skills=['Python']))
    monkeypatch.setattr(main,'extract_candidate_profile',provider)
    uploaded=upload(pdf_bytes());assert uploaded.status_code==201
    data=uploaded.json();assert data['status']=='ready' and data['processable'] is True and data['characters']>0
    doc=data['document_id']
    assert client.post(f'/api/v1/cv/{doc}/profile',json={'consent_external_processing':False}).status_code==403
    provider.assert_not_called()
    generated=client.post(f'/api/v1/cv/{doc}/profile',json={'consent_external_processing':True})
    assert generated.status_code==200
    provider.assert_called_once()
    saved=client.get('/api/v1/profiles/'+generated.json()['candidate_id']).json()
    missing={g['field']:g for g in saved['gaps'] if g['missing']}
    assert {'languages','contact','target_role','education','experience','work_modes','salary','availability'}<=missing.keys()
    assert missing['languages']['importance']=='opcional'
    assert saved['profile']['years_experience'] is None
    assert saved['profile']['languages']==[]
    assert client.put('/api/v1/profiles/'+saved['candidate_id'],json=saved['profile']).status_code==200


def test_previous_profile_preserved_after_bad_upload(monkeypatch):
    provider=Mock();monkeypatch.setattr(main,'extract_candidate_profile',provider)
    saved=client.post('/api/v1/profiles',json={'name':'Sofía Vega','years_experience':0}).json()
    assert upload(pdf_bytes('blank')).status_code==422
    assert client.get('/api/v1/profiles/'+saved['candidate_id']).json()==saved
    provider.assert_not_called()


@pytest.mark.parametrize('years,missing',[(None,True),(0,False),(3,False)])
def test_optional_languages_and_unknown_experience(years,missing):
    gaps={g['field']:g for g in profile_gaps(CandidateProfile(years_experience=years))}
    assert gaps['experience']['missing']==missing
    assert gaps['languages']['missing'] and gaps['languages']['importance']=='opcional'
    filled={g['field']:g for g in profile_gaps(CandidateProfile(languages=['Español']))}
    assert not filled['languages']['missing']
    assert client.post('/api/v1/profiles',json={'years_experience':years,'languages':[]}).status_code==201


@pytest.mark.parametrize('error,status',[(RuntimeError('not configured'),503),(APIConnectionError(request=httpx.Request('POST','https://example.com')),502)])
def test_provider_failure_retry_without_fake_profile(monkeypatch,error,status):
    provider=Mock(side_effect=error);monkeypatch.setattr(main,'extract_candidate_profile',provider)
    doc=upload(pdf_bytes()).json()['document_id']
    path=f'/api/v1/cv/{doc}/profile'
    result=client.post(path,json={'consent_external_processing':True})
    assert result.status_code==status
    assert 'No se generó un nuevo perfil' in result.json()['detail']
    assert client.get('/api/v1/profiles').json()==[]
    assert (main.UPLOAD_DIR/f'{doc}.pdf').exists()
    provider.side_effect=None;provider.return_value=CandidateProfile(name='Recuperado')
    assert client.post(path,json={'consent_external_processing':True}).status_code==200
    assert len(client.get('/api/v1/profiles').json())==1


def test_partial_write_cleans_only_new_file(monkeypatch):
    previous=main.UPLOAD_DIR/'preexistente.pdf';previous.write_bytes(b'preservar')
    def fail(source,target):
        target.write(b'partial')
        raise OSError('simulated disk failure')
    monkeypatch.setattr(main,'copyfileobj',fail)
    with pytest.raises(OSError,match='simulated'):
        upload(pdf_bytes())
    assert list(main.UPLOAD_DIR.iterdir())==[previous]
    assert previous.read_bytes()==b'preservar'


def test_parser_exception_is_controlled(monkeypatch,tmp_path):
    path=tmp_path/'broken.pdf';path.write_bytes(b'%PDF-1.7\ninvalid')
    monkeypatch.setattr('app.services.pdf_extractor.PdfReader',Mock(side_effect=KeyError('/Root')))
    with pytest.raises(PDFValidationError,match='dañado'):
        extract_pdf_text(path)
