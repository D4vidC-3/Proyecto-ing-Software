"""Identidad por bytes dentro del almacenamiento local; nunca por nombre del candidato.

flock coordina los procesos de la API en Linux sin crear tablas ni ficheros de locks.
El bloqueo del directorio cubre la publicación; el del PDF cubre la generación.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import os
import re

from fastapi import HTTPException
from sqlalchemy import select
from app.models.entities import Candidate, Profile


def fingerprint(stream):
    stream.seek(0)
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    stream.seek(0)
    return digest


@contextmanager
def directory_lock(directory):
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(directory, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


@contextmanager
def document_lock(path):
    with path.open('rb') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield


def matching_document(db, directory, digest, preferred_id=None):
    """Preserva vínculos existentes; con duplicados antiguos elige el más antiguo.

No modifica ni fusiona ninguno. Un ID ya vinculado sigue apuntando a SU candidato.
"""
    if preferred_id and db.scalar(select(Profile.id).where(Profile.document_id == preferred_id)):
        return preferred_id
    matches = []
    for path in sorted(directory.glob('*.pdf')):
        if not re.fullmatch(r'[0-9a-f]{32}', path.stem):
            continue
        with path.open('rb') as stream:
            if fingerprint(stream) == digest:
                matches.append(path.stem)
    if not matches:
        return None
    linked = db.scalar(
        select(Profile.document_id).join(Candidate, Candidate.id == Profile.candidate_id)
        .where(Profile.document_id.in_(matches))
        .order_by(Candidate.created_at, Candidate.id)
    )
    return linked or matches[0]


def store_document(db, directory, temporary, copy):
    digest = fingerprint(temporary)
    with directory_lock(directory):
        existing = matching_document(db, directory, digest)
        if existing:
            return existing, digest, True
        # ID compatible con el contrato anterior; la comparación usa SHA-256 completo.
        document_id = digest[:32]
        destination = directory / f'{document_id}.pdf'
        if destination.exists():
            raise HTTPException(409, 'Conflicto de huella documental; no se reemplazó ningún archivo.')
        created = False
        try:
            with destination.open('xb') as output:
                created = True
                temporary.seek(0)
                copy(temporary, output)
        except BaseException:
            if created:
                destination.unlink(missing_ok=True)
            raise
        return document_id, digest, False
