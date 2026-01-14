"""
Response Services - Matching and Coordination Logic

This module contains the logic for matching SOS requests
to the best available responders.
"""

from typing import List, Dict, Optional
from decimal import Decimal
import math

from accounts.models import ResponderProfile
from sos.models import SOSRequest


def calculate_distance(lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal) -> float:
    """
    Calculate approximate distance between two coordinates in kilometers.
    Uses Haversine formula for accuracy.
    """
    
    # Convert to floats for math operations
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    
    # Earth's radius in kilometers
    R = 6371
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def find_matching_responders(
    sos: SOSRequest,
    required_skills: Optional[List[str]] = None,
    max_distance_km: float = 50.0,
    limit: int = 10
) -> List[Dict]:
    """
    Find responders matching the SOS request requirements.
    
    Matching priorities (in order):
    1. Skills match (if required_skills provided)
    2. Availability
    3. Reputation score
    4. Distance (if responder has location data)
    
    Args:
        sos: The SOS request to match
        required_skills: Optional list of required skills
        max_distance_km: Maximum distance to consider (default 50km)
        limit: Maximum number of responders to return
    
    Returns:
        List of dictionaries with responder info and match score
    """
    
    # Start with available responders only
    responders = ResponderProfile.objects.filter(
        is_available=True
    ).select_related('user')
    
    matched = []
    
    for responder in responders:
        match_info = {
            'responder_id': responder.id,
            'user_id': responder.user.id,
            'supabase_user_id': responder.user.supabase_user_id,
            'skills': responder.skills,
            'reputation_score': responder.reputation_score,
            'match_score': 0,
            'match_reasons': []
        }
        
        # Score 1: Skill matching (most important)
        if required_skills:
            responder_skills = set(responder.skills) if responder.skills else set()
            required_set = set(required_skills)
            matched_skills = responder_skills.intersection(required_set)
            
            if matched_skills:
                skill_score = (len(matched_skills) / len(required_set)) * 50
                match_info['match_score'] += skill_score
                match_info['matched_skills'] = list(matched_skills)
                match_info['match_reasons'].append(
                    f"Skills match: {', '.join(matched_skills)}"
                )
            else:
                # No skill match - lower priority but still include
                match_info['match_reasons'].append("No skill match")
        else:
            # No skills required - give base score
            match_info['match_score'] += 25
            match_info['match_reasons'].append("No specific skills required")
        
        # Score 2: Reputation (adds up to 30 points)
        reputation_score = (responder.reputation_score / 100) * 30
        match_info['match_score'] += reputation_score
        match_info['match_reasons'].append(
            f"Reputation: {responder.reputation_score}/100"
        )
        
        # Score 3: Distance (adds up to 20 points, if location available)
        if (responder.last_known_latitude and responder.last_known_longitude):
            distance = calculate_distance(
                sos.latitude, sos.longitude,
                responder.last_known_latitude, responder.last_known_longitude
            )
            match_info['distance_km'] = round(distance, 2)
            
            if distance <= max_distance_km:
                # Closer = higher score (inverse relationship)
                distance_score = (1 - (distance / max_distance_km)) * 20
                match_info['match_score'] += distance_score
                match_info['match_reasons'].append(
                    f"Distance: {round(distance, 1)} km"
                )
            else:
                match_info['match_reasons'].append(
                    f"Distance: {round(distance, 1)} km (beyond range)"
                )
        else:
            match_info['distance_km'] = None
            match_info['match_reasons'].append("Location unknown")
        
        # Round final score
        match_info['match_score'] = round(match_info['match_score'], 1)
        matched.append(match_info)
    
    # Sort by match score (highest first)
    matched.sort(key=lambda x: x['match_score'], reverse=True)
    
    return matched[:limit]


def assign_responder(sos: SOSRequest, responder: ResponderProfile) -> 'ResponderAssignment':
    """
    Assign a responder to an SOS request.
    
    Creates a ResponderAssignment record and updates SOS status.
    
    Args:
        sos: The SOS request
        responder: The responder to assign
    
    Returns:
        The created ResponderAssignment
    """
    from .models import ResponderAssignment
    
    # Create assignment
    assignment = ResponderAssignment.objects.create(
        sos=sos,
        responder=responder,
        status='assigned'
    )
    
    # Update SOS status
    sos.status = 'assigned'
    sos.save()
    
    return assignment


def escalate_to_authority(
    sos: SOSRequest,
    authority_type: str,
    reason: str
) -> 'AuthorityEscalation':
    """
    Escalate an SOS to authorities.
    
    For MVP, this creates a record. In production, this would
    integrate with actual emergency services APIs.
    
    Args:
        sos: The SOS request to escalate
        authority_type: Type of authority (police/fire/medical/other)
        reason: Reason for escalation
    
    Returns:
        The created AuthorityEscalation record
    """
    from .models import AuthorityEscalation
    import uuid
    
    # Create mock reference ID
    mock_reference = f"MOCK-{authority_type.upper()}-{uuid.uuid4().hex[:8].upper()}"
    
    escalation = AuthorityEscalation.objects.create(
        sos=sos,
        authority_type=authority_type,
        reason=reason,
        authority_reference=mock_reference
    )
    
    return escalation
