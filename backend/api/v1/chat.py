"""
💬 AI Chat API Endpoints
Handles conversational AI assistant for astrology queries with comprehensive Vedic knowledge
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from models.schemas import ChatMessage, ChatResponse, ChartData
from modules.veda_mind import get_veda_mind
from modules.jnana_hub.vedic_knowledge_base import knowledge_base
from modules.auth import get_current_user
import logging

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def send_message(message: ChatMessage, current_user: dict = Depends(get_current_user)):
    """
    Send a message to the AI astrology assistant with session-based conversation memory
    """
    try:
        veda_mind = get_veda_mind()
        
        # Use user ID as session ID for persistent conversations
        session_id = f"user_{current_user['user_id']}"
        
        # Generate response with conversation context
        response_text = veda_mind.generate_response(
            message=message.message,
            session_id=session_id,
            context=message.context
        )
        
        # Get contextual suggestions and related topics
        suggestions = veda_mind.get_suggestions(message.message, session_id)
        related_topics = veda_mind.get_related_topics(message.message)
        
        return ChatResponse(
            response=response_text,
            suggestions=suggestions,
            related_topics=related_topics
        )
    except Exception as e:
        logging.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

@router.post("/chart-question")
async def ask_chart_question(question: str, chart_data: ChartData):
    """
    Ask a specific question about a birth chart
    """
    try:
        answer = veda_mind.answer_question(question, chart_data)
        
        return {
            "question": question,
            "answer": answer,
            "chart_context": {
                "ascendant": chart_data.ascendant.value,
                "sun_sign": chart_data.sun_sign.value,
                "moon_sign": chart_data.moon_sign.value
            }
        }
    except Exception as e:
        logging.error(f"Error answering chart question: {e}")
        raise HTTPException(status_code=500, detail=f"Error answering chart question: {str(e)}")

@router.get("/suggestions")
async def get_chat_suggestions():
    """
    Get suggested questions for the AI assistant
    """
    try:
        suggestions = [
            "What does my Sun sign mean?",
            "How do I calculate my ascendant?",
            "What are the effects of planetary transits?",
            "Explain the concept of Nakshatras",
            "What is Guna Milan in compatibility?",
            "How do Dasha periods work?",
            "What are the different houses in astrology?",
            "How do I read my birth chart?",
            "What is the difference between Vedic and Western astrology?",
            "How do planetary aspects work?"
        ]
        
        return {"suggestions": suggestions}
    except Exception as e:
        logging.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@router.get("/topics")
async def get_chat_topics():
    """
    Get available chat topics and categories
    """
    try:
        topics = {
            "basics": {
                "name": "Astrology Basics",
                "description": "Fundamental concepts of Vedic astrology",
                "questions": [
                    "What is Vedic astrology?",
                    "How do I read my birth chart?",
                    "What are the 12 zodiac signs?"
                ]
            },
            "planets": {
                "name": "Planets",
                "description": "Understanding planetary influences",
                "questions": [
                    "What does each planet represent?",
                    "How do planets affect my life?",
                    "What is planetary strength?"
                ]
            },
            "houses": {
                "name": "Houses",
                "description": "The 12 houses and their meanings",
                "questions": [
                    "What do the houses represent?",
                    "How do I find my house placements?",
                    "Which house is most important?"
                ]
            },
            "compatibility": {
                "name": "Compatibility",
                "description": "Relationship and marriage compatibility",
                "questions": [
                    "How do I check compatibility?",
                    "What is Guna Milan?",
                    "Are we a good match?"
                ]
            },
            "transits": {
                "name": "Transits & Dasha",
                "description": "Planetary periods and movements",
                "questions": [
                    "What are planetary transits?",
                    "How do Dasha periods work?",
                    "What is my current Dasha?"
                ]
            }
        }
        
        return {"topics": topics}
    except Exception as e:
        logging.error(f"Error getting topics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting topics: {str(e)}")

def _normalize_tokens(text: str) -> List[str]:
    import re
    return re.findall(r"[a-z]+", text.lower())

def _fuzzy_has(text: str, keyword: str, cutoff: float = 0.85) -> bool:
    """Return True if text very likely contains the keyword (typo-tolerant)."""
    import difflib
    tokens = _normalize_tokens(text)
    if keyword in text.lower():
        return True
    return any(difflib.get_close_matches(tok, [keyword], n=1, cutoff=cutoff) for tok in tokens)

def _canonicalize_message_for_fuzzy(text: str) -> Optional[str]:
    """Return a canonicalized form of the message with typo-tolerant keyword normalization.

    Rules (aligned with tests):
    - Empty / whitespace-only input returns unchanged.
    - If no fuzzy matches are found, return original message unchanged.
    - If one or more keywords (possibly misspelled) are detected, ensure their canonical forms
      are present in the output. Preserve original message to keep numerals / punctuation.
    - Multiple typos should surface multiple canonical tokens (e.g. satturn + hous + mercuri).
    - Case-insensitive: different casing yields same canonical output when lowered.
    """
    if text == "" or text.isspace():
        return text  # Preserve empty/whitespace exactly

    candidates = [
        ("mars", ["mars", "mangal", "maanrs", "mras", "marg"]),
        ("mercury", ["mercury", "budha", "mercuri", "mercurry", "mercry", "mercu"]),
        ("jupiter", ["jupiter", "guru", "jupitr", "jupitar", "guruu", "jupitor", "juptr"]),
        ("venus", ["venus", "shukra", "venas", "venuse", "venuz", "venuss"]),
        ("saturn", ["saturn", "shani", "satturn", "satrun", "shanni", "saturnn"]),
        ("rahu", ["rahu", "rahoo", "rahuu"]),
        ("ketu", ["ketu", "ketuu", "ketoo"]),
        ("career", ["career", "job", "profession", "carrier", "kareer"]),
        ("marriage", ["marriage", "spouse", "partner", "mariage", "marrage", "marrige", "marriege"]),
        ("wealth", ["wealth", "money", "finance", "finanse"]),
        ("health", ["health", "disease", "illness", "helth"]),
        ("children", ["children", "kids", "pregnancy", "childrens"]),
        ("education", ["education", "study", "learning", "studies"]),
        ("remedy", ["remedy", "remedies", "solution", "mantra", "gemstone"]),
        ("dasha", ["dasha", "dasa", "dashaa"]),
        ("birth chart", ["birth chart", "kundali", "horoscope", "chart", "kundli", "kundli", "kundali"]),
        ("houses", ["houses", "bhava", "house", "hous", "haus"]),
        ("nakshatra", ["nakshatra", "nakshatras", "nakshatram", "lunar mansion", "constellation"]),
        ("ascendant", ["ascendant", "rising sign", "lagna", "ascendent", "asccendant"]),
        ("descendant", ["descendant", "descenddant"]),
        ("yoga", ["yoga", "raj yoga", "rajyoga", "raaj yoga", "yogga"]),
        ("dosha", ["dosha", "dossha", "mangal dosha", "manglik", "kuja dosha", "mangalik"]),
        ("transit", ["transit", "transits", "transist"]),
    ]

    text_lower = text.lower()
    tokens = _normalize_tokens(text)
    import difflib
    found = []
    for canonical, keys in candidates:
        # Direct substring match
        if any(k in text_lower for k in keys):
            found.append(canonical)
            continue
        # Typo-tolerant token match
        for tok in tokens:
            if any(difflib.get_close_matches(tok, [k], n=1, cutoff=0.85) for k in keys):
                found.append(canonical)
                break

    if not found:
        return text  # no changes

    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for f in found:
        if f not in seen:
            seen.add(f)
            ordered.append(f)

    # Append canonical tokens to original message so original context (numbers, punctuation) remains
    # Ensures tests find both canonical forms and original content
    return f"{text} " + " ".join(ordered)

def generate_ai_response(message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Generate AI response based on message and context using comprehensive knowledge base"""
    message_lower = message.lower()
    
    # Search knowledge base for relevant information
    search_results = knowledge_base.search(message)
    
    # If we found specific results, format them nicely
    if search_results["results"]:
        response_parts = []
        
        for result in search_results["results"]:
            result_type = result["type"]
            result_data = result["data"]
            
            if result_type == "planet":
                # Format planet information
                planet = result_data
                response = f"""
**{planet['name']}**

{planet['nature']}

**Key Significations:** {', '.join(planet['significations'][:10])}

**Exaltation:** {planet['exalted']} | **Debilitation:** {planet['debilitated']}
**Own Signs:** {', '.join(planet['own_signs'])}

**Positive Qualities:** {', '.join(planet['qualities']['positive'][:5])}
**Challenges:** {', '.join(planet['qualities']['negative'][:4])}

**Career Fields:** {', '.join(planet['career'][:6])}
**Body Parts:** {', '.join(planet['body_parts'][:5])}

**Day:** {planet['day']} | **Color:** {planet['color']} | **Gemstone:** {planet['gemstone']}

**Top Remedies:**
"""
                for i, remedy in enumerate(planet['remedies'][:4], 1):
                    response += f"{i}. {remedy}\n"
                
                # Add special information for certain planets
                if 'manglik_dosha' in planet:
                    response += f"\n**Manglik Dosha:** Mars in houses {', '.join(map(str, planet['manglik_dosha']['houses']))} creates Manglik Dosha affecting marriage. Effects include: {', '.join(planet['manglik_dosha']['effects'][:3])}"
                elif 'sade_sati' in planet:
                    response += f"\n**Sade Sati:** {planet['sade_sati']['description']}. Phases: {', '.join(planet['sade_sati']['phases'])}"
                elif 'mahadasha' in planet:
                    response += f"\n**Mahadasha Period:** {planet['mahadasha']}"
                
                response_parts.append(response.strip())
            
            elif result_type == "house":
                # Format house information
                house = result_data
                response = f"""
**{house['name']} ({house['sanskrit']})**

**Significations:** {', '.join(house['significations'][:8])}

**Natural Sign:** {house['natural_sign']} | **Natural Ruler:** {house['natural_ruler']} | **Karaka:** {house['karaka']}

**Interpretation:** {house['interpretation']}

**Special Nature:**"""
                if house.get('kendra'):
                    response += " Angular House (Kendra) - Very powerful"
                if house.get('trikona'):
                    response += " Trine House (Trikona) - Most auspicious"
                if house.get('upachaya'):
                    response += " Growth House (Upachaya) - Improves with time"
                if house.get('dusthana'):
                    response += " Challenging House (Dusthana) - Requires attention"
                if house.get('maraka'):
                    response += " Maraka House - Can cause obstacles"
                
                response += "\n\n**Planetary Placements:**\n"
                planets_info = house.get('planets_here', {})
                for planet_key, effect in planets_info.items():
                    if planet_key != 'general' and planet_key != 'benefics' and planet_key != 'malefics':
                        response += f"• **{planet_key.title()}:** {effect}\n"
                
                response_parts.append(response.strip())
            
            elif result_type == "yogas":
                # Format yoga information
                response = "**🌟 Vedic Astrology Yogas (Planetary Combinations)**\n\n"
                
                if "mangal dosha" in message_lower or "manglik" in message_lower:
                    dosha = knowledge_base.knowledge["doshas"]["manglik_dosha"]
                    response = f"""
**{dosha['name']}**

**Formation:** {dosha['formation']}

**Effects:** {', '.join(dosha['effects'])}

**Intensity Levels:**
• High: {dosha['intensity']['high']}
• Medium: {dosha['intensity']['medium']}

**Cancellation Conditions:**
"""
                    for i, cancel in enumerate(dosha['cancellations'], 1):
                        response += f"{i}. {cancel}\n"
                    
                    response += "\n**Remedies:**\n"
                    for i, remedy in enumerate(dosha['remedies'], 1):
                        response += f"{i}. {remedy}\n"
                
                elif "raj yoga" in message_lower:
                    raj = result_data["raj_yogas"]
                    response += f"**{raj['name']}**\n\n{raj['definition']}\n\n**Types:**\n"
                    for yoga_type in raj['types']:
                        response += f"\n• **{yoga_type['name']}:** {yoga_type['description']}\n  Results: {yoga_type['results']}"
                
                elif "dhana yoga" in message_lower or "wealth" in message_lower:
                    dhana = result_data["dhana_yogas"]
                    response += f"**{dhana['name']}**\n\n{dhana['definition']}\n\n**Types:**\n"
                    for yoga_type in dhana['types']:
                        response += f"\n• **{yoga_type['name']}:** {yoga_type['description']}\n  Results: {yoga_type['results']}"
                
                elif "pancha mahapurusha" in message_lower or "mahapurusha" in message_lower:
                    pancha = result_data["pancha_mahapurusha"]
                    response += f"**{pancha['name']}**\n\n{pancha['definition']}\n\n"
                    for yoga in pancha['types']:
                        response += f"\n**{yoga['name']}**\n"
                        response += f"Formation: {yoga['formation']}\n"
                        response += f"Results: {yoga['results']}\n"
                
                else:
                    # General yoga overview
                    response += "**Raj Yogas:** Combinations for power and authority\n"
                    response += "**Dhana Yogas:** Combinations for wealth\n"
                    response += "**Pancha Mahapurusha Yogas:** Five great person yogas\n"
                    response += "**Neecha Bhanga Raj Yoga:** Debilitation cancellation\n"
                
                response_parts.append(response.strip())
            
            elif result_type == "doshas":
                # Format dosha information
                response = "**⚠️ Vedic Astrology Doshas (Afflictions)**\n\n"
                
                if "kala sarpa" in message_lower:
                    dosha = result_data["kala_sarpa_dosha"]
                    response = f"""
**{dosha['name']}**

**Formation:** {dosha['formation']}
**Types:** {dosha['types']}

**Effects:** {', '.join(dosha['effects'])}

**Positive Aspect:** {dosha['positive_aspect']}

**Cancellation Conditions:**
"""
                    for i, cancel in enumerate(dosha['cancellations'], 1):
                        response += f"{i}. {cancel}\n"
                    
                    response += "\n**Remedies:**\n"
                    for i, remedy in enumerate(dosha['remedies'], 1):
                        response += f"{i}. {remedy}\n"
                
                elif "pitra dosha" in message_lower or "ancestral" in message_lower:
                    dosha = result_data["pitra_dosha"]
                    response = f"""
**{dosha['name']}**

**Formation:**
"""
                    for formation in dosha['formation']:
                        response += f"• {formation}\n"
                    
                    response += f"\n**Effects:** {', '.join(dosha['effects'])}\n"
                    response += "\n**Remedies:**\n"
                    for i, remedy in enumerate(dosha['remedies'], 1):
                        response += f"{i}. {remedy}\n"
                
                elif "nadi dosha" in message_lower:
                    dosha = result_data["nadi_dosha"]
                    response = f"""
**{dosha['name']}**

**Formation:** {dosha['formation']}
**Nadis:** {', '.join(dosha['nadis'])}

**Effects:** {dosha['effects']}
**Severity:** {dosha['severity']}

**Cancellation Conditions:**
"""
                    for i, cancel in enumerate(dosha['cancellations'], 1):
                        response += f"{i}. {cancel}\n"
                    
                    response += "\n**Remedies:**\n"
                    for i, remedy in enumerate(dosha['remedies'], 1):
                        response += f"{i}. {remedy}\n"
                
                else:
                    response += "**Mangal Dosha:** Mars in specific houses affecting marriage\n"
                    response += "**Kala Sarpa Dosha:** All planets between Rahu-Ketu axis\n"
                    response += "**Pitra Dosha:** Ancestral afflictions\n"
                    response += "**Nadi Dosha:** Same Nadi in compatibility matching\n"
                
                response_parts.append(response.strip())
            
            elif result_type == "compatibility":
                # Format compatibility information
                ashta = result_data["ashtakoota"]
                response = f"""
**{ashta['name']}**

Total Points: **{ashta['total_points']}**

**The 8 Koots (Factors):**

"""
                for koot in ashta['koots']:
                    response += f"**{koot['points']}. {koot['name']} ({koot['points']} points)**\n"
                    response += f"   {koot['description']}\n"
                    if 'types' in koot:
                        response += f"   Types: {', '.join(koot['types'][:5]) if isinstance(koot['types'], list) else koot['types']}\n"
                    response += f"   Matching: {koot['matching']}\n\n"
                
                response += "**Score Interpretation:**\n"
                interp = ashta['interpretation']
                response += f"• **Excellent:** {interp['excellent']}\n"
                response += f"• **Very Good:** {interp['very_good']}\n"
                response += f"• **Good:** {interp['good']}\n"
                response += f"• **Average:** {interp['average']}\n"
                response += f"• **Poor:** {interp['poor']}\n\n"
                response += f"**Note:** {ashta['note']}"
                
                response_parts.append(response.strip())
        
        if response_parts:
            return "\n\n---\n\n".join(response_parts)
    
    # Fallback to specific interpretations for common questions
    if "career" in message_lower or "job" in message_lower or "profession" in message_lower:
        return """
**Career in Vedic Astrology**

Career is analyzed through the **10th house** (Karma Bhava), its lord, and planets placed there.

**Planetary Career Indicators:**
• **Sun:** Government, administration, leadership, medicine, politics
• **Moon:** Public relations, hospitality, nursing, water business
• **Mars:** Military, police, engineering, surgery, sports, real estate
• **Mercury:** Business, trading, writing, teaching, communication, accounting
• **Jupiter:** Teaching, law, philosophy, priesthood, advisory, finance
• **Venus:** Arts, entertainment, fashion, hospitality, luxury goods
• **Saturn:** Labor work, service, construction, mining, occult, spirituality

The **10th lord's** strength and placement determine career success. **Dashas** (planetary periods) indicate timing of career changes and promotions.
"""
    
    elif "marriage" in message_lower or "spouse" in message_lower:
        return """
**Marriage in Vedic Astrology**

Marriage is analyzed through multiple factors:

**Primary Indicators:**
• **7th House:** Marriage, spouse, partnerships
• **7th Lord:** Spouse characteristics, marriage timing
• **Venus:** Karaka for wife (for men), romance, love
• **Jupiter:** Karaka for husband (for women), wisdom in marriage

**Compatibility Analysis:**
• **Guna Milan (Ashtakoota):** 36-point matching system
• **Mangal Dosha:** Mars in 1st, 4th, 7th, 8th, 12th houses
• **7th House Analysis:** Planets and aspects
• **Navamsa Chart (D9):** Marriage quality and spouse nature

**Minimum 18 points** in Guna Milan is recommended. Check for Mangal Dosha in both charts.
"""
    
    elif "dasha" in message_lower:
        return """
**Vimshottari Dasha System**

The Vimshottari Dasha is a 120-year planetary period system based on your Moon's nakshatra at birth.

**Planetary Periods (Mahadashas):**
• **Ketu:** 7 years - Spirituality, detachment, sudden events
• **Venus:** 20 years - Love, luxury, arts, marriage, comforts
• **Sun:** 6 years - Authority, career, recognition, father
• **Moon:** 10 years - Emotions, mind, mother, public
• **Mars:** 7 years - Energy, courage, property, conflicts
• **Rahu:** 18 years - Material gains, obsessions, foreign
• **Jupiter:** 16 years - Wisdom, children, fortune, spirituality
• **Saturn:** 19 years - Discipline, delays, hard work, karma
• **Mercury:** 17 years - Business, communication, intelligence

Each Mahadasha is divided into 9 **Antardashas** (sub-periods) of all planets. Results depend on planetary strength, placement, and aspects.
"""
    
    elif "sade sati" in message_lower:
        return """
**Sade Sati (Saturn's 7.5 Year Transit)**

Sade Sati occurs when **Saturn transits through:**
1. **12th house from Moon** (2.5 years) - Rising phase, expenses, losses
2. **Over the Moon sign** (2.5 years) - **Peak period**, maximum challenges
3. **2nd house from Moon** (2.5 years) - Setting phase, recovery begins

**Effects:**
• Delays and obstacles in all areas
• Financial challenges
• Health issues
• Relationship stress
• Mental pressure
• Hard work with slow results

**Positive Outcomes:**
• Maturity and wisdom
• Spiritual growth
• Karmic lessons learned
• Long-term stability
• Discipline and patience

**Remedies:**
• Chant Hanuman Chalisa daily
• Worship Lord Shani on Saturdays
• Donate black items, iron, oil
• Feed crows and poor people
• Practice patience and hard work
• Avoid major risks during peak period
"""
    
    elif "wealth" in message_lower or "money" in message_lower or "finance" in message_lower:
        return """
**Wealth in Vedic Astrology**

Wealth is analyzed through the **2nd house** (accumulated wealth), **11th house** (gains & income), and their lords.

**Planetary Wealth Indicators:**
• **Jupiter:** Prosperity, expansion, natural significator of wealth
• **Venus:** Luxury, material comforts, beautiful possessions
• **Mercury:** Business profits, trading income
• **Moon:** Public wealth, fluctuating income

The strength and placement of these planets, along with beneficial aspects, determine financial success. **Dhana Yogas** (wealth combinations) are special planetary combinations that bring significant wealth.
"""
    
    elif "health" in message_lower or "disease" in message_lower or "illness" in message_lower:
        return """
        Health in Vedic astrology is primarily analyzed through the 1st house (body), 6th house (diseases), 
        and 8th house (chronic ailments). The Ascendant and its lord show overall health and vitality. 
        The Sun represents vitality and heart, Moon governs mental health and fluids, Mars indicates accidents 
        and surgeries, Mercury affects nervous system, Jupiter relates to liver and fat, Venus shows kidneys 
        and reproductive health, and Saturn indicates chronic diseases and bones.
        """
    elif "children" in message_lower or "kids" in message_lower or "pregnancy" in message_lower:
        return """
        Children in Vedic astrology are analyzed through the 5th house (children & creativity), its lord, 
        and Jupiter (significator of children). The strength of the 5th house and Jupiter determines fertility, 
        number of children, and their well-being. For timing of childbirth, Dasha periods of 5th house lord, 
        Jupiter, or planets connected to the 5th house are considered. The condition of the Moon is also 
        important for conception and pregnancy.
        """
    elif "education" in message_lower or "study" in message_lower or "learning" in message_lower:
        return """
        Education in Vedic astrology is analyzed through the 4th house (foundational education), 5th house 
        (intelligence & higher learning), and 9th house (advanced studies & higher education). Mercury represents 
        analytical intelligence and learning ability, Jupiter shows wisdom and higher knowledge, and the Moon 
        governs memory and concentration. The strength of these houses and planets determines educational 
        success, field of study, and academic achievements.
        """
    
    # Remedies & Solutions
    elif any(k in message_lower for k in ["remedy", "remedies", "solution", "solutions", "mantra", "mantras", "gemstone", "gemstones"]):
        return """
        Vedic astrology offers various remedies to strengthen weak planets or reduce negative effects: 
        1) Gemstones worn on specific fingers amplify planetary energies, 2) Mantras chanted regularly 
        invoke planetary blessings, 3) Charity (dana) on specific days reduces karmic debt, 4) Fasting on 
        planet-specific days strengthens their positive effects, 5) Yantras (sacred geometry) harmonize 
        planetary energies, 6) Pujas and rituals performed by priests can mitigate doshas. Always consult 
        an experienced astrologer before starting remedies.
        """
    
    # House-specific questions
    elif "1st house" in message_lower or "first house" in message_lower:
        return """
        The 1st house (Ascendant/Lagna) represents your physical body, personality, appearance, and overall 
        approach to life. It shows your self-identity, health, vitality, and how you project yourself to the 
        world. The Ascendant sign and planets in the 1st house significantly shape your character and life path.
        """
    elif "7th house" in message_lower or "seventh house" in message_lower:
        return """
        The 7th house represents marriage, partnerships, spouse, and business collaborations. It shows the 
        nature of your life partner, marital happiness, and how you interact in one-on-one relationships. 
        The 7th house also governs contracts, agreements, and your public image in partnerships.
        """
    elif "10th house" in message_lower or "tenth house" in message_lower:
        return """
        The 10th house represents career, profession, social status, and public reputation. It shows your 
        achievements, ambitions, and how you're recognized in society. The 10th house governs your relationship 
        with authority figures, government, and your contribution to society. It's called the house of Karma 
        (action).
        """
    
    # Timing & Transits
    elif "transit" in message_lower or "gochara" in message_lower:
        return """
        Transits (Gochara) are the current movements of planets through the zodiac and their effects on your 
        birth chart. Major transits of Saturn (2.5 years per sign), Jupiter (1 year per sign), and Rahu-Ketu 
        (1.5 years per sign) create significant life changes. Transits activate the potential shown in your 
        birth chart. The transit of planets over your natal planets, Ascendant, or house cusps triggers events 
        in specific life areas.
        """
    elif "sade sati" in message_lower or "shani sade sati" in message_lower:
        return """
        Sade Sati is a 7.5-year period when Saturn transits the 12th, 1st, and 2nd houses from your natal 
        Moon. This challenging period brings life lessons, responsibilities, and karmic settling. The first 
        2.5 years affect mental peace, the middle 2.5 years impact health and finances, and the last 2.5 years 
        affect relationships. Despite its reputation, Sade Sati can bring maturity, discipline, and long-term 
        stability if faced with patience and hard work.
        """
    
    # Yogas (Special Combinations)
    elif "raj yoga" in message_lower or "rajyoga" in message_lower:
        return """
        Raj Yoga is a powerful combination in Vedic astrology formed when lords of Kendra houses (1st, 4th, 
        7th, 10th) and Trikona houses (1st, 5th, 9th) combine through conjunction, aspect, or exchange. 
        Raj Yogas bring power, authority, fame, and success. The strength of Raj Yoga depends on the planets 
        involved, their strength, and the Dasha periods activating them. Strong Raj Yogas can elevate a person 
        to positions of great influence and prosperity.
        """
    elif "mangal dosha" in message_lower or "manglik" in message_lower or "kuja dosha" in message_lower:
        return """
        Mangal Dosha (Kuja Dosha) occurs when Mars is placed in the 1st, 4th, 7th, 8th, or 12th house from 
        Ascendant, Moon, or Venus. This placement can create challenges in marriage, causing delays, conflicts, 
        or separation. However, the dosha's intensity varies based on Mars' sign, aspects, and other factors. 
        Remedies include marrying another Manglik person, performing specific rituals, or waiting for the 
        Dosha to cancel naturally after age 28. Not all Mars placements are equally problematic.
        """
    
    # Basic astrology knowledge
    elif "vedic astrology" in message_lower or "jyotish" in message_lower or "what is astrology" in message_lower:
        return """
        Vedic astrology (Jyotish) is an ancient Indian system of astrology that uses the sidereal zodiac 
        and focuses on the Moon's position. It provides insights into personality, life events, karma, and 
        spiritual growth through the analysis of planetary positions at the time of birth. Unlike Western 
        astrology, Vedic astrology uses the fixed star positions and emphasizes predictive techniques like 
        Dasha systems and divisional charts.
        """
    elif "birth chart" in message_lower or "kundali" in message_lower or "horoscope" in message_lower or "chart" in message_lower:
        return """
        A birth chart (Kundali/Kundli) is a map of the sky at the exact moment of your birth. It shows 
        the positions of planets in different zodiac signs and houses, revealing your personality, strengths, 
        challenges, and life path. To generate your chart, you need your exact birth date, time (accurate to 
        the minute), and birthplace. The chart includes the Ascendant, 12 houses, 9 planets, and 27 Nakshatras.
        """
    elif "zodiac signs" in message_lower or "zodiac sign" in message_lower or "rashi" in message_lower or "signs" in message_lower:
        return """
        The 12 zodiac signs (Rashis) in Vedic astrology are: Aries (Mesha), Taurus (Vrishabha), Gemini (Mithuna), 
        Cancer (Karka), Leo (Simha), Virgo (Kanya), Libra (Tula), Scorpio (Vrishchika), Sagittarius (Dhanu), 
        Capricorn (Makara), Aquarius (Kumbha), and Pisces (Meena). Each sign has unique characteristics, 
        qualities (cardinal/fixed/mutable), elements (fire/earth/air/water), and ruling planets that influence 
        personality and behavior.
        """
    elif "planets" in message_lower or "graha" in message_lower or "navagraha" in message_lower:
        return """
        In Vedic astrology, there are 9 planets (Navagrahas): Sun (Surya), Moon (Chandra), Mars (Mangal), 
        Mercury (Budha), Jupiter (Guru), Venus (Shukra), Saturn (Shani), Rahu (North Node), and Ketu (South Node). 
        Each planet represents different aspects of life and influences personality traits, life events, and 
        karma based on their position, strength, and aspects in your birth chart. Rahu and Ketu are shadow 
        planets (lunar nodes) but have powerful effects.
        """
    elif "houses" in message_lower or "bhava" in message_lower:
        return """
        The 12 houses (Bhavas) in Vedic astrology represent different areas of life: 1st (self/personality), 
        2nd (wealth/family), 3rd (courage/siblings), 4th (home/mother), 5th (children/creativity), 6th (health/enemies), 
        7th (marriage/partnerships), 8th (transformation/longevity), 9th (luck/dharma), 10th (career/status), 
        11th (gains/friendships), and 12th (losses/spirituality). Houses are divided into Kendra (angular), 
        Trikona (trinal), Upachaya (growth), and Dusthana (challenging) categories.
        """
    elif "nakshatra" in message_lower or "lunar mansion" in message_lower or "constellation" in message_lower:
        return """
        Nakshatras are the 27 (or 28) lunar mansions in Vedic astrology, each spanning 13°20'. They are 
        subdivisions of the zodiac that provide deeper insights into personality, destiny, and life patterns. 
        Each Nakshatra has a ruling deity, planetary lord, symbols, and unique characteristics. Your Moon's 
        Nakshatra (Janma Nakshatra) is particularly important for determining your mental nature, Dasha periods, 
        and compatibility. Nakshatras are used in naming ceremonies, muhurta (timing), and detailed predictions.
        """
    elif "compatibility" in message_lower or "guna milan" in message_lower or "match" in message_lower:
        return """
        Guna Milan (Ashtakoot) is the traditional Vedic compatibility system that evaluates 8 factors (Kootas) 
        between two birth charts, totaling 36 points: Varna (1), Vashya (2), Tara (3), Yoni (4), Graha Maitri (5), 
        Gana (6), Bhakoot (7), and Nadi (8). A score above 18 is acceptable, 18-24 is good, 24-32 is very good, 
        and 32-36 is excellent. However, modern astrologers also consider planetary positions, Mangal Dosha, 
        7th house strength, and overall chart compatibility beyond just Guna Milan.
        """
    elif "dasha" in message_lower or "mahadasha" in message_lower or "antardasha" in message_lower:
        return """
        Dasha systems are planetary time periods that predict when specific events will occur in your life. 
        The Vimshottari Dasha is most commonly used, spanning 120 years divided among 9 planets. Each planet's 
        Mahadasha (major period) runs for a fixed number of years (Sun: 6, Moon: 10, Mars: 7, Rahu: 18, Jupiter: 16, 
        Saturn: 19, Mercury: 17, Ketu: 7, Venus: 20), further divided into Antardashas (sub-periods) and 
        Pratyantardashas. The ruling Dasha lord activates specific houses and karmas in your chart.
        """
    
    # Default response for general questions
    else:
        # One-pass fuzzy fallback: try to canonicalize typos to a known intent
        try:
            if not (context and context.get("_no_fuzzy")):
                canonical = _canonicalize_message_for_fuzzy(message_lower)
                if canonical:
                    # Prevent infinite loops by marking this as a canonical reroute
                    return generate_ai_response(canonical, {"_no_fuzzy": True})
        except Exception:
            # If fuzzy routing fails for any reason, fall through to default
            pass

        return """
        I'm Yatin, your Vedic astrology AI assistant! I can help you with:
        
        🌟 Personal Analysis: Sun sign, Moon sign, Ascendant (Rising sign)
        🪐 Planets: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
        🏠 Houses: All 12 houses and their meanings
        ⭐ Nakshatras: 27 lunar mansions
        💑 Compatibility: Guna Milan, marriage analysis
        ⏰ Timing: Dashas, transits, Sade Sati
        🎯 Life Areas: Career, marriage, wealth, health, education, children
        ✨ Special Yogas: Raj Yoga, Mangal Dosha
        🔮 Remedies: Gemstones, mantras, rituals
        
        Feel free to ask me anything about Vedic astrology!
        """

