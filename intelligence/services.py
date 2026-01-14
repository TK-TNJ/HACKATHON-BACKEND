"""
Intelligence Services - Core decision-making logic for LifeLink.

This module contains the "brain" of the emergency response system.
Supports both rule-based (fast) and LLM (intelligent) analysis.

Functions:
- calculate_urgency: Determines urgency score (0-100)
- classify_emergency: Categorizes emergency type
- analyze_sos: Main analysis function (rule-based)
- analyze_sos_hybrid: Enhanced analysis with LLM + fallback
"""

from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


# Emergency keywords for classification
EMERGENCY_KEYWORDS = {
    'medical': [
        'heart', 'attack', 'breathing', 'blood', 'unconscious', 'seizure',
        'stroke', 'allergic', 'reaction', 'choking', 'pain', 'chest',
        'diabetic', 'insulin', 'overdose', 'poison', 'injury', 'hurt',
        'bleeding', 'broken', 'fracture', 'burn', 'pregnant', 'labor',
        'faint', 'collapse', 'cpr', 'pulse', 'ambulance', 'hospital'
    ],
    'safety': [
        'attack', 'assault', 'robbery', 'theft', 'stalker', 'follow',
        'threat', 'weapon', 'gun', 'knife', 'danger', 'help', 'police',
        'intruder', 'break-in', 'violent', 'abuse', 'domestic', 'kidnap',
        'hostage', 'trapped', 'locked', 'fear', 'scared', 'unsafe'
    ],
    'accident': [
        'car', 'crash', 'accident', 'collision', 'hit', 'vehicle',
        'motorcycle', 'bicycle', 'pedestrian', 'road', 'traffic',
        'fire', 'explosion', 'smoke', 'building', 'collapse', 'fall',
        'drown', 'water', 'electric', 'shock', 'gas', 'leak'
    ],
    'emotional': [
        'suicide', 'self-harm', 'depressed', 'mental', 'crisis',
        'panic', 'anxiety', 'alone', 'desperate', 'hopeless',
        'scared', 'trauma', 'overwhelmed', 'breakdown'
    ]
}


