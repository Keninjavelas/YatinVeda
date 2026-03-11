"""Native Vedic astrological calculations engine.

Provides birth chart (Kundli) generation, planetary positions,
Dasha periods, Nakshatra mapping, and house placement calculations
without relying on external APIs.

Uses the Swiss Ephemeris (swisseph) library for astronomical calculations
when available, falling back to simplified mathematical models.
"""

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    import swisseph as swe
    SWE_AVAILABLE = True
except ImportError:
    swe = None
    SWE_AVAILABLE = False
    logger.info("swisseph not installed — using simplified calculation models")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_SPAN = 360.0 / 27  # 13°20'

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# Vimshottari Dasha sequence and total years per planet
DASHA_SEQUENCE = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
    ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19),
    ("Mercury", 17),
]
DASHA_TOTAL_YEARS = sum(y for _, y in DASHA_SEQUENCE)  # 120

# Ayanamsa constant (Lahiri - approximate for date calculations)
LAHIRI_AYANAMSA_J2000 = 23.853  # degrees at J2000.0
AYANAMSA_YEARLY_RATE = 50.29 / 3600  # arcseconds per year → degrees


class HouseSystem(Enum):
    EQUAL = "equal"
    WHOLE_SIGN = "whole_sign"
    PLACIDUS = "placidus"


@dataclass
class PlanetPosition:
    planet: str
    longitude: float  # sidereal degrees 0‒360
    sign: str
    sign_index: int  # 0-based
    degree_in_sign: float
    nakshatra: str
    nakshatra_index: int
    nakshatra_pada: int  # 1‒4
    is_retrograde: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "planet": self.planet,
            "longitude": round(self.longitude, 4),
            "sign": self.sign,
            "sign_index": self.sign_index,
            "degree_in_sign": round(self.degree_in_sign, 4),
            "nakshatra": self.nakshatra,
            "nakshatra_index": self.nakshatra_index,
            "nakshatra_pada": self.nakshatra_pada,
            "is_retrograde": self.is_retrograde,
        }


@dataclass
class HouseCusp:
    house: int  # 1‒12
    longitude: float
    sign: str

    def to_dict(self) -> Dict[str, Any]:
        return {"house": self.house, "longitude": round(self.longitude, 4), "sign": self.sign}


@dataclass
class DashaPeriod:
    planet: str
    start: datetime
    end: datetime
    years: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "planet": self.planet,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "years": round(self.years, 2),
        }


@dataclass
class BirthChart:
    ascendant: float
    ascendant_sign: str
    planets: List[PlanetPosition] = field(default_factory=list)
    houses: List[HouseCusp] = field(default_factory=list)
    dashas: List[DashaPeriod] = field(default_factory=list)
    ayanamsa: float = 0.0
    calculation_method: str = "simplified"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ascendant": round(self.ascendant, 4),
            "ascendant_sign": self.ascendant_sign,
            "ayanamsa": round(self.ayanamsa, 4),
            "calculation_method": self.calculation_method,
            "planets": [p.to_dict() for p in self.planets],
            "houses": [h.to_dict() for h in self.houses],
            "dashas": [d.to_dict() for d in self.dashas],
        }


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _sign_from_longitude(lon: float) -> Tuple[str, int, float]:
    """Return (sign_name, sign_index_0based, degree_in_sign)."""
    idx = int(lon / 30) % 12
    return SIGNS[idx], idx, lon % 30


def _nakshatra_from_longitude(lon: float) -> Tuple[str, int, int]:
    """Return (nakshatra_name, nakshatra_index_0based, pada_1based)."""
    idx = int(lon / NAKSHATRA_SPAN) % 27
    pada = int((lon % NAKSHATRA_SPAN) / (NAKSHATRA_SPAN / 4)) + 1
    return NAKSHATRAS[idx], idx, min(pada, 4)


def _julian_day(dt: datetime) -> float:
    """Convert datetime to Julian Day Number."""
    y = dt.year
    m = dt.month
    d = dt.day + dt.hour / 24 + dt.minute / 1440 + dt.second / 86400
    if m <= 2:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5


