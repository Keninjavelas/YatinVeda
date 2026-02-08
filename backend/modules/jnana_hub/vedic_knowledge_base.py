"""
Vedic Knowledge Base
Centralized repository of Vedic astrology concepts and principles
"""

knowledge_base = {
    "nakshatras": {
        "description": "27 lunar mansions in Vedic astrology",
        "count": 27,
        "significance": "Determines specific qualities and predictions"
    },
    "planets": {
        "grahas": ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"],
        "description": "Nine celestial bodies influencing human life"
    },
    "houses": {
        "bhavas": 12,
        "description": "12 divisions of the birth chart representing life areas"
    },
    "doshas": {
        "types": ["Vata", "Pitta", "Kapha"],
        "description": "Constitutional types in Ayurveda, linked to astrology"
    },
    "yogas": {
        "description": "Planetary combinations indicating specific life outcomes",
        "examples": ["Raj Yoga", "Dhana Yoga", "Gajakesari Yoga"]
    },
    "dashas": {
        "description": "Planetary periods timing life events",
        "primary_system": "Vimshottari Dasha"
    }
}


def get_concept(topic: str) -> dict:
    """Retrieve knowledge base entry for a topic"""
    return knowledge_base.get(topic.lower(), {"description": "Concept not found in knowledge base"})


def search_knowledge(query: str) -> list:
    """Search knowledge base for matching topics"""
    query_lower = query.lower()
    matches = []
    for topic, data in knowledge_base.items():
        if query_lower in topic or query_lower in str(data).lower():
            matches.append({
                "topic": topic,
                "data": data
            })
    return matches


def get_relevant_context(query: str) -> str:
    """
    Get relevant Vedic knowledge context for a given query
    
    Args:
        query: User's question or topic
    
    Returns:
        Formatted string with relevant knowledge base information
    """
    import json
    
    # Search knowledge base for matching topics
    matches = search_knowledge(query)
    
    if not matches:
        # Return default context for unmatched queries
        return ""
    
    # Format matched knowledge into readable context
    context_parts = []
    for match in matches[:3]:  # Limit to top 3 matches
        topic = match["topic"].title()
        data = match["data"]
        
        if isinstance(data, dict):
            # Format dictionary data
            lines = [f"**{topic}:**"]
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    lines.append(f"- {key.title()}: {json.dumps(value)}")
                else:
                    lines.append(f"- {key.title()}: {value}")
            context_parts.append("\n".join(lines))
        else:
            context_parts.append(f"**{topic}:** {data}")
    
    return "\n\n".join(context_parts)