def calculate_urgency(sos_data: dict) -> dict:
    """
    Calculate urgency score for an SOS request.
    
    Args:
        sos_data: Dictionary containing:
            - silent_mode: bool
            - description: str (optional)
            - created_at: datetime or str
            - latitude/longitude: float
            - is_bystander_report: bool
            - victim_condition: str
            - estimated_victims: int
            - card_urgency_boost: int (from selected card)
    
    Returns:
        Dictionary with:
            - urgency_score: int (0-100)
            - severity_level: str (critical/high/moderate/low)
            - urgency_factors: list of contributing factors
    """
    
    base_score = 50
    factors = []
    
    # Emergency Card Boost
    card_boost = sos_data.get('card_urgency_boost', 0)
    if card_boost > 0:
        base_score += card_boost
        factors.append(f"Emergency card selected (+{card_boost})")
    
    # Bystander Report Boost
    if sos_data.get('is_bystander_report', False):
        base_score += 25
        factors.append("Bystander report - victim unable to self-report (+25)")
    
    # Victim Condition
    victim_condition = sos_data.get('victim_condition', 'unknown')
    if victim_condition == 'unconscious':
        base_score += 15
        factors.append("Victim is unconscious/unresponsive (+15)")
    elif victim_condition == 'semi_conscious':
        base_score += 10
        factors.append("Victim is semi-conscious (+10)")
    
    # Multiple Victims
    estimated_victims = sos_data.get('estimated_victims', 1)
    if estimated_victims > 1:
        multi_victim_boost = min(estimated_victims * 5, 20)
        base_score += multi_victim_boost
        factors.append(f"Multiple victims ({estimated_victims}) (+{multi_victim_boost})")
    
    # Silent mode indicates serious danger
    if sos_data.get('silent_mode', False):
        base_score += 30
        factors.append("Silent mode activated (+30)")
    
    # Time of day - late night is higher risk
    created_at = sos_data.get('created_at')
    if created_at:
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = datetime.now()
        
        hour = created_at.hour
        if 22 <= hour or hour < 6:
            base_score += 20
            factors.append(f"Late night hour ({hour}:00) (+20)")
        elif 6 <= hour < 8 or 18 <= hour < 22:
            base_score += 10
            factors.append(f"Evening/early morning hour ({hour}:00) (+10)")
    
    # Keywords in description
    description = sos_data.get('description', '') or ''
    description_lower = description.lower()
    
    critical_keywords = ['unconscious', 'not breathing', 'heart attack', 
                         'stroke', 'weapon', 'gun', 'fire', 'suicide']
    high_keywords = ['blood', 'bleeding', 'attack', 'assault', 'crash',
                     'trapped', 'drowning', 'choking']
    
    for keyword in critical_keywords:
        if keyword in description_lower:
            base_score += 30
            factors.append(f"Critical keyword '{keyword}' (+30)")
            break
    else:
        for keyword in high_keywords:
            if keyword in description_lower:
                base_score += 15
                factors.append(f"High-priority keyword '{keyword}' (+15)")
                break
    
    # No description penalty (unless card selected)
    has_card = sos_data.get('card_urgency_boost', 0) > 0
    if not description and sos_data.get('silent_mode', False):
        base_score += 10
        factors.append("No description with silent mode (+10)")
    elif not description and not has_card:
        base_score -= 10
        factors.append("No description provided (-10)")
    
    # Cap score
    urgency_score = max(0, min(100, base_score))
    
    # Severity level
    if urgency_score >= 80:
        severity_level = 'critical'
    elif urgency_score >= 60:
        severity_level = 'high'
    elif urgency_score >= 40:
        severity_level = 'moderate'
    else:
        severity_level = 'low'
    
    return {
        'urgency_score': urgency_score,
        'severity_level': severity_level,
        'urgency_factors': factors
    }


def classify_emergency(sos_data: dict) -> dict:
    """
    Classify the type of emergency based on description and context.
    
    Returns:
        Dictionary with emergency_type, confidence, matched_keywords, reasoning
    """
    
    description = sos_data.get('description', '') or ''
    description_lower = description.lower()
    
    category_scores = {}
    category_keywords = {}
    
    for category, keywords in EMERGENCY_KEYWORDS.items():
        matches = [kw for kw in keywords if kw in description_lower]
        category_scores[category] = len(matches)
        category_keywords[category] = matches
    
    best_category = max(category_scores, key=category_scores.get)
    best_score = category_scores[best_category]
    
    if best_score == 0:
        if sos_data.get('silent_mode', False):
            return {
                'emergency_type': 'safety',
                'confidence': 0.6,
                'matched_keywords': [],
                'reasoning': 'Silent mode activated - assuming safety threat'
            }
        return {
            'emergency_type': 'unknown',
            'confidence': 0.0,
            'matched_keywords': [],
            'reasoning': 'No recognizable keywords'
        }
    
    total_keywords = sum(category_scores.values())
    confidence = round(min((best_score / max(total_keywords, 1)) * 1.5, 1.0), 2)
    
    return {
        'emergency_type': best_category,
        'confidence': confidence,
        'matched_keywords': category_keywords[best_category],
        'reasoning': f"Matched {best_score} {best_category}-related keywords"
    }


