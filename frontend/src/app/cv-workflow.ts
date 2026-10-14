import type { CandidateProfile } from "./profile-types";

export type ReadyDocument = {
  document_id: string;
  filename: string;
  size_bytes: number;
  status: "ready";
  processable: true;
  characters: number;
  saved_profile?: GeneratedProfile | null;
};
export type GeneratedProfile = {
  document_id: string;
  candidate_id: string;
  profile: CandidateProfile;
  status?: "structured" | "reused" | "regenerated";
  updated_at?: string;
};
export type CvState = {
  version: number;
  file: File | null;
  phase: "idle" | "selected" | "uploading" | "validating" | "ready" | "extracting" | "generated" | "rejected" | "provider_error";
  document: ReadyDocument | null;
  profile: GeneratedProfile | null;
  consent: boolean;
  message: string;
};

const initialState: CvState = {
  version: 0, file: null, phase: "idle", document: null, profile: null,
  consent: false, message: "",
};

/** Una selección invalida todas las respuestas anteriores, incluso si abortar no las detiene. */
export class CvWorkflow {
  private state: CvState = initialState;
  private listeners = new Set<() => void>();
  private controller: AbortController | null = null;
  private version = 0;
  private baseUrl: string;
  private request: typeof fetch;

  constructor(baseUrl: string, request: typeof fetch = fetch) {
    this.baseUrl = baseUrl;
    // Evitar invocar fetch con la instancia del flujo como receptor de Window.
    this.request = (...args) => request(...args);
  }
  getSnapshot = () => this.state;
  getServerSnapshot = () => initialState;
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  };
  private publish(patch: Partial<CvState>) {
    this.state = { ...this.state, ...patch, version: this.version };
    this.listeners.forEach((listener) => listener());
  }
  cancel = () => {
    this.version += 1;
    this.controller?.abort();
    this.controller = null;
  };
  select(file: File | null) {
    this.cancel();
    this.publish({ ...initialState, file, phase: file ? "selected" : "idle",
      message: file ? "Archivo seleccionado. Todavía no se ha cargado ni validado." : "" });
  }
  setConsent(consent: boolean) {
    if (this.state.document && this.state.phase !== "extracting") this.publish({ consent });
  }
  private begin() {
    this.cancel();
    this.controller = new AbortController();
    return { version: this.version, signal: this.controller.signal };
  }
  private current(version: number) { return version === this.version; }

  async upload() {
    const file = this.state.file;
    if (!file || ["uploading", "validating", "extracting"].includes(this.state.phase)) return;
    const operation = this.begin();
    this.publish({ document: null, profile: null, consent: false, phase: "uploading", message: "Cargando y validando el PDF en el servidor..." });
    try {
      if (!file.name.toLowerCase().endsWith(".pdf") || (file.type && file.type !== "application/pdf")) {
        throw new Error("Formato no permitido. Selecciona un archivo PDF con texto seleccionable.");
      }
      if (file.size === 0) throw new Error("El archivo está vacío (0 bytes). Selecciona otro PDF.");
      const body = new FormData();
      body.append("file", file);
      const response = await this.request(`${this.baseUrl}/api/v1/cv/upload`, { method: "POST", body, signal: operation.signal });
      if (!this.current(operation.version)) return;
      this.publish({ phase: "validating" });
      const data = await response.json();
      if (!this.current(operation.version)) return;
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "No se pudo validar el PDF.");
      if (data.status !== "ready" || data.processable !== true || !(data.characters > 0) || !/^[0-9a-f]{32}$/.test(data.document_id ?? "")) {
        throw new Error("La carga no confirmó que el PDF tenga texto procesable. Vuelve a cargarlo.");
      }
      const saved = data.saved_profile as GeneratedProfile | null | undefined;
      if (saved && (saved.document_id !== data.document_id || !/^[0-9a-f]{32}$/.test(saved.candidate_id) || !saved.profile)) {
        throw new Error("El perfil guardado no corresponde al documento validado.");
      }
      this.publish({ phase: saved ? "generated" : "ready", document: data, profile: saved ?? null,
        message: saved ? "Este CV ya está registrado. Se muestra el perfil guardado, incluidas sus ediciones; no se llamó a la IA." : "PDF validado con texto útil. Disponible para generar un perfil después de tu consentimiento." });
    } catch (error) {
      if (!this.current(operation.version)) return;
      this.publish({ phase: "rejected", document: null, profile: null, consent: false,
        message: error instanceof Error ? error.message : "No fue posible cargar y validar el PDF. Reintenta o crea el perfil manualmente." });
    }
  }

  async generate(regenerate = false) {
    const document = this.state.document;
    if (!document || !this.state.consent || !["ready", "generated", "provider_error"].includes(this.state.phase)) return;
    const savedProfile = this.state.profile;
    if (regenerate && !savedProfile?.updated_at) return;
    const operation = this.begin();
    this.publish({ phase: "extracting", profile: null, message: regenerate ? "Regenerando con autorización explícita..." : "Consultando o generando el perfil del PDF validado..." });
    try {
      const response = await this.request(`${this.baseUrl}/api/v1/cv/${document.document_id}/profile`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ consent_external_processing: true,
          ...(regenerate ? { regenerate: true, expected_updated_at: savedProfile?.updated_at } : {}),
        }), signal: operation.signal,
      });
      const data = await response.json();
      if (!this.current(operation.version)) return;
      if (!response.ok) {
        if ([404, 413, 415, 422].includes(response.status)) {
          this.publish({ document: null, consent: false });
        }
        throw new Error(typeof data.detail === "string" ? data.detail : "El proveedor de IA falló. Puedes reintentar o crear el perfil manualmente.");
      }
      if (data.document_id !== document.document_id || !/^[0-9a-f]{32}$/.test(data.candidate_id ?? "") || !data.profile) {
        throw new Error("La respuesta de IA no corresponde al documento actual o no contiene un perfil válido. Puedes reintentar.");
      }
      this.publish({ phase: "generated", profile: data, message: data.status === "reused"
        ? "Se muestra el perfil guardado. Se conservaron sus ediciones y su candidato; no se llamó a la IA."
        : data.status === "regenerated" ? "Perfil regenerado explícitamente. Se conservaron el candidato, las postulaciones y el seguimiento."
        : "Se generó un perfil para el archivo seleccionado. Revisa los datos y los avisos de faltantes." });
    } catch (error) {
      if (!this.current(operation.version)) return;
      this.publish({ phase: this.state.document ? "provider_error" : "rejected", profile: this.state.document ? savedProfile : null,
        message: error instanceof Error ? error.message : "No fue posible generar el perfil. Puedes reintentar o crearlo manualmente." });
    }
  }
}
