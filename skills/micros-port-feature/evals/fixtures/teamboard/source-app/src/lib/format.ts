const UNITS: Array<[number, Intl.RelativeTimeFormatUnit]> = [
  [60, 'second'],
  [60, 'minute'],
  [24, 'hour'],
  [7, 'day'],
]

const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

export function timeAgo(iso: string): string {
  let delta = (Date.parse(iso) - Date.now()) / 1000
  for (const [step, unit] of UNITS) {
    if (Math.abs(delta) < step) return rtf.format(Math.round(delta), unit)
    delta /= step
  }
  return rtf.format(Math.round(delta), 'week')
}
