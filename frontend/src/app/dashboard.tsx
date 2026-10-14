"use client";
import { createContext, useContext, useEffect, useRef, useState, type FormEvent } from "react";
import { salaryError } from "./profile-validation";
import { vacancyText } from "./vacancy-presentation";
import type {
  CandidateProfile,
  WorkExperience,
  Education,
} from "./profile-types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const ReadingProfile = createContext(false);
type Profile = {
  candidate_id: string;
  source: string;
  profile: CandidateProfile;
  gaps: {
    field: string;
    label: string;
    importance: string;
    missing: boolean;
  }[];
};
type Vacancy = {
  id: string;
  title: string;
  company: string;
  description: string;
  location: string | null;
  work_mode: string | null;
  contract_type: string | null;
  salary_min_cop: number | null;
  salary_max_cop: number | null;
  years_experience: number | null;
  required_skills: string[];
  desired_skills: string[];
  published_at: string;
  source: string;
};
type Recommendation = {
  vacancy: Vacancy;
  score: number;
  matched_skills: string[];
  missing_skills: string[];
  unknown: string[];
  components: {
    criterion: string;
    weight: number;
    points: number;
    known: boolean;
    reason: string;
  }[];
};
type ApplicationStatus = "postulado" | "en_revision" | "entrevista" | "contratado" | "descartado";