def _ayanamsa(jd: float) -> float:
    """Compute Lahiri ayanamsa for a given Julian Day."""
    if SWE_AVAILABLE:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.get_ayanamsa(jd)
    # Simplified linear model
    t = (jd - 2451545.0) / 365.25  # years from J2000.0
    return LAHIRI_AYANAMSA_J2000 + AYANAMSA_YEARLY_RATE * t


# ---------------------------------------------------------------------------
# Simplified planetary longitude calculator (fallback)
# ---------------------------------------------------------------------------

# Mean orbital elements at J2000.0 (simplified, tropical)
_MEAN_ELEMENTS = {
    #               L0 (deg)    rate (deg/day)
    "Sun":         (280.46646,  0.9856474),
    "Moon":        (218.3165,   13.1763966),
    "Mercury":     (252.2509,   4.0923344),
    "Venus":       (181.9798,   1.6021302),
    "Mars":        (355.4530,   0.5240208),
    "Jupiter":     ( 34.3515,   0.0831294),
    "Saturn":      ( 50.0774,   0.0334442),
}


def _mean_longitude(planet: str, jd: float) -> float:
    """Return tropical mean longitude in degrees."""
    if planet not in _MEAN_ELEMENTS:
        return 0.0
    l0, rate = _MEAN_ELEMENTS[planet]
    days = jd - 2451545.0
    return (l0 + rate * days) % 360


def _compute_rahu_ketu(jd: float) -> Tuple[float, float]:
    """Return mean Rahu & Ketu longitudes (tropical)."""
    days = jd - 2451545.0
    # Mean ascending node regresses ~0.0529539 deg/day
    rahu = (125.0445 - 0.0529539 * days) % 360
    ketu = (rahu + 180) % 360
    return rahu, ketu


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