def analyze_sos(sos_data: dict) -> dict:
    """
    Main rule-based analysis function.
    
    Returns complete analysis with urgency, classification, skills, escalation flag.
    """
    
    urgency = calculate_urgency(sos_data)
    classification = classify_emergency(sos_data)
    
    skill_recommendations = {
        'medical': ['first_aid', 'cpr', 'emt', 'nurse', 'doctor'],
        'safety': ['security', 'self_defense', 'crisis_negotiation'],
        'accident': ['first_aid', 'firefighting', 'rescue'],
        'emotional': ['counseling', 'mental_health', 'crisis_support'],
        'unknown': ['first_aid', 'general']
    }
    
    recommended_skills = skill_recommendations.get(
        classification['emergency_type'], 
        ['general']
    )
    
    needs_authority = (
        urgency['severity_level'] == 'critical' or
        classification['emergency_type'] in ['safety', 'accident'] or
        urgency['urgency_score'] >= 85
    )
    
    return {
        'urgency_score': urgency['urgency_score'],
        'severity_level': urgency['severity_level'],
        'urgency_factors': urgency['urgency_factors'],
        'emergency_type': classification['emergency_type'],
        'classification_confidence': classification['confidence'],
        'matched_keywords': classification['matched_keywords'],
        'classification_reasoning': classification['reasoning'],
        'recommended_skills': recommended_skills,
        'needs_authority_escalation': needs_authority,
        'analysis_timestamp': datetime.now().isoformat(),
        'analysis_method': 'rule_based'
    }


def analyze_sos_hybrid(sos_data: dict, use_llm: bool = True) -> dict:
    """
    Hybrid analysis - LLM first with rule-based fallback.
    
    Token-optimized approach:
    1. Skip LLM if description empty or card selected
    2. Try Groq LLM analysis (fast, accurate)
    3. Fallback to rule-based on any failure
    4. Merge LLM insights with rule-based urgency
    
    Args:
        sos_data: SOS request data
        use_llm: Whether to attempt LLM analysis (default True)
    
    Returns:
        Enhanced analysis with panic_level, emotional_state if LLM used
    """
    
    # Always get rule-based analysis as baseline
    rule_result = analyze_sos(sos_data)
    
    # Check if we should skip LLM (token optimization)
    description = sos_data.get('description', '') or ''
    has_card = sos_data.get('card_urgency_boost', 0) > 0
    
    if not use_llm:
        logger.debug("LLM disabled by parameter")
        return rule_result
    
    if not description or len(description.strip()) < 5:
        logger.debug("Skipping LLM - no/short description")
        return rule_result
    
    if has_card:
        logger.debug("Skipping LLM - emergency card selected")
        return rule_result
    
    # Try LLM analysis
    try:
        from .groq_service import analyze_with_llm
        
        context = {
            'silent_mode': sos_data.get('silent_mode', False),
            'is_bystander': sos_data.get('is_bystander_report', False)
        }
        
        llm_result = analyze_with_llm(description, context, has_card)
        
        if llm_result:
            # Merge LLM insights with rule-based urgency
            merged = rule_result.copy()
            
            # Use LLM classification if confident
            if llm_result.get('emergency_type') != 'unknown':
                merged['emergency_type'] = llm_result['emergency_type']
                merged['classification_reasoning'] = llm_result.get('llm_reasoning', '')
            
            # Add LLM-specific fields
            merged['panic_level'] = llm_result.get('panic_level', 5)
            merged['emotional_state'] = llm_result.get('emotional_state', 'unknown')
            merged['llm_reasoning'] = llm_result.get('llm_reasoning', '')
            merged['analysis_method'] = 'hybrid'
            
            # Boost urgency if LLM detects high panic
            panic_level = llm_result.get('panic_level', 5)
            if panic_level >= 8:
                merged['urgency_score'] = min(100, merged['urgency_score'] + 15)
                merged['urgency_factors'].append(f"High panic detected by AI (+15)")
                if merged['urgency_score'] >= 80:
                    merged['severity_level'] = 'critical'
            
            # Use LLM skills if provided
            if llm_result.get('recommended_skills'):
                merged['recommended_skills'] = llm_result['recommended_skills']
            
            logger.info("Hybrid analysis complete with LLM enhancement")
            return merged
            
    except ImportError:
        logger.warning("Groq service not available")
    except Exception as e:
        logger.warning(f"LLM analysis failed, using rule-based: {e}")
    
    # Fallback to rule-based
    return rule_result
