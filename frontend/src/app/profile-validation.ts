import type { CandidateProfile } from "./profile-types";

export function salaryError(preferences: CandidateProfile["preferences"]): string | null {
  const { salary_min_cop: min, salary_max_cop: max } = preferences;
  return min !== null && max !== null && min > max
    ? "El salario mínimo no puede superar el máximo. Corrige el rango; tus datos se conservan."
    : null;
}
