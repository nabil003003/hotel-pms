export function addDaysIso(baseIso: string, days: number) {
  // Arithmétique en UTC : parser/formater en heure locale ferait dériver la
  // date d'un jour dès que le fuseau du navigateur a un offset positif
  // (ex. minuit local == 23h la veille en UTC, cf. incident réel avec
  // GMT+1 : addDaysIso("2026-08-07", 1) retournait "2026-08-07" au lieu de
  // "2026-08-08", rejeté par reservation-service car check_out == check_in).
  const d = new Date(`${baseIso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}
