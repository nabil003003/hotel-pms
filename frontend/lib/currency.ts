/**
 * Formatage monétaire strict MAD (décision D5) — remplace le "DH" sans
 * décimales des maquettes par le format imposé §0.1 du spec :
 * devise MAD, 2 décimales, locale marocaine.
 */
export function formatMAD(amount: number): string {
  return new Intl.NumberFormat("fr-MA", {
    style: "currency",
    currency: "MAD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}