type Application = {
  id: string;
  vacancy: Vacancy;
  status: ApplicationStatus;
  simulation_id: string;
  is_current: boolean;
  hired_at: string | null;
  created_at: string;
  next_step: string;
  evidence: Record<string, unknown>;
  allowed_transitions: ApplicationStatus[];
};
type SimulationView = {
  current_id: string;
  occupied_vacancy_ids: string[];
  simulations: { id: string; created_at: string; active: boolean }[];
  hires: { application_id: string; candidate_name: string | null; vacancy_title: string; hired_at: string | null; simulation_id: string }[];
};
type Activity = {
  id: string;
  agent: string;
  action: string;
  created_at: string;
  reason: string;
  application_id: string | null;
  status: string;
  result_ref: string | null;
  operation_id: string | null;
  execution_context: {
    execution_mode?: string;
    provider?: string | null;
    configured_model?: string | null;
    effective_model?: string | null;
    provider_request_id?: string | null;
    metadata_status?: string;
  } | null;
};
type Reminder = {
  id: string;
  application_id: string;
  due_at: string;
  message: string;
  pending: boolean;
};
const empty = (): CandidateProfile => ({
  name: null,
  email: null,
  phone: null,
  location: null,
  professional_summary: null,
  target_role: null,
  years_experience: null,
  skills: [],
  languages: [],
  work_experience: [],
  education: [],
  preferences: {
    desired_roles: [],
    preferred_locations: [],
    work_modes: [],
    salary_min_cop: null,
    salary_max_cop: null,
    contract_type: null,
    availability: null,
  },
});
async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${API}/api/v1${path}`, {
    method,
    headers:
      body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Revisa los campos. No fue posible completar la operación.",
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
const money = (n: number | null) =>
  n === null ? "No informado" : `${n.toLocaleString("es-CO")} COP`;
const date = (s: string) =>
  new Date(
    s.endsWith("Z") || /[+-]\d\d:\d\d$/.test(s) ? s : `${s}Z`,
  ).toLocaleString("es-CO");
function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string | number | null;
  onChange: (v: string) => void;
  type?: string;
}) {
  const reading = useContext(ReadingProfile);
  if (reading) return <div className="text-sm"><p className="font-medium">{label}</p><p className="whitespace-pre-wrap">{value ?? "No informado"}</p></div>;
  return (
    <label className="grid gap-1 text-sm">
      {label}
      <input
        type={type}
        min={type === "number" ? 0 : undefined}
        step={type === "number" ? "any" : undefined}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-slate-300 p-2"
      />
    </label>
  );
}
function ListField({
  label,
  values,
  onChange,
}: {
  label: string;
  values: string[];
  onChange: (v: string[]) => void;
}) {
  // Local text preserves the comma while the user types a new entry.
  const [text, setText] = useState(values.join(", "));
  return (
    <Field
      label={`${label} (separar con comas)`}
      value={text}
      onChange={(v) => {
        setText(v);
        onChange(
          v
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
        );
      }}
    />
  );
}

export default function Dashboard({
  extractedCandidateId,
  cvOperationVersion = 0,
}: {
  extractedCandidateId?: string;
  cvOperationVersion?: number;
}) {
  const profileRequest = useRef(0);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [selected, setSelected] = useState<Profile | null>(null);
  const [draft, setDraft] = useState<CandidateProfile>(empty);
  const [editorKey, setEditorKey] = useState(0);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [preview, setPreview] = useState<Vacancy | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [dirty, setDirty] = useState(false);
  const [editing, setEditing] = useState(true);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "success" | "error">("idle");
  const saving = useRef(false);
  const [simulation, setSimulation] = useState<SimulationView | null>(null);
  const [newSimulationConfirm, setNewSimulationConfirm] = useState(false);
  const occupied = (id: string) => simulation?.occupied_vacancy_ids.includes(id) ?? false;

  async function loadCandidate(id: string) {
    const request = ++profileRequest.current;
    const [p, r, a, m, s] = await Promise.all([
      api<Profile>(`/profiles/${id}`),
      api<Recommendation[]>(`/profiles/${id}/recommendations`),
      api<Application[]>(`/profiles/${id}/applications`),
      api<Reminder[]>(`/profiles/${id}/reminders`),
      api<SimulationView>("/simulations"),
    ]);
    // La recomendación persiste un evento; leer actividad después evita omitirlo.
    const l = await api<Activity[]>(`/profiles/${id}/activity`);
    if (request !== profileRequest.current) return;
    setSelected(p);
    setSimulation(s);
    setDraft(p.profile);
    setEditorKey((k) => k + 1);
    setRecommendations(r);
    setApplications(a);
    setActivity(l);
    setReminders(m);
    setPreview(null);
    setConfirmed(false);
    setDeleteConfirm(false);
    setDirty(false);
    setEditing(false);
    setSaveState("idle");
  }
  useEffect(() => {
    let active = true;
    Promise.all([api<Profile[]>("/profiles"), api<Vacancy[]>("/vacancies"), api<SimulationView>("/simulations")])
      .then(([p, v, s]) => {
        if (active) {
          setProfiles(p);
          setVacancies(v);
          setSimulation(s);
        }
      })
      .catch((e) => {
        if (active) setMessage(e.message);
      });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    const request = ++profileRequest.current;
    if (!extractedCandidateId) return;
    let active = true;
    Promise.all([
      api<Profile>(`/profiles/${extractedCandidateId}`),
      api<Profile[]>("/profiles"),
    ])
      .then(([p, ps]) => {
        if (!active || request !== profileRequest.current) return;
        setSelected(p);
        setDraft(p.profile);
        setProfiles(ps);
        setEditorKey((k) => k + 1);
        setRecommendations([]);
        setApplications([]);
        setActivity([]);
        setReminders([]);
        setPreview(null);
        setDirty(false);
        setEditing(false);
        setSaveState("idle");
      })
      .catch((e) => {
        if (active) setMessage(e.message);
      });
    return () => {
      active = false;
    };
  }, [extractedCandidateId, cvOperationVersion]);
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setMessage("");
    try {
      await action();
    } catch (e) {
      setMessage(
        e instanceof Error ? e.message : "No fue posible conectar con la API.",
      );
    } finally {
      setBusy(false);
    }
  }
  function update<K extends keyof CandidateProfile>(
    key: K,
    value: CandidateProfile[K],
  ) {
    setDraft({ ...draft, [key]: value });
    setDirty(true);
    setPreview(null);
  }
  function preference<K extends keyof CandidateProfile["preferences"]>(
    key: K,
    value: CandidateProfile["preferences"][K],
  ) {
    update("preferences", { ...draft.preferences, [key]: value });
  }
  async function save(event: FormEvent) {
    event.preventDefault();
    if (saving.current) return;
    const error = salaryError(draft.preferences);
    if (error) {
      setSaveState("error");
      setMessage(error);
      return;
    }
    saving.current = true;
    const request = ++profileRequest.current;
    setBusy(true);
    setSaveState("saving");
    setMessage("Guardando perfil y preferencias…");
    try {
      const p = await api<Profile>(
        selected ? `/profiles/${selected.candidate_id}` : "/profiles",
        selected ? "PUT" : "POST",
        draft,
      );
      if (request !== profileRequest.current) return;
      setSelected(p);
      setDraft(p.profile);
      setEditorKey((k) => k + 1);
      setProfiles((ps) => [p, ...ps.filter((row) => row.candidate_id !== p.candidate_id)]);
      setDirty(false);
      setEditing(false);
      setRecommendations([]);
      setSaveState("success");
      setMessage("Perfil y preferencias guardados correctamente. Puedes consultar las recomendaciones actualizadas.");
    } catch (e) {
      if (request !== profileRequest.current) return;
      setSaveState("error");
      setMessage(`${e instanceof Error ? e.message : "No fue posible conectar con la API."} No se confirmó el guardado; tus datos escritos se conservan para corregir o reintentar.`);
    } finally {
      saving.current = false;
      setBusy(false);
    }
  }
  function fresh() {
    profileRequest.current += 1;
    setSelected(null);
    setDraft(empty());
    setEditorKey((k) => k + 1);
    setRecommendations([]);
    setApplications([]);
    setActivity([]);
    setReminders([]);
    setPreview(null);
    setDeleteConfirm(false);
    setDirty(false);
    setEditing(true);
    setSaveState("idle");
    setMessage("Entrada manual: completa los datos que conozcas.");
  }
  return (
    <div className="space-y-6 mt-6">
      <p className="rounded-lg bg-amber-50 p-4 text-sm text-amber-900">
        Entorno de demostración académica: todas las vacantes, postulaciones y
        contrataciones son simuladas. No se envían postulaciones a empresas.
        Cada vacante representa un puesto. Sin autenticación multiusuario.
      </p>
      <p role={saveState === "error" ? "alert" : "status"} aria-live="polite" className="text-sm font-medium">
        {message}
      </p>
      <fieldset
        disabled={busy}
        className="min-w-0 space-y-6 disabled:opacity-70"
      >
        <section className="panel" id="perfil-guardado">
          <h2>Perfil guardado y edición</h2>
          {cvOperationVersion > 0 && selected && selected.candidate_id !== extractedCandidateId && (
            <p role="status" className="my-3 rounded border border-amber-300 bg-amber-50 p-3 text-amber-950">
              No se generó un nuevo perfil. Se muestra el perfil guardado de {selected.profile.name || "Sin nombre"}.
              {" "}Este perfil no es el resultado del archivo seleccionado actualmente.
            </p>
          )}
          {selected && selected.candidate_id === extractedCandidateId && (
            <p className="my-3 text-sm text-emerald-800">Perfil asociado al CV actual: {selected.profile.name || "Sin nombre"}.</p>
          )}
          <div className="flex flex-wrap gap-3 my-4">
            <label>
              Perfiles guardados
              <select
                aria-label="Perfiles guardados"
                className="block border p-2 rounded"
                value={selected?.candidate_id ?? ""}
                onChange={(e) => {
                  const id = e.target.value;
                  if (id) void run(() => loadCandidate(id));
                  else fresh();
                }}
              >
                <option value="">Nuevo perfil manual</option>
                {profiles.map((p) => (
                  <option key={p.candidate_id} value={p.candidate_id}>
                    {p.profile.name || "Sin nombre"} ·{" "}
                    {p.candidate_id.slice(0, 6)}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="btn" onClick={fresh}>
              Crear perfil manual
            </button>
            <button
              type="button"
              className="btn"
              onClick={() =>
                void run(async () =>
                  setProfiles(await api<Profile[]>("/profiles")),
                )
              }
            >
              Actualizar lista
            </button>
          </div>
          <p className="text-sm mb-4">
            Origen: {selected?.source ?? "manual"}. Un campo vacío se conserva
            como desconocido. Ningún campo faltante impide guardar.
          </p>
          {selected && (
            <div className="mb-4 rounded bg-amber-50 p-3">
              <strong>Información por completar</strong>
              <ul>
                {selected.gaps
                  .filter((g) => g.missing)
                  .map((g) => (
                    <li key={g.field}>
                      {g.label} · {g.importance} · desconocido
                    </li>
                  ))}
              </ul>
              {selected.gaps.every((g) => !g.missing) && (
                <p>No se detectaron vacíos básicos.</p>
              )}
            </div>
          )}
          {selected && !editing && <button type="button" className="btn my-3" onClick={() => { setEditing(true); setSaveState("idle"); setMessage(""); }}>Editar</button>}
          {selected && editing && <button type="button" className="btn my-3" onClick={() => { setDraft(selected.profile); setEditorKey((k) => k + 1); setDirty(false); setEditing(false); setSaveState("idle"); setMessage(""); }}>Cancelar edición</button>}
          <ReadingProfile.Provider value={!editing}>
          <form onSubmit={save} key={editorKey} aria-label={editing ? "Editar perfil" : "Perfil guardado"} aria-busy={saveState === "saving"} className={`space-y-4 ${!editing ? "[&_button]:hidden" : ""}`}>
            <div className="grid gap-3 md:grid-cols-2">
              {(
                [
                  ["name", "Nombre"],
                  ["email", "Correo"],
                  ["phone", "Teléfono (incluye prefijo internacional, por ejemplo +57)"],
                  ["location", "Ubicación"],
                  ["target_role", "Cargo objetivo"],
                  ["professional_summary", "Resumen profesional"],
                ] as const
              ).map(([key, label]) => (
                <Field
                  key={key}
                  label={label}
                  type={key === "phone" ? "tel" : "text"}
                  value={draft[key]}
                  onChange={(v) => update(key, v || null)}
                />
              ))}
              <Field
                label="Años de experiencia (0 si no tienes)"
                type="number"
                value={draft.years_experience}
                onChange={(v) =>
                  update("years_experience", v === "" ? null : Number(v))
                }
              />
              <ListField
                label="Habilidades"
                values={draft.skills}
                onChange={(v) => update("skills", v)}
              />
              <ListField
                label="Idiomas"
                values={draft.languages}
                onChange={(v) => update("languages", v)}
              />
              <ListField
                label="Cargos deseados"
                values={draft.preferences.desired_roles}
                onChange={(v) => preference("desired_roles", v)}
              />
              <ListField
                label="Ubicaciones preferidas"
                values={draft.preferences.preferred_locations}
                onChange={(v) => preference("preferred_locations", v)}
              />
              <div>
                <p className="text-sm">Modalidades</p>
                {!editing ? <p>{draft.preferences.work_modes.join(", ") || "No informado"}</p> : ["remoto", "hibrido", "presencial"].map((mode) => (
                  <label key={mode} className="mr-3 text-sm">
                    <input
                      type="checkbox"
                      checked={draft.preferences.work_modes
                        .map((v) =>
                          v
                            .normalize("NFD")
                            .replace(/[\u0300-\u036f]/g, "")
                            .toLowerCase(),
                        )
                        .includes(mode)}
                      onChange={(e) =>
                        preference(
                          "work_modes",
                          e.target.checked
                            ? [...draft.preferences.work_modes, mode]
                            : draft.preferences.work_modes.filter(
                                (v) =>
                                  v
                                    .normalize("NFD")
                                    .replace(/[\u0300-\u036f]/g, "")
                                    .toLowerCase() !== mode,
                              ),
                        )
                      }
                    />{" "}
                    {mode}
                  </label>
                ))}
              </div>
              <Field
                label="Salario mínimo COP"
                type="number"
                value={draft.preferences.salary_min_cop}
                onChange={(v) =>
                  preference("salary_min_cop", v === "" ? null : Number(v))
                }
              />
              <Field
                label="Salario máximo COP"
                type="number"
                value={draft.preferences.salary_max_cop}
                onChange={(v) =>
                  preference("salary_max_cop", v === "" ? null : Number(v))
                }
              />
              <Field
                label="Tipo de contrato"
                value={draft.preferences.contract_type}
                onChange={(v) => preference("contract_type", v || null)}
              />
              <Field
                label="Disponibilidad"
                value={draft.preferences.availability}
                onChange={(v) => preference("availability", v || null)}
              />
            </div>
            <h3 className="font-semibold">Experiencia laboral</h3>
            {draft.work_experience.map((job, index) => (
              <div
                key={index}
                className="rounded border p-3 grid md:grid-cols-2 gap-3"
              >
                {(
                  [
                    "company",
                    "role",
                    "start_date",
                    "end_date",
                    "description",
                  ] as const
                ).map((k, i) => (
                  <Field
                    key={k}
                    label={
                      ["Empresa", "Cargo", "Inicio", "Fin", "Descripción"][i]
                    }
                    value={job[k]}
                    onChange={(v) =>
                      update(
                        "work_experience",
                        draft.work_experience.map((row, n) =>
                          n === index ? { ...row, [k]: v || null } : row,
                        ),
                      )
                    }
                  />
                ))}
                <button
                  type="button"
                  className="btn"
                  onClick={() =>
                    update(
                      "work_experience",
                      draft.work_experience.filter((_, n) => n !== index),
                    )
                  }
                >
                  Quitar experiencia {index + 1}
                </button>
              </div>
            ))}
            <button
              type="button"
              className="btn"
              onClick={() =>
                update("work_experience", [
                  ...draft.work_experience,
                  {
                    company: null,
                    role: null,
                    start_date: null,
                    end_date: null,
                    description: null,
                  } as WorkExperience,
                ])
              }
            >
              Agregar experiencia
            </button>
            <h3 className="font-semibold">Educación</h3>
            {draft.education.map((ed, index) => (
              <div
                key={index}
                className="rounded border p-3 grid md:grid-cols-2 gap-3"
              >
                {(
                  ["degree", "institution", "start_year", "end_year"] as const
                ).map((k, i) => (
                  <Field
                    key={k}
                    label={
                      ["Título", "Institución", "Año inicial", "Año final"][i]
                    }
                    type={i >= 2 ? "number" : "text"}
                    value={ed[k]}
                    onChange={(v) =>
                      update(
                        "education",
                        draft.education.map((row, n) =>
                          n === index
                            ? {
                                ...row,
                                [k]: v === "" ? null : i >= 2 ? Number(v) : v,
                              }
                            : row,
                        ),
                      )
                    }
                  />
                ))}
                <button
                  type="button"
                  className="btn"
                  onClick={() =>
                    update(
                      "education",
                      draft.education.filter((_, n) => n !== index),
                    )
                  }
                >
                  Quitar educación {index + 1}
                </button>
              </div>
            ))}
            <button
              type="button"
              className="btn"
              onClick={() =>
                update("education", [
                  ...draft.education,
                  {
                    degree: null,
                    institution: null,
                    start_year: null,
                    end_year: null,
                  } as Education,
                ])
              }
            >
              Agregar educación
            </button>
            <div>
              <button className="btn primary" type="submit">
                {saveState === "saving" ? "Guardando…" : "Guardar perfil"}
              </button>
              {dirty && (
                <span className="ml-3 text-sm">Cambios sin guardar</span>
              )}
            </div>
          </form>
          </ReadingProfile.Provider>
          {selected && (
            <div className="border-t pt-4 mt-5">
              <label className="text-sm">
                <input
                  type="checkbox"
                  checked={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.checked)}
                />{" "}
                Eliminar este perfil y sus postulaciones, recordatorios e
                historial. El PDF cargado permanece en el almacenamiento local.
              </label>
              <button
                type="button"
                className="btn ml-3"
                disabled={!deleteConfirm}
                onClick={() =>
                  void run(async () => {
                    await api(`/profiles/${selected.candidate_id}`, "DELETE");
                    setProfiles(await api<Profile[]>("/profiles"));
                    fresh();
                    setMessage("Perfil y registros asociados eliminados.");
                  })
                }
              >
                Eliminar perfil
              </button>
            </div>
          )}
        </section>
        <section className="panel">
          <h2>Vacantes y recomendaciones</h2>
          <p className="text-sm my-2">{vacancies.length} vacantes en el catálogo.</p>
          <p className="text-sm">{simulation ? `${vacancies.length - simulation.occupied_vacancy_ids.length} disponibles · ${simulation.occupied_vacancy_ids.length} ocupadas · Simulación ${simulation.current_id.slice(0, 8)}${simulation.current_id.endsWith("0001") ? " (inicial)" : ""}` : "Cargando disponibilidad…"}</p>
          {!selected && (
            <div className="grid gap-3 my-3">
              <p>Selecciona o guarda un perfil para calcular su afinidad y preparar una postulación.</p>
              {vacancies.map((v) => (
                <article key={v.id} className="border rounded-lg p-4">
                  <h3 className="font-semibold">{v.title}</h3>
                  <p className="font-medium">{!simulation ? "Disponibilidad pendiente" : occupied(v.id) ? "Ocupada" : "Disponible"}</p>
                  <p>{vacancyText(v.company)} · {v.location} · {v.work_mode}</p>
                  <p className="text-sm">{money(v.salary_min_cop)} – {money(v.salary_max_cop)}</p>
                  <details className="my-2">
                    <summary>Detalle de la vacante</summary>
                    <p>{vacancyText(v.description)}</p>
                    <p>Requisitos: {v.required_skills.join(", ")}.</p>
                    <p>Deseables: {v.desired_skills.join(", ")}.</p>
                    <p>Contrato: {v.contract_type ?? "Desconocido"}. Fuente: {v.source}.</p>
                  </details>
                </article>
              ))}
            </div>
          )}
          <p className="text-sm">
            Afinidad de 0 a 100 puntos por reglas. Datos desconocidos aportan 0;
            no es una probabilidad de contratación. Guarda los cambios antes de
            consultar o postularte.
          </p>
          <button
            type="button"
            className="btn my-3"
            disabled={!selected || dirty}
            onClick={() =>
              selected && void run(() => loadCandidate(selected.candidate_id))
            }
          >
            Consultar recomendaciones y seguimiento
          </button>
          {selected && recommendations.length === 0 && (
            <p>
              No hay recomendaciones cargadas. Consulta o importa el dataset
              siguiendo el guion de demo.
            </p>
          )}
          <div className="grid gap-3">
            {recommendations.map((r) => (
              <article key={r.vacancy.id} className="border rounded-lg p-4">
                <div className="flex justify-between gap-4">
                  <h3 className="font-semibold">{r.vacancy.title}</h3>
                  <strong className="whitespace-nowrap">{r.score} / 100</strong>
                </div>
                <p className="font-medium">{!simulation ? "Disponibilidad pendiente" : occupied(r.vacancy.id) ? "Ocupada" : "Disponible"}</p>
                <p>
                  {vacancyText(r.vacancy.company)} · {r.vacancy.location} ·{" "}
                  {r.vacancy.work_mode}
                </p>
                <p className="text-sm">
                  {money(r.vacancy.salary_min_cop)} –{" "}
                  {money(r.vacancy.salary_max_cop)}
                </p>
                <p className="text-sm mt-2">
                  Coinciden:{" "}
                  {r.matched_skills.join(", ") || "Ninguna identificada"}.
                  Faltan:{" "}
                  {r.missing_skills.join(", ") || "Ninguna identificada"}.
                </p>
                <details className="my-2">
                  <summary>Detalle y explicación</summary>
                  <p className="my-2">{vacancyText(r.vacancy.description)}</p>
                  <p>
                    Contrato: {r.vacancy.contract_type ?? "Desconocido"}.
                    Experiencia requerida:{" "}
                    {r.vacancy.years_experience ?? "Desconocida"} años.
                  </p>
                  <p>
                    Requisitos: {r.vacancy.required_skills.join(", ")}.
                    Deseables: {r.vacancy.desired_skills.join(", ")}.
                  </p>
                  <p>
                    Publicación: {r.vacancy.published_at}. Fuente:{" "}
                    {r.vacancy.source}.
                  </p>
                  <ul className="text-sm mt-2">
                    {r.components.map((c) => (
                      <li key={c.criterion}>
                        {c.reason}: {c.points}/{c.weight}
                        {!c.known ? " (desconocido)" : ""}
                      </li>
                    ))}
                  </ul>
                  <p className="text-sm mt-2">
                    Experiencia, contrato y habilidades deseables son
                    informativos y no alteran los pesos.
                  </p>
                </details>
                <button
                  type="button"
                  className="btn"
                  disabled={
                    dirty || !simulation || occupied(r.vacancy.id) ||
                    applications.some((a) => a.is_current && a.vacancy.id === r.vacancy.id)
                  }
                  onClick={() => {
                    setPreview(r.vacancy);
                    setConfirmed(false);
                  }}
                >
                  {occupied(r.vacancy.id) ? "Vacante ocupada" : applications.some((a) => a.is_current && a.vacancy.id === r.vacancy.id)
                    ? "Ya postulado"
                    : "Preparar postulación simulada"}
                </button>
              </article>
            ))}
          </div>
          {preview && (
            <div
              role="dialog"
              aria-label="Confirmar postulación simulada"
              className="fixed bottom-5 left-1/2 z-50 w-[min(90vw,42rem)] -translate-x-1/2 rounded-xl border-2 border-blue-700 p-5 bg-blue-50 shadow-xl"
            >
              <h3 className="font-bold">Confirmar simulación</h3>
              <p>
                {draft.name || "Candidato sin nombre"} → {preview.title} ·{" "}
                {vacancyText(preview.company)}
              </p>
              <p>
                Se guardará una evidencia local. No se enviarán datos a la
                empresa ni a Magneto.
              </p>
              <label className="block my-3">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />{" "}
                Confirmo esta postulación simulada
              </label>
              <button
                type="button"
                className="btn primary"
                disabled={!confirmed || dirty || !simulation || occupied(preview.id)}
                onClick={() =>
                  selected &&
                  void run(async () => {
                    await api("/applications", "POST", {
                      candidate_id: selected.candidate_id,
                      vacancy_id: preview.id,
                      confirmed: true,
                      simulation_id: simulation?.current_id,
                    });
                    await loadCandidate(selected.candidate_id);
                    setMessage(
                      "Postulación simulada registrada con evidencia.",
                    );
                  })
                }
              >
                Confirmar postulación
              </button>
              <button
                type="button"
                className="btn ml-3"
                onClick={() => {
                  setPreview(null);
                  setConfirmed(false);
                }}
              >
                Cancelar
              </button>
            </div>
          )}
        </section>
        <section className="panel">
          <h2>Contratados y simulaciones</h2>
          <p className="text-sm">Un puesto por vacante en cada simulación. El historial de simulaciones anteriores se conserva.</p>
          {simulation?.hires.length === 0 && <p>No hay contrataciones registradas.</p>}
          <ul>
            {simulation?.hires.map((hire) => <li key={hire.application_id} className="my-3">
              <strong>{hire.candidate_name || "Sin nombre"}</strong> · {hire.vacancy_title} · {hire.hired_at ? date(hire.hired_at) : "Fecha de contratación no registrada (histórico)"}
              <p className="text-sm">{hire.simulation_id === simulation.current_id ? "Simulación actual" : `Simulación anterior ${hire.simulation_id.slice(0, 8)}`}</p>
            </li>)}
          </ul>
          <details className="my-3"><summary>Historial de simulaciones</summary>
            <ul>{simulation?.simulations.map((s) => <li key={s.id}>{s.id.slice(0, 8)} · {date(s.created_at)} · {s.active ? "Actual" : "Anterior"}</li>)}</ul>
            <p className="text-sm">La fecha de la simulación inicial indica su creación durante la migración; las postulaciones conservan sus fechas originales.</p>
          </details>
          <label className="block my-3"><input type="checkbox" checked={newSimulationConfirm} onChange={(e) => setNewSimulationConfirm(e.target.checked)} /> Confirmo iniciar una nueva simulación: todas las vacantes vuelven a estar disponibles y el historial actual queda en lectura.</label>
          <button type="button" className="btn" disabled={!newSimulationConfirm || !simulation || dirty} onClick={() => void run(async () => {
            const result = await api<SimulationView>("/simulations", "POST", { confirmed: true, expected_current_id: simulation?.current_id });
            setSimulation(result);
            setNewSimulationConfirm(false);
            setPreview(null);
            if (selected) await loadCandidate(selected.candidate_id);
            setMessage("Nueva simulación iniciada. Historial anterior conservado.");
          })}>Iniciar nueva simulación</button>
        </section>
        <section className="panel">
          <h2>Postulaciones y seguimiento</h2>
          {applications.length === 0 && (
            <p>No hay postulaciones para mostrar.</p>
          )}
          {applications.map((a) => (
            <article key={a.id} className="border rounded p-4 my-3">
              <h3 className="font-semibold">
                {a.vacancy.title} · {a.status}
              </h3>
              <p className="text-sm">
                {a.is_current ? "Simulación actual" : "Simulación anterior (solo lectura)"} · {date(a.created_at)} ·{" "}
                {["descartado", "contratado"].includes(a.status) ? "Finalizada" : "Activa"}
              </p>
              <p className="my-2">Próximo paso: {a.next_step}</p>
              <label className="text-sm">
                Cambiar estado (demostración manual)
                <select
                  className="border rounded p-2 ml-2"
                  aria-label={`Estado de ${a.vacancy.title}`}
                  value=""
                  disabled={dirty || !a.is_current || a.allowed_transitions.length === 0}
                  onChange={(e) => {
                    const status = e.target.value;
                    if (status && selected)
                      void run(async () => {
                        await api(`/applications/${a.id}`, "PATCH", { status });
                        await loadCandidate(selected.candidate_id);
                        setMessage("Estado de demostración actualizado.");
                      });
                  }}
                >
                  <option value="">Seleccionar</option>
                  {a.allowed_transitions.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </label>
              <details className="mt-2">
                <summary>Evidencia de la simulación</summary>
                <pre className="whitespace-pre-wrap break-all text-xs bg-slate-50 p-2">
                  {JSON.stringify(a.evidence, null, 2)}
                </pre>
              </details>
              <details>
                <summary>Historial del proceso</summary>
                <ul>
                  {activity
                    .filter((l) => l.application_id === a.id)
                    .map((l) => (
                      <li key={l.id} className="my-2 text-sm">
                        {date(l.created_at)} · {l.agent} · {l.action}:{" "}
                        {l.reason}
                      </li>
                    ))}
                </ul>
              </details>
            </article>
          ))}
          <h3 className="font-semibold mt-5">
            Recordatorios dentro de WORKINT
          </h3>
          <ul>
            {reminders
              .filter((r) => r.pending)
              .map((r) => (
                <li className="my-2 text-sm" key={r.id}>
                  {date(r.due_at)} · {r.message} · proceso{" "}
                  {r.application_id.slice(0, 8)}
                </li>
              ))}
          </ul>
          {!reminders.some((r) => r.pending) && (
            <p className="text-sm">Sin recordatorios pendientes.</p>
          )}
        </section>
        <section className="panel">
          <h2>Actividad de componentes y flujos</h2>
          <p className="text-sm">Eventos persistidos en orden cronológico.</p>
          <ol>
            {activity.map((l) => (
              <li key={l.id} className="border-b py-3 text-sm">
                <strong>
                  {l.agent} · {l.action}
                </strong>{" "}
                · {date(l.created_at)} · {l.status}
                <p>{l.reason}</p>
                <p className="text-xs break-all">
                  Referencia: {l.result_ref ?? "Sin referencia"}
                </p>
                <p className="text-xs break-all">Operación: {l.operation_id ?? "No registrada (histórico)"} · Contexto: {l.execution_context?.execution_mode ?? "No registrado (histórico)"}</p>
                {l.action === "extraer_cv" && <p className="text-xs break-all">
                  Proveedor: {l.execution_context?.provider ?? "No disponible"} · Modelo efectivo: {l.execution_context?.effective_model ?? "No disponible"} · Solicitud del proveedor: {l.execution_context?.provider_request_id ?? "No disponible"}.
                  {l.execution_context?.configured_model && ` Modelo configurado: ${l.execution_context.configured_model} (no prueba el modelo efectivo).`}
                </p>}
              </li>
            ))}
          </ol>
        </section>
      </fieldset>
    </div>
  );
}
