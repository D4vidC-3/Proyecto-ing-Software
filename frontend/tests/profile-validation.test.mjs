import test from "node:test";
import assert from "node:assert/strict";
import { salaryError } from "../src/app/profile-validation.ts";

test("salario: permite desconocidos, cero e igualdad; rechaza rango invertido", () => {
  for (const [min, max] of [[null, null], [0, 0], [100, 100], [null, 100], [100, null]]) {
    assert.equal(salaryError({ salary_min_cop: min, salary_max_cop: max }), null);
  }
  assert.match(salaryError({ salary_min_cop: 200, salary_max_cop: 100 }), /mínimo/);
});