class AstrologyEngine:
    """Compute Vedic birth charts with planetary positions and Dasha periods."""

    def __init__(self, house_system: HouseSystem = HouseSystem.WHOLE_SIGN):
        self.house_system = house_system

    def calculate_chart(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone_offset: float = 5.5,  # IST default
    ) -> BirthChart:
        """Calculate full birth chart.

        Args:
            birth_datetime: Local birth date & time.
            latitude / longitude: Birth location coordinates.
            timezone_offset: Offset from UTC in hours.

        Returns:
            BirthChart with planets, houses, and Dasha periods.
        """
        # Convert local time to UTC
        utc_dt = birth_datetime - timedelta(hours=timezone_offset)
        jd = _julian_day(utc_dt)
        ayanamsa = _ayanamsa(jd)

        if SWE_AVAILABLE:
            return self._calculate_swe(jd, latitude, longitude, ayanamsa, birth_datetime)
        return self._calculate_simplified(jd, latitude, longitude, ayanamsa, birth_datetime)

    # ------------------------------------------------------------------
    # Swiss Ephemeris path
    # ------------------------------------------------------------------
    def _calculate_swe(self, jd: float, lat: float, lon: float,
                       ayanamsa: float, birth_dt: datetime) -> BirthChart:
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        SWE_PLANET_MAP = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS, "Saturn": swe.SATURN,
        }

        planets: List[PlanetPosition] = []
        for name, pid in SWE_PLANET_MAP.items():
            flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
            result = swe.calc_ut(jd, pid, flags)
            trop_lon = result[0][0] if isinstance(result[0], (list, tuple)) else result[0]
            sid_lon = trop_lon % 360
            speed = result[0][3] if isinstance(result[0], (list, tuple)) and len(result[0]) > 3 else 0
            sign, si, deg = _sign_from_longitude(sid_lon)
            nak, ni, pada = _nakshatra_from_longitude(sid_lon)
            planets.append(PlanetPosition(
                planet=name, longitude=sid_lon, sign=sign, sign_index=si,
                degree_in_sign=deg, nakshatra=nak, nakshatra_index=ni,
                nakshatra_pada=pada, is_retrograde=speed < 0,
            ))

        # Rahu/Ketu via mean node
        rahu_result = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        rahu_lon = (rahu_result[0][0] if isinstance(rahu_result[0], (list, tuple)) else rahu_result[0]) % 360
        ketu_lon = (rahu_lon + 180) % 360
        for name, lon_val in [("Rahu", rahu_lon), ("Ketu", ketu_lon)]:
            sign, si, deg = _sign_from_longitude(lon_val)
            nak, ni, pada = _nakshatra_from_longitude(lon_val)
            planets.append(PlanetPosition(
                planet=name, longitude=lon_val, sign=sign, sign_index=si,
                degree_in_sign=deg, nakshatra=nak, nakshatra_index=ni,
                nakshatra_pada=pada,
            ))

        # Ascendant
        houses_cusps, ascmc = swe.houses(jd, lat, lon, b'W')  # Whole sign
        asc_lon = (ascmc[0] - ayanamsa) % 360
        asc_sign, _, _ = _sign_from_longitude(asc_lon)

        houses = self._build_houses(asc_lon)
        dashas = self._compute_dashas(planets, birth_dt)

        return BirthChart(
            ascendant=asc_lon, ascendant_sign=asc_sign,
            planets=planets, houses=houses, dashas=dashas,
            ayanamsa=ayanamsa, calculation_method="swisseph",
        )

    # ------------------------------------------------------------------
    # Simplified fallback path
    # ------------------------------------------------------------------
    def _calculate_simplified(self, jd: float, lat: float, lon: float,
                              ayanamsa: float, birth_dt: datetime) -> BirthChart:
        planets: List[PlanetPosition] = []
        for name in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
            trop = _mean_longitude(name, jd)
            sid = (trop - ayanamsa) % 360
            sign, si, deg = _sign_from_longitude(sid)
            nak, ni, pada = _nakshatra_from_longitude(sid)
            planets.append(PlanetPosition(
                planet=name, longitude=sid, sign=sign, sign_index=si,
                degree_in_sign=deg, nakshatra=nak, nakshatra_index=ni,
                nakshatra_pada=pada,
            ))

        rahu_trop, ketu_trop = _compute_rahu_ketu(jd)
        for name, trop in [("Rahu", rahu_trop), ("Ketu", ketu_trop)]:
            sid = (trop - ayanamsa) % 360
            sign, si, deg = _sign_from_longitude(sid)
            nak, ni, pada = _nakshatra_from_longitude(sid)
            planets.append(PlanetPosition(
                planet=name, longitude=sid, sign=sign, sign_index=si,
                degree_in_sign=deg, nakshatra=nak, nakshatra_index=ni,
                nakshatra_pada=pada,
            ))

        # Simplified ascendant: based on LST
        lst_hours = (jd - 2451545.0) * 1.00273790935 % 24 + lon / 15
        asc_trop = (lst_hours * 15) % 360
        asc_sid = (asc_trop - ayanamsa) % 360
        asc_sign, _, _ = _sign_from_longitude(asc_sid)

        houses = self._build_houses(asc_sid)
        dashas = self._compute_dashas(planets, birth_dt)

        return BirthChart(
            ascendant=asc_sid, ascendant_sign=asc_sign,
            planets=planets, houses=houses, dashas=dashas,
            ayanamsa=ayanamsa, calculation_method="simplified",
        )

    # ------------------------------------------------------------------
    # Houses
    # ------------------------------------------------------------------
    def _build_houses(self, asc_lon: float) -> List[HouseCusp]:
        houses: List[HouseCusp] = []
        if self.house_system == HouseSystem.WHOLE_SIGN:
            first_sign_start = int(asc_lon / 30) * 30
            for i in range(12):
                cusp = (first_sign_start + i * 30) % 360
                sign, _, _ = _sign_from_longitude(cusp)
                houses.append(HouseCusp(house=i + 1, longitude=cusp, sign=sign))
        else:
            # Equal house: each house = asc + i*30
            for i in range(12):
                cusp = (asc_lon + i * 30) % 360
                sign, _, _ = _sign_from_longitude(cusp)
                houses.append(HouseCusp(house=i + 1, longitude=cusp, sign=sign))
        return houses

    # ------------------------------------------------------------------
    # Vimshottari Dasha
    # ------------------------------------------------------------------
    def _compute_dashas(self, planets: List[PlanetPosition],
                        birth_dt: datetime) -> List[DashaPeriod]:
        moon = next((p for p in planets if p.planet == "Moon"), None)
        if moon is None:
            return []

        # Find starting Dasha lord from Moon's Nakshatra
        nak_idx = moon.nakshatra_index
        # Each Nakshatra is ruled by a planet in the Dasha sequence (repeating cycle of 9)
        lord_index = nak_idx % 9  # index into DASHA_SEQUENCE
        lord_name, lord_years = DASHA_SEQUENCE[lord_index]

        # Elapsed fraction within the Nakshatra
        moon_in_nak = moon.longitude % NAKSHATRA_SPAN
        elapsed_fraction = moon_in_nak / NAKSHATRA_SPAN
        remaining_years = lord_years * (1 - elapsed_fraction)

        dashas: List[DashaPeriod] = []
        cursor = birth_dt

        # First (partial) Dasha
        end = cursor + timedelta(days=remaining_years * 365.25)
        dashas.append(DashaPeriod(planet=lord_name, start=cursor, end=end, years=remaining_years))
        cursor = end

        # Subsequent full Dashas (cycle through remaining lords)
        for offset in range(1, 9):
            idx = (lord_index + offset) % 9
            name, years = DASHA_SEQUENCE[idx]
            end = cursor + timedelta(days=years * 365.25)
            dashas.append(DashaPeriod(planet=name, start=cursor, end=end, years=float(years)))
            cursor = end

        return dashas

    # ------------------------------------------------------------------
    # Compatibility (Ashtakoot)
    # ------------------------------------------------------------------
    def calculate_compatibility(
        self,
        chart1: BirthChart,
        chart2: BirthChart,
    ) -> Dict[str, Any]:
        """Simple Ashtakoot-style compatibility scoring between two charts."""
        moon1 = next((p for p in chart1.planets if p.planet == "Moon"), None)
        moon2 = next((p for p in chart2.planets if p.planet == "Moon"), None)
        if not moon1 or not moon2:
            return {"total_score": 0, "max_score": 36, "details": {}}

        scores: Dict[str, float] = {}

        # 1. Varna (1 point)
        varna_map = {0: 0, 1: 1, 2: 2, 3: 3}  # simplified
        v1 = varna_map.get(moon1.sign_index % 4, 0)
        v2 = varna_map.get(moon2.sign_index % 4, 0)
        scores["varna"] = 1.0 if v1 >= v2 else 0.0

        # 2. Vashya (2 points)
        scores["vashya"] = 2.0 if abs(moon1.sign_index - moon2.sign_index) <= 2 else 1.0

        # 3. Tara (3 points)
        tara_diff = abs(moon1.nakshatra_index - moon2.nakshatra_index) % 9
        scores["tara"] = 3.0 if tara_diff in {1, 2, 4, 6, 8} else 1.5

        # 4. Yoni (4 points)
        scores["yoni"] = 4.0 if moon1.nakshatra_index % 14 == moon2.nakshatra_index % 14 else 2.0

        # 5. Graha Maitri (5 points)
        sign_diff = abs(moon1.sign_index - moon2.sign_index)
        scores["graha_maitri"] = 5.0 if sign_diff in {0, 3, 4, 5} else 2.5

        # 6. Gana (6 points)
        g1 = moon1.nakshatra_index % 3
        g2 = moon2.nakshatra_index % 3
        scores["gana"] = 6.0 if g1 == g2 else 3.0

        # 7. Bhakoot (7 points)
        bhakoot_diff = (moon2.sign_index - moon1.sign_index) % 12
        bad_combos = {1, 5, 6, 7, 11}
        scores["bhakoot"] = 0.0 if bhakoot_diff in bad_combos else 7.0

        # 8. Nadi (8 points)
        n1 = moon1.nakshatra_index % 3
        n2 = moon2.nakshatra_index % 3
        scores["nadi"] = 8.0 if n1 != n2 else 0.0

        total = sum(scores.values())
        return {
            "total_score": round(total, 1),
            "max_score": 36,
            "percentage": round(total / 36 * 100, 1),
            "details": scores,
        }


# Module-level singleton
_engine: Optional[AstrologyEngine] = None


def get_astrology_engine() -> AstrologyEngine:
    global _engine
    if _engine is None:
        _engine = AstrologyEngine()
    return _engine
