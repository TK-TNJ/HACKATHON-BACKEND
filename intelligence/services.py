"""
Intelligence Services - Core decision-making logic for LifeLink.

This module contains the "brain" of the emergency response system.
All logic is rule-based (no ML) for MVP/hackathon simplicity.

Functions:
- calculate_urgency: Determines urgency score (0-100)
- classify_emergency: Categorizes emergency type
- analyze_sos: Main analysis function combining above
"""

from datetime import datetime
import re


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
    
    Returns:
        Dictionary with:
            - urgency_score: int (0-100)
            - severity_level: str (critical/high/moderate/low)
            - urgency_factors: list of contributing factors
    
    Scoring Logic:
        Base score: 50
        +30 for silent mode (indicates danger)
        +20 for late night hours (10pm - 6am)
        +10-30 for critical keywords
        -10 for vague/no description
    """
    
    base_score = 50
    factors = []
    
    # Factor 1: Silent mode indicates serious danger
    if sos_data.get('silent_mode', False):
        base_score += 30
        factors.append("Silent mode activated (+30)")
    
    # Factor 2: Time of day - late night is higher risk
    created_at = sos_data.get('created_at')
    if created_at:
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = datetime.now()
        
        hour = created_at.hour
        if 22 <= hour or hour < 6:  # 10 PM to 6 AM
            base_score += 20
            factors.append(f"Late night hour ({hour}:00) (+20)")
        elif 6 <= hour < 8 or 18 <= hour < 22:  # Early morning or evening
            base_score += 10
            factors.append(f"Evening/early morning hour ({hour}:00) (+10)")
    
    # Factor 3: Keywords in description
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
            break  # Only add bonus once
    else:
        for keyword in high_keywords:
            if keyword in description_lower:
                base_score += 15
                factors.append(f"High-priority keyword '{keyword}' (+15)")
                break
    
    # Factor 4: No description might indicate panic/inability to type
    if not description and sos_data.get('silent_mode', False):
        base_score += 10
        factors.append("No description with silent mode (+10)")
    elif not description:
        base_score -= 10
        factors.append("No description provided (-10)")
    
    # Cap score between 0 and 100
    urgency_score = max(0, min(100, base_score))
    
    # Determine severity level
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
    
    Args:
        sos_data: Dictionary containing:
            - description: str (optional)
            - silent_mode: bool
    
    Returns:
        Dictionary with:
            - emergency_type: str (medical/safety/accident/emotional/unknown)
            - confidence: float (0-1)
            - matched_keywords: list
    
    Classification Logic:
        - Count keyword matches for each category
        - Return category with most matches
        - Silent mode with no description defaults to 'safety'
    """
    
    description = sos_data.get('description', '') or ''
    description_lower = description.lower()
    
    # Count matches for each category
    category_scores = {}
    category_keywords = {}
    
    for category, keywords in EMERGENCY_KEYWORDS.items():
        matches = []
        for keyword in keywords:
            if keyword in description_lower:
                matches.append(keyword)
        category_scores[category] = len(matches)
        category_keywords[category] = matches
    
    # Find best matching category
    best_category = max(category_scores, key=category_scores.get)
    best_score = category_scores[best_category]
    
    # Handle edge cases
    if best_score == 0:
        # No keyword matches
        if sos_data.get('silent_mode', False):
            # Silent mode with no context suggests safety issue
            return {
                'emergency_type': 'safety',
                'confidence': 0.6,
                'matched_keywords': [],
                'reasoning': 'Silent mode activated without description - assuming safety threat'
            }
        else:
            return {
                'emergency_type': 'unknown',
                'confidence': 0.0,
                'matched_keywords': [],
                'reasoning': 'No recognizable keywords in description'
            }
    
    # Calculate confidence based on keyword matches
    total_keywords = sum(category_scores.values())
    confidence = best_score / max(total_keywords, 1)
    confidence = round(min(confidence * 1.5, 1.0), 2)  # Boost and cap at 1.0
    
    return {
        'emergency_type': best_category,
        'confidence': confidence,
        'matched_keywords': category_keywords[best_category],
        'reasoning': f"Matched {best_score} {best_category}-related keywords"
    }


def analyze_sos(sos_data: dict) -> dict:
    """
    Main analysis function - combines urgency and classification.
    
    This is the primary entry point for the intelligence system.
    
    Args:
        sos_data: Dictionary containing SOS request data
    
    Returns:
        Complete analysis with urgency score, classification, and recommendations
    """
    
    # Get urgency and classification
    urgency = calculate_urgency(sos_data)
    classification = classify_emergency(sos_data)
    
    # Add recommended skills based on emergency type
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
    
    # Determine if authority escalation is needed
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
        'analysis_timestamp': datetime.now().isoformat()
    }
