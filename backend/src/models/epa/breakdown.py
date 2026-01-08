"""
FTC EPA Breakdown Processing

Handles score breakdown processing for FTC EPA calculations.
"""

from typing import Any, List

import numpy as np

from src.db.models import Year
from src.models.epa.math import unit_sigmoid
from src.ftc.breakdown import all_keys, get_keys


def post_process_breakdown(
    year: int, key: str, breakdown: Any, opp_breakdown: Any
) -> Any:
    """
    Post-process breakdown predictions for FTC scoring.
    
    FTC doesn't have ranking points like FRC, so this is simpler.
    We just ensure values are within reasonable bounds.
    
    Args:
        year: Season year
        key: Match key
        breakdown: Predicted breakdown array for this alliance
        opp_breakdown: Predicted breakdown array for opponent
    
    Returns:
        Processed breakdown array
    """
    keys = get_keys(year)
    
    # Ensure all component scores are non-negative
    for i in range(len(breakdown)):
        if breakdown[i] < 0:
            breakdown[i] = 0
    
    # Total points should be sum of components (index 0)
    # Auto, teleop, endgame are indices 1, 2, 3
    if len(breakdown) >= 4:
        component_sum = breakdown[1] + breakdown[2] + breakdown[3]
        # Adjust total if components don't match
        if abs(breakdown[0] - component_sum) > 1:
            breakdown[0] = component_sum
    
    return breakdown


def post_process_attrib(year: int, attrib: Any) -> Any:
    """
    Post-process EPA attribution after match.
    
    Args:
        year: Season year
        attrib: Attribution array
    
    Returns:
        Processed attribution
    """
    # Ensure attribution values are reasonable
    for i in range(len(attrib)):
        # Clamp extreme values
        attrib[i] = np.clip(attrib[i], -50, 50)
    
    return attrib


def get_score_from_breakdown(
    key: str,
    year: int,
    breakdown: Any,
    opp_breakdown: Any,
    rp_1: float = 0,
    rp_2: float = 0,
    rp_3: float = 0,
    elim: bool = False,
) -> float:
    """
    Calculate predicted score from breakdown.
    
    For FTC, the score is simply the total_points (index 0).
    
    Args:
        key: Match key
        year: Season year
        breakdown: Score breakdown array
        opp_breakdown: Opponent breakdown array
        rp_1, rp_2, rp_3: Ranking point predictions (not used in FTC)
        elim: Whether this is an elimination match
    
    Returns:
        Predicted score
    """
    # Total points is always index 0
    return float(breakdown[0])


def get_breakdown_mean(breakdowns: List[Any]) -> Any:
    """
    Calculate mean breakdown across multiple matches.
    
    Args:
        breakdowns: List of breakdown arrays
    
    Returns:
        Mean breakdown array
    """
    if not breakdowns:
        return None
    return np.mean(breakdowns, axis=0)


def calculate_component_epa(
    team_breakdown: Any,
    alliance_breakdown: Any,
    num_teams: int = 2,
) -> Any:
    """
    Calculate per-component EPA contribution.
    
    Assumes equal contribution from each team on the alliance.
    
    Args:
        team_breakdown: Team's breakdown contribution
        alliance_breakdown: Full alliance breakdown
        num_teams: Number of teams on alliance (2 for FTC)
    
    Returns:
        Estimated team contribution array
    """
    # Simple assumption: each team contributes equally
    return alliance_breakdown / num_teams


def breakdown_diff(actual: Any, predicted: Any) -> Any:
    """
    Calculate difference between actual and predicted breakdown.
    
    Args:
        actual: Actual score breakdown
        predicted: Predicted breakdown
    
    Returns:
        Difference array (actual - predicted)
    """
    return np.array(actual) - np.array(predicted)
