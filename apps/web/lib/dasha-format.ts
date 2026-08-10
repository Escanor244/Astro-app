/**
 * Formatting for dasha periods.
 *
 * Split out of the component so it can be unit-tested, because both functions
 * here have a trap in them.
 *
 * Dates arrive as naive local ISO strings — "2015-02-01T10:23:45" — already
 * converted to the birth place's wall clock by the engine. They are formatted by
 * *slicing the string*, never by `new Date(...)`. Passing a naive ISO string to
 * the Date constructor makes the browser reinterpret it in the viewer's own
 * timezone, so a dasha that begins at 00:30 in Chennai would print as the
 * previous day for anyone reading from London. The whole point of the engine
 * sending local time is lost the moment a Date object touches it.
 *
 * Durations span five orders of magnitude — a mahadasha is up to 20 years, a
 * prana period a few minutes — so one unit cannot serve them all.
 */

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

/** "2015-02-01T10:23:45" -> "1 Feb 2015". Pure string work, no Date. */
export function formatPeriodDate(iso: string): string {
  const [datePart] = iso.split("T");
  const [y, m, d] = datePart.split("-");
  const month = MONTHS[Number(m) - 1];
  if (!month || !y || !d) return iso;
  return `${Number(d)} ${month} ${y}`;
}

/** The clock part, "10:23". Empty when the string carries no time. */
export function formatPeriodTime(iso: string): string {
  const time = iso.split("T")[1];
  return time ? time.slice(0, 5) : "";
}

/**
 * A period's length in whichever unit reads naturally at that scale.
 *
 * Deliberately approximate: these are labels beside exact start and end dates,
 * not the dates themselves. Months are 30 days and years 365, which is what
 * makes "16y" come out of a 16-year mahadasha instead of "15y 11m".
 */
export function formatDuration(days: number): string {
  // The threshold is 360, not 365, and that matters. Months here are 30 days,
  // so anything from 360 days up is already twelve of them; handing such a value
  // to the months branch printed "12m 5d" — a month that does not exist in a
  // twelve-month year. Letting the years branch take it lets its own carry
  // resolve the case.
  if (days >= 360) {
    const years = Math.floor(days / 365);
    const months = Math.round((days - years * 365) / 30);
    // Rounding up to 12 months must carry, or a 16-year period prints "15y 12m".
    if (months >= 12) return `${years + 1}y`;
    return months ? `${years}y ${months}m` : `${years}y`;
  }
  if (days >= 30) {
    const months = Math.floor(days / 30);
    const rest = Math.round(days - months * 30);
    if (rest >= 30) {
      // The day rounded up to a whole month, and that carry can itself reach
      // twelve — 359.5 days is 11 months and 29.5 more, which rounds to a
      // twelfth month. It has to keep going up, not stop at "12m".
      return months + 1 >= 12 ? "1y" : `${months + 1}m`;
    }
    return rest ? `${months}m ${rest}d` : `${months}m`;
  }
  if (days >= 1) {
    const whole = Math.floor(days);
    const hours = Math.round((days - whole) * 24);
    if (hours >= 24) return `${whole + 1}d`;
    return hours ? `${whole}d ${hours}h` : `${whole}d`;
  }
  const minutes = Math.round(days * 24 * 60);
  if (minutes >= 60) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return m ? `${h}h ${m}m` : `${h}h`;
  }
  return `${Math.max(minutes, 1)}m`;
}

/** Whether a period has already finished, relative to the engine's `at`. */
export function isPast(period: { end: string }, at: string): boolean {
  return period.end < at;
}
