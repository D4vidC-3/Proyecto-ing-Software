"use client";

import { useEffect, useState, useSyncExternalStore, type FormEvent } from "react";
import Dashboard from "./dashboard";
import { CvWorkflow } from "./cv-workflow";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [workflow] = useState(() => new CvWorkflow(API_URL));
  const state = useSyncExternalStore(workflow.subscribe, workflow.getSnapshot, workflow.getServerSnapshot);
  const [maxBytes, setMaxBytes] = useState<number | null>(null);
  const busy = ["uploading", "validating", "extracting"].includes(state.phase);
  const failed = ["rejected", "provider_error"].includes(state.phase);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}/api/v1/cv/limits`, { signal: controller.signal })
      .then((response) => response.ok ? response.json() : null)
      .then((data) => { if (!controller.signal.aborted && data?.max_size_bytes > 0) setMaxBytes(data.max_size_bytes); })
      .catch(() => { /* La carga sigue validando el límite en el servidor. */ });
    return () => { controller.abort(); workflow.cancel(); };
  }, [workflow]);

  function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void workflow.upload();
  }

  return (
    <main className="min-h-screen bg-slate-50 px-5 py-12 text-slate-900">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8">
          <h1 className="text-4xl font-bold">WORKINT</h1>
          <p className="mt-2 text-slate-600">Profile Manager · Demostración local con datos ficticios</p>
        </header>
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">1. Cargar y validar hoja de vida</h2>
          <p className="mt-2 text-sm text-slate-600">
            Selecciona un PDF con texto seleccionable.
            {maxBytes !== null && ` Límite configurado: ${maxBytes.toLocaleString("es-CO")} bytes (${(maxBytes / 1024 / 1024).toLocaleString("es-CO")} MiB).`}
            {" "}WORKINT no incluye OCR: un PDF en blanco o con solo imágenes no permite generar un perfil con IA.
          </p>
          <form onSubmit={handleUpload}>
            <input type="file" accept=".pdf,application/pdf" aria-label="Seleccionar hoja de vida PDF"
              onChange={(event) => workflow.select(event.target.files?.[0] ?? null)}
              className="mt-5 block w-full rounded-lg border border-slate-300 p-3" />
            <button type="submit" disabled={!state.file || busy}
              className="mt-5 rounded-lg bg-blue-700 px-5 py-3 font-medium text-white disabled:opacity-50">
              {["uploading", "validating"].includes(state.phase) ? "Cargando y validando documento..." : "Cargar documento"}
            </button>
          </form>
          {state.message && <p role={failed ? "alert" : "status"} className={`mt-4 text-sm ${failed ? "text-red-800" : "text-slate-700"}`}>{state.message}</p>}
          {failed && <p className="mt-2 text-sm">Puedes cargar otro PDF con texto seleccionable o usar <a href="#perfil-guardado" className="underline">Crear perfil manual</a>. No se generó un nuevo perfil.</p>}
          {state.document && (
            <div className="mt-5 rounded-lg bg-slate-100 p-4 text-sm">
              <p><strong>Archivo validado:</strong> {state.document.filename}</p>
              <p className="mt-1 break-all"><strong>Documento:</strong> {state.document.document_id}</p>
              <p className="mt-1"><strong>Texto útil:</strong> {state.document.characters} caracteres</p>
            </div>
          )}
        </section>
        {state.document?.processable && (
          <section className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">2. Generar perfil profesional</h2>
            <p className="mt-2 text-sm text-slate-600">El PDF ya pasó la validación local. Si tiene un perfil asociado, se muestra el guardado. Solo una extracción nueva o regeneración autorizada envía su texto a Groq.</p>
            <label className="mt-5 flex items-start gap-3 text-sm">
              <input type="checkbox" checked={state.consent} disabled={busy}
                onChange={(event) => workflow.setConsent(event.target.checked)} className="mt-1" />
              <span>Autorizo que el contenido de este CV de prueba sea enviado a Groq para generar mi perfil profesional.</span>
            </label>
            <button type="button" onClick={() => void workflow.generate()} disabled={!state.consent || busy}
              className="mt-5 rounded-lg bg-emerald-700 px-5 py-3 font-medium text-white disabled:opacity-50">
              {state.phase === "extracting" ? "Analizando hoja de vida..." : state.profile ? "Mostrar perfil guardado" : "Generar perfil con IA"}
            </button>
            {state.profile?.updated_at && (
              <button type="button" disabled={!state.consent || busy}
                className="mt-3 ml-3 rounded-lg border border-amber-700 px-4 py-3 text-amber-900 disabled:opacity-50"
                onClick={() => {
                  if (window.confirm("Regenerar reemplazará los datos del perfil guardado, incluidas tus correcciones. Se conservarán el candidato, sus postulaciones, historial y recordatorios. ¿Confirmas la regeneración con IA?")) {
                    void workflow.generate(true);
                  }
                }}>
                Regenerar con IA (reemplaza los datos)
              </button>
            )}
          </section>
        )}
        <Dashboard extractedCandidateId={state.profile?.candidate_id} cvOperationVersion={state.version} />
      </div>
    </main>
  );
}
