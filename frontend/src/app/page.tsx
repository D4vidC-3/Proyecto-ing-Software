
"use client";

import { useState, type FormEvent } from "react";

type UploadResult = {
  message: string;
  document_id: string;
  filename: string;
  size_bytes: number;
};

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<UploadResult | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || loading) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setMessage("Selecciona un archivo PDF válido.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setMessage("El archivo supera el límite de 5 MB.");
      return;
    }

    setLoading(true);
    setMessage("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/cv/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "No se pudo cargar el archivo."
        );
      }

      setResult(data);
      setMessage("Hoja de vida cargada correctamente.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Error al comunicarse con el servidor."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-16 text-slate-900">
      <div className="mx-auto max-w-xl">
        <h1 className="text-4xl font-bold">WORKINT</h1>
        <p className="mt-2 text-slate-600">
          Tu asistente de empleabilidad
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-8 rounded-xl border border-slate-200 bg-white p-8 shadow-sm"
        >
          <h2 className="text-xl font-semibold">
            Carga tu hoja de vida
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Selecciona un PDF de prueba de máximo 5 MB.
          </p>

          <input
            type="file"
            accept=".pdf,application/pdf"
            aria-label="Seleccionar hoja de vida PDF"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setResult(null);
              setMessage("");
            }}
            className="mt-6 block w-full rounded-lg border p-3"
          />

          <button
            type="submit"
            disabled={!file || loading}
            className="mt-6 w-full rounded-lg bg-blue-700 px-5 py-3 font-medium text-white disabled:opacity-50"
          >
            {loading ? "Cargando..." : "Cargar documento"}
          </button>

          {message && (
            <p role="status" className="mt-4 text-sm">
              {message}
            </p>
          )}

          {result && (
            <div className="mt-4 rounded-lg bg-slate-100 p-4 text-sm">
              <p>Archivo: {result.filename}</p>
              <p>ID: {result.document_id}</p>
              <p>Tamaño: {result.size_bytes} bytes</p>
            </div>
          )}
        </form>
      </div>
    </main>
  );
}
