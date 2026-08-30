import { addDaysIso } from "@/lib/date-utils";
import type { Room } from "@/lib/api-clients/establishment";

export const DAY_WIDTH = 96;
export const ROW_HEIGHT = 56;
export const ROOM_COL_WIDTH = 140;

export function buildDayRange(fromDate: string, toDate: string): string[] {
  const days: string[] = [];
  let d = fromDate;
  let guard = 0;
  while (d <= toDate && guard < 366) {
    days.push(d);
    d = addDaysIso(d, 1);
    guard += 1;
  }
  return days;
}

export function sortRooms(rooms: Room[]): Room[] {
  return [...rooms].sort((a, b) => a.floor - b.floor || a.numero.localeCompare(b.numero));
}

function nightsBetween(a: string, b: string): number {
  return Math.round((Date.parse(`${b}T00:00:00Z`) - Date.parse(`${a}T00:00:00Z`)) / 86_400_000);
}

/**
 * Position/largeur (en nombre de colonnes jour) d'une barre de réservation,
 * clippée aux bornes de la plage affichée. Retourne `null` si la
 * réservation ne chevauche pas du tout la plage visible.
 */
export function barGeometry(
  checkIn: string,
  checkOut: string,
  days: string[],
  dayIndexByIso: Map<string, number>
): { startIdx: number; nightCount: number } | null {
  if (days.length === 0) return null;
  const rangeStart = days[0];
  const rangeEndExclusive = addDaysIso(days[days.length - 1], 1);
  if (checkOut <= rangeStart || checkIn >= rangeEndExclusive) return null;

  const clippedStart = checkIn < rangeStart ? rangeStart : checkIn;
  const clippedEnd = checkOut > rangeEndExclusive ? rangeEndExclusive : checkOut;
  const startIdx = dayIndexByIso.get(clippedStart) ?? 0;
  const nightCount = Math.max(1, nightsBetween(clippedStart, clippedEnd));
  return { startIdx, nightCount };
}