def generate_suggestions(message: str) -> List[str]:
    """Generate follow-up suggestions based on the message"""
    message_lower = message.lower()
    
    # Specific planet suggestions
    if "mars" in message_lower:
        return ["Tell me about Mangal Dosha", "What about Mercury?", "How does Mars affect career?"]
    elif "jupiter" in message_lower:
        return ["What about wealth in astrology?", "Tell me about children", "What is Raj Yoga?"]
    elif "saturn" in message_lower:
        return ["What is Sade Sati?", "Tell me about career", "How do remedies work?"]
    elif "venus" in message_lower:
        return ["Tell me about marriage", "What about compatibility?", "How does Venus affect relationships?"]
    elif "rahu" in message_lower or "ketu" in message_lower:
        return ["What are transits?", "Tell me about Dasha periods", "What about spiritual growth?"]
    
    # Sign-related suggestions
    elif "sun sign" in message_lower:
        return ["What does my Moon sign mean?", "How do I calculate my ascendant?", "Tell me about planets"]
    elif "moon sign" in message_lower:
        return ["What does my Sun sign mean?", "What are Nakshatras?", "How do emotions affect life?"]
    elif "ascendant" in message_lower or "rising sign" in message_lower:
        return ["How do I generate my birth chart?", "What are the 12 houses?", "Tell me about planetary aspects"]
    
    # Life area suggestions
    elif "career" in message_lower or "job" in message_lower:
        return ["What about the 10th house?", "How does Jupiter affect career?", "When will career improve?"]
    elif "marriage" in message_lower or "spouse" in message_lower:
        return ["What is Guna Milan?", "Tell me about the 7th house", "What is Mangal Dosha?"]
    elif "wealth" in message_lower or "money" in message_lower:
        return ["What about Jupiter?", "Tell me about the 2nd house", "What are Dhana Yogas?"]
    elif "health" in message_lower:
        return ["What about the 6th house?", "How does Saturn affect health?", "What are health remedies?"]
    elif "children" in message_lower:
        return ["What about the 5th house?", "How does Jupiter affect children?", "When is good time for pregnancy?"]
    
    # House suggestions
    elif "house" in message_lower:
        return ["Tell me about the Ascendant", "What are Kendra houses?", "How do houses affect life?"]
    
    # Timing & predictions
    elif "dasha" in message_lower:
        return ["What are transits?", "How long is each Mahadasha?", "What is my current Dasha?"]
    elif "transit" in message_lower:
        return ["What is Sade Sati?", "How do Jupiter transits work?", "Tell me about Dasha periods"]
    elif "sade sati" in message_lower:
        return ["What are Saturn remedies?", "How long does Sade Sati last?", "What about Jupiter transits?"]
    
    # Yogas & doshas
    elif "raj yoga" in message_lower:
        return ["What are Kendra houses?", "How do I know if I have Raj Yoga?", "What about Dhana Yoga?"]
    elif "mangal dosha" in message_lower or "manglik" in message_lower:
        return ["What are dosha remedies?", "Can Mangal Dosha be cancelled?", "Tell me about marriage compatibility"]
    
    # Compatibility
    elif "compatibility" in message_lower or "guna milan" in message_lower:
        return ["What is Mangal Dosha?", "How many points are good?", "Tell me about the 7th house"]
    
    # Basic topics
    elif "birth chart" in message_lower or "kundali" in message_lower:
        return ["How do I generate my birth chart?", "What does my ascendant mean?", "Tell me about houses"]
    elif "planets" in message_lower or "navagraha" in message_lower:
        return ["What does Jupiter mean?", "Tell me about Saturn", "How do planets affect personality?"]
    elif "nakshatra" in message_lower:
        return ["What is my Nakshatra?", "How do Nakshatras work?", "Tell me about Moon sign"]
    elif "vedic astrology" in message_lower or "jyotish" in message_lower:
        return ["How do I generate my birth chart?", "What are Dashas?", "Tell me about houses"]
    elif "remedy" in message_lower or "gemstone" in message_lower:
        return ["What gemstone for Saturn?", "How do mantras work?", "Tell me about planetary strengths"]
    
    # Default suggestions
    else:
        return [
            "What does my Sun sign mean?",
            "Tell me about career in astrology",
            "What is Guna Milan?",
            "Explain Dasha periods"
        ]

def get_related_topics(message: str) -> List[str]:
    """Get related topics based on the message"""
    message_lower = message.lower()
    
    if "birth chart" in message_lower:
        return ["Planets", "Houses", "Ascendant", "Moon Sign"]
    elif "planets" in message_lower:
        return ["Planetary Strength", "Dasha Periods", "Transits", "Planetary Aspects"]
    elif "compatibility" in message_lower:
        return ["Guna Milan", "Marriage", "Relationships", "Love Compatibility"]
    else:
        return ["Vedic Astrology", "Birth Chart", "Planets", "Houses"]


