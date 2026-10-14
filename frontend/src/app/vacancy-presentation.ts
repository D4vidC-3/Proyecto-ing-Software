// Solo presentación: no se modifica el catálogo ni la entrada del matching.
export function vacancyText(value: string): string {
  return value
    .replace(/V\d{2} - DEMOSTRACIÓN ACADÉMICA\. Oferta ficticia; contratación exclusivamente simulada y local\.\s*/g, "")
    .replace(/\s*\(fictici[oa]\)/gi, "")
    .replace(/Vacante ficticia/gi, "Vacante")
    .replace(/\s*Solo demostración académica\./gi, "");
}
