"""Advanced remedy recommendation engine with tracking.

Provides personalized remedy suggestions based on chart analysis,
tracks adherence and outcomes, and integrates with the prescription system.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RemedyCategory(str, Enum):
    GEMSTONE = "gemstone"
    MANTRA = "mantra"
    YANTRA = "yantra"
    CHARITY = "charity"
    PUJA = "puja"
    FASTING = "fasting"
    COLOR_THERAPY = "color_therapy"
    LIFESTYLE = "lifestyle"
    HERBAL = "herbal"


class RemedyPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RemedyDetail:
    category: RemedyCategory
    title: str
    description: str
    planet: str
    priority: RemedyPriority = RemedyPriority.MEDIUM
    duration_days: int = 40
    instructions: str = ""
    contraindications: str = ""
    expected_benefits: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "planet": self.planet,
            "priority": self.priority.value,
            "duration_days": self.duration_days,
            "instructions": self.instructions,
            "contraindications": self.contraindications,
            "expected_benefits": self.expected_benefits,
        }


# ---------------------------------------------------------------------------
# Remedy knowledge base
# ---------------------------------------------------------------------------

PLANETARY_REMEDIES: Dict[str, List[RemedyDetail]] = {
    "Sun": [
        RemedyDetail(RemedyCategory.GEMSTONE, "Ruby (Manik)", "Wear a natural ruby set in gold on the ring finger of the right hand on a Sunday during Shukla Paksha.", "Sun", RemedyPriority.HIGH, 0, "Minimum 3 carats. Energize before wearing.", "Not suitable if Sun is in the 6th, 8th, or 12th house.", "Boosts confidence, leadership, vitality."),
        RemedyDetail(RemedyCategory.MANTRA, "Surya Mantra", "Chant 'Om Hraam Hreem Hraum Sah Suryaya Namah' 7000 times over 40 days or 108 times daily.", "Sun", RemedyPriority.MEDIUM, 40, "Begin on a Sunday at sunrise facing east.", "", "Strengthens willpower and reduces Sun afflictions."),
        RemedyDetail(RemedyCategory.CHARITY, "Wheat & Jaggery Donation", "Donate wheat, jaggery, copper, and red cloth on Sundays.", "Sun", RemedyPriority.LOW, 0, "Donate before sunset.", "", "Reduces malefic Sun effects."),
    ],
    "Moon": [
        RemedyDetail(RemedyCategory.GEMSTONE, "Pearl (Moti)", "Wear a natural pearl set in silver on the little finger on a Monday.", "Moon", RemedyPriority.HIGH, 0, "Minimum 5 carats.", "Avoid if Moon is with Rahu/Ketu.", "Emotional balance, mental peace."),
        RemedyDetail(RemedyCategory.MANTRA, "Chandra Mantra", "Chant 'Om Shraam Shreem Shraum Sah Chandraya Namah' 11000 times over 40 days.", "Moon", RemedyPriority.MEDIUM, 40, "Begin on a Monday during Shukla Paksha.", "", "Calms the mind, improves intuition."),
        RemedyDetail(RemedyCategory.FASTING, "Monday Fasting", "Observe fast on Mondays, consuming only milk and fruits.", "Moon", RemedyPriority.LOW, 0, "Continue for at least 16 Mondays.", "Not for those with health conditions.", "Strengthens Moon, emotional stability."),
    ],
    "Mars": [
        RemedyDetail(RemedyCategory.GEMSTONE, "Red Coral (Moonga)", "Wear a red coral set in gold or copper on the ring finger on a Tuesday.", "Mars", RemedyPriority.HIGH, 0, "Minimum 6 carats. Triangular shape preferred.", "Avoid if Mars is malefic for your ascendant.", "Boosts courage, energy, property gains."),
        RemedyDetail(RemedyCategory.MANTRA, "Mangal Mantra", "Chant 'Om Kraam Kreem Kraum Sah Bhaumaya Namah' 10000 times over 40 days.", "Mars", RemedyPriority.MEDIUM, 40, "Begin on a Tuesday.", "", "Reduces Manglik dosha effects."),
        RemedyDetail(RemedyCategory.CHARITY, "Red Lentil Donation", "Donate red lentils, red cloth, and copper on Tuesdays.", "Mars", RemedyPriority.LOW, 0, "Donate to those in need.", "", "Pacifies Mars-related problems."),
    ],
    "Mercury": [
        RemedyDetail(RemedyCategory.GEMSTONE, "Emerald (Panna)", "Wear a natural emerald set in gold on the little finger on a Wednesday.", "Mercury", RemedyPriority.HIGH, 0, "Minimum 3.5 carats.", "Avoid if Mercury is in dusthana houses.", "Improves communication, intellect."),
        RemedyDetail(RemedyCategory.MANTRA, "Budh Mantra", "Chant 'Om Braam Breem Braum Sah Budhaya Namah' 9000 times over 40 days.", "Mercury", RemedyPriority.MEDIUM, 40, "Begin on a Wednesday.", "", "Enhances business skills, verbal ability."),
    ],
    "Jupiter": [
        RemedyDetail(RemedyCategory.GEMSTONE, "Yellow Sapphire (Pukhraj)", "Wear a yellow sapphire set in gold on the index finger on a Thursday.", "Jupiter", RemedyPriority.HIGH, 0, "Minimum 3 carats. Ceylon origin preferred.", "Not suitable if Jupiter is in 6th/8th/12th.", "Brings wisdom, prosperity, good fortune."),
        RemedyDetail(RemedyCategory.MANTRA, "Guru Mantra", "Chant 'Om Graam Greem Graum Sah Gurave Namah' 19000 times.", "Jupiter", RemedyPriority.MEDIUM, 40, "Begin on a Thursday during Pushya Nakshatra.", "", "Spiritual growth, academic success."),
        RemedyDetail(RemedyCategory.PUJA, "Guru Puja", "Perform special puja for Jupiter on Thursdays with yellow flowers and turmeric.", "Jupiter", RemedyPriority.MEDIUM, 0, "Visit a temple and offer bananas.", "", "Strengthens Jupiter blessings."),
    ],
    "Venus": [
        RemedyDetail(RemedyCategory.GEMSTONE, "Diamond (Heera)", "Wear a diamond set in platinum or silver on the middle finger on a Friday.", "Venus", RemedyPriority.HIGH, 0, "Minimum 0.5 carat. White Sapphire as alternative.", "Avoid if Venus is combust.", "Enhances love, luxury, artistic talents."),
        RemedyDetail(RemedyCategory.MANTRA, "Shukra Mantra", "Chant 'Om Draam Dreem Draum Sah Shukraya Namah' 16000 times.", "Venus", RemedyPriority.MEDIUM, 40, "Begin on a Friday.", "", "Improves relationships, material comforts."),
    ],
    "Saturn": [
        RemedyDetail(RemedyCategory.GEMSTONE, "Blue Sapphire (Neelam)", "Wear a blue sapphire set in silver or iron on the middle finger on a Saturday.", "Saturn", RemedyPriority.CRITICAL, 0, "MUST trial-test for 3 days before permanent wearing. Minimum 4 carats.", "Very powerful stone — test thoroughly first.", "Career stability, discipline, longevity."),
        RemedyDetail(RemedyCategory.MANTRA, "Shani Mantra", "Chant 'Om Praam Preem Praum Sah Shanaischaraya Namah' 23000 times.", "Saturn", RemedyPriority.HIGH, 40, "Begin on a Saturday at sunset.", "", "Reduces Sade Sati and Shani dasha effects."),
        RemedyDetail(RemedyCategory.CHARITY, "Oil & Iron Donation", "Donate black sesame seeds (til), iron, mustard oil, and dark cloth on Saturdays.", "Saturn", RemedyPriority.MEDIUM, 0, "Donate before sunset.", "", "Significantly reduces Saturn afflictions."),
    ],
    "Rahu": [
        RemedyDetail(RemedyCategory.GEMSTONE, "Hessonite (Gomed)", "Wear a hessonite garnet set in silver on the middle finger on a Saturday or Wednesday.", "Rahu", RemedyPriority.HIGH, 0, "Minimum 5 carats. Honey-colored preferred.", "Avoid if Rahu is well-placed.", "Protects from illusions, mental clarity."),
        RemedyDetail(RemedyCategory.MANTRA, "Rahu Mantra", "Chant 'Om Bhram Bhreem Bhroum Sah Rahave Namah' 18000 times.", "Rahu", RemedyPriority.MEDIUM, 40, "Begin during Rahu Kaal on a Saturday.", "", "Reduces confusion, material obsessions."),
    ],
    "Ketu": [
        RemedyDetail(RemedyCategory.GEMSTONE, "Cat's Eye (Lehsunia)", "Wear a cat's eye chrysoberyl set in silver on the middle finger.", "Ketu", RemedyPriority.HIGH, 0, "Minimum 3 carats. MUST trial-test.", "Very powerful — test for 3 days first.", "Spiritual progress, moksha, protection."),
        RemedyDetail(RemedyCategory.MANTRA, "Ketu Mantra", "Chant 'Om Sraam Sreem Sraum Sah Ketave Namah' 17000 times.", "Ketu", RemedyPriority.MEDIUM, 40, "Begin on a Tuesday or Saturday.", "", "Spiritual growth, past karma resolution."),
    ],
}


class RemedyEngine:
    """Generates remedy recommendations based on chart analysis."""

    def recommend_remedies(
        self,
        chart_data: Dict[str, Any],
        concerns: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate personalized remedy recommendations.

        Args:
            chart_data: Birth chart data with planets array.
            concerns: User-specified areas of concern (e.g., 'career', 'health', 'relationship').

        Returns:
            Sorted list of remedy recommendations.
        """
        recommendations: List[Dict[str, Any]] = []
        planets = chart_data.get("planets", [])

        for planet_info in planets:
            planet_name = planet_info.get("planet", "")
            remedies = PLANETARY_REMEDIES.get(planet_name, [])
            if not remedies:
                continue

            # Determine if planet needs remediation
            needs_remedy = self._assess_planet(planet_info, chart_data)
            if not needs_remedy:
                continue

            for remedy in remedies:
                rec = remedy.to_dict()
                rec["relevance_score"] = self._relevance_score(remedy, planet_info, concerns)
                recommendations.append(rec)

        # Sort by relevance (higher first), then priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(
            key=lambda r: (-r["relevance_score"], priority_order.get(r["priority"], 4))
        )
        return recommendations

    def _assess_planet(self, planet_info: Dict, chart_data: Dict) -> bool:
        """Determine if a planet needs remediation based on position."""
        # Planets that are retrograde often benefit from remedies
        if planet_info.get("is_retrograde"):
            return True

        # Check house placement — planets in dusthana houses (6, 8, 12) often need help
        sign_index = planet_info.get("sign_index", 0)
        houses = chart_data.get("houses", [])
        if houses:
            asc_sign = houses[0].get("sign", "") if isinstance(houses[0], dict) else ""
            # Simplified check
            if sign_index in {5, 7, 11}:  # 6th, 8th, 12th sign offsets (0-based)
                return True

        # Rahu/Ketu always benefit from remedies
        if planet_info.get("planet") in {"Rahu", "Ketu"}:
            return True

        # Saturn in challenging positions
        if planet_info.get("planet") == "Saturn":
            return True

        return False

    def _relevance_score(self, remedy: RemedyDetail, planet_info: Dict,
                         concerns: Optional[List[str]]) -> float:
        score = 50.0
        # Priority boost
        priority_boost = {"critical": 40, "high": 30, "medium": 20, "low": 10}
        score += priority_boost.get(remedy.priority.value, 0)

        # Retrograde planets get higher scores
        if planet_info.get("is_retrograde"):
            score += 15

        # Concern alignment
        if concerns:
            concern_planet_map = {
                "career": {"Saturn", "Sun", "Mars", "Jupiter"},
                "health": {"Sun", "Moon", "Mars"},
                "relationship": {"Venus", "Moon", "Jupiter"},
                "finance": {"Jupiter", "Venus", "Mercury"},
                "education": {"Mercury", "Jupiter"},
                "spiritual": {"Ketu", "Jupiter", "Moon"},
                "marriage": {"Venus", "Jupiter", "Moon"},
                "children": {"Jupiter", "Moon"},
            }
            for concern in concerns:
                relevant = concern_planet_map.get(concern.lower(), set())
                if remedy.planet in relevant:
                    score += 20
                    break

        return round(score, 1)

    def create_tracking_plan(self, remedies: List[Dict[str, Any]],
                              start_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Create a structured tracking plan for selected remedies."""
        start = start_date or datetime.utcnow()
        plan = []
        for i, remedy in enumerate(remedies):
            duration = remedy.get("duration_days", 40)
            if duration == 0:
                # Continuous remedies (gemstones etc.) — track quarterly
                duration = 90
            entry = {
                "remedy_id": i + 1,
                "title": remedy["title"],
                "category": remedy["category"],
                "planet": remedy["planet"],
                "start_date": start.isoformat(),
                "end_date": (start + timedelta(days=duration)).isoformat(),
                "duration_days": duration,
                "daily_tasks": self._generate_daily_tasks(remedy),
                "milestones": self._generate_milestones(duration),
                "status": "not_started",
                "adherence_percentage": 0.0,
            }
            plan.append(entry)
        return plan

    def _generate_daily_tasks(self, remedy: Dict[str, Any]) -> List[str]:
        category = remedy.get("category", "")
        if category == "mantra":
            return ["Complete mantra chanting session", "Record count", "Note any experiences"]
        elif category == "fasting":
            return ["Observe fast as prescribed", "Maintain dietary restrictions", "Meditate"]
        elif category == "charity":
            return ["Make donation as prescribed", "Record donation details"]
        elif category == "gemstone":
            return ["Wear gemstone as prescribed", "Clean and energize monthly"]
        elif category == "puja":
            return ["Perform puja with prescribed items", "Offer prayers"]
        return ["Follow prescribed remedy", "Track progress"]

    def _generate_milestones(self, duration: int) -> List[Dict[str, Any]]:
        milestones = []
        checkpoints = [7, 21, duration] if duration > 21 else [duration // 2, duration]
        for day in checkpoints:
            milestones.append({
                "day": day,
                "description": f"Day {day} checkpoint — assess progress and experiences",
                "completed": False,
            })
        return milestones


# Module-level singleton
_engine: Optional[RemedyEngine] = None


def get_remedy_engine() -> RemedyEngine:
    global _engine
    if _engine is None:
        _engine = RemedyEngine()
    return _engine
