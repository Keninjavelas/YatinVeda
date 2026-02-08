/**
 * Geocoding utility to fetch coordinates from city names
 * Uses OpenStreetMap Nominatim API (free, no API key required)
 */

export interface Coordinates {
  latitude: number
  longitude: number
  timezone: string
  displayName: string
}

/**
 * Fetch coordinates for a given city/location
 * @param location City name, can include country (e.g., "Mumbai, India")
 * @returns Coordinates and timezone
 */
export async function getCoordinatesFromLocation(location: string): Promise<Coordinates | null> {
  try {
    // Use Nominatim API (OpenStreetMap)
    const encodedLocation = encodeURIComponent(location)
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?q=${encodedLocation}&format=json&limit=1&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'YatinVeda-Astrology-App'
        }
      }
    )

    if (!response.ok) {
      throw new Error('Geocoding request failed')
    }

    const data = await response.json()

    if (!data || data.length === 0) {
      return null
    }

    const result = data[0]
    const latitude = parseFloat(result.lat)
    const longitude = parseFloat(result.lon)

    // Determine timezone based on coordinates (simplified mapping)
    const timezone = getTimezoneFromCoordinates(latitude, longitude, result.address?.country_code)

    return {
      latitude,
      longitude,
      timezone,
      displayName: result.display_name
    }
  } catch (error) {
    console.error('Geocoding error:', error)
    return null
  }
}

/**
 * Simple timezone mapping based on coordinates and country
 * For more accurate timezone detection, consider using a dedicated API
 */
function getTimezoneFromCoordinates(lat: number, lon: number, countryCode?: string): string {
  // India
  if (countryCode === 'in') return 'Asia/Kolkata'
  
  // USA - simplified zones
  if (countryCode === 'us') {
    if (lon < -120) return 'America/Los_Angeles' // Pacific
    if (lon < -105) return 'America/Denver' // Mountain
    if (lon < -90) return 'America/Chicago' // Central
    return 'America/New_York' // Eastern
  }
  
  // UK
  if (countryCode === 'gb') return 'Europe/London'
  
  // Australia
  if (countryCode === 'au') {
    if (lon < 140) return 'Australia/Perth' // Western
    if (lon < 145) return 'Australia/Adelaide' // Central
    return 'Australia/Sydney' // Eastern
  }
  
  // China
  if (countryCode === 'cn') return 'Asia/Shanghai'
  
  // Japan
  if (countryCode === 'jp') return 'Asia/Tokyo'
  
  // Canada
  if (countryCode === 'ca') {
    if (lon < -120) return 'America/Vancouver' // Pacific
    if (lon < -105) return 'America/Edmonton' // Mountain
    if (lon < -90) return 'America/Winnipeg' // Central
    if (lon < -60) return 'America/Toronto' // Eastern
    return 'America/Halifax' // Atlantic
  }
  
  // Germany
  if (countryCode === 'de') return 'Europe/Berlin'
  
  // France
  if (countryCode === 'fr') return 'Europe/Paris'
  
  // Singapore
  if (countryCode === 'sg') return 'Asia/Singapore'
  
  // UAE
  if (countryCode === 'ae') return 'Asia/Dubai'
  
  // General timezone estimation based on longitude
  // Each 15 degrees of longitude ≈ 1 hour
  const hourOffset = Math.round(lon / 15)
  
  if (hourOffset === 0) return 'UTC'
  if (hourOffset > 0) return `UTC+${hourOffset}`
  return `UTC${hourOffset}`
}

/**
 * Debounce function to limit API calls
 */
export function debounce<TArgs extends unknown[]>(
  func: (...args: TArgs) => void,
  wait: number
): (...args: TArgs) => void {
  let timeout: NodeJS.Timeout | null = null

  return function executedFunction(...args: TArgs) {
    const later = () => {
      timeout = null
      func(...args)
    }

    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(later, wait)
  }
}
