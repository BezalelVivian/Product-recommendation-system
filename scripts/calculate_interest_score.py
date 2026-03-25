"""
Calculate Interest Score based on user actions

WEIGHTAGE SYSTEM:
- View: +1 point
- Hover 2-3s: +3 points
- Hover 3-5s: +5 points
- Hover 5s+: +10 points
- Click: +8 points
- Add to cart: +15 points
- Purchase: +25 points
- Search: +4 points

NEGATIVE:
- Click but no cart: -2
- Multiple views no action: -3
"""

def calculate_interest_score(action_type, hover_duration=0, metadata=None):
    """
    Calculate interest score based on action.
    
    Args:
        action_type: Type of action (view, hover, click, cart_add, purchase)
        hover_duration: Time in seconds (for hover events)
        metadata: Additional context
        
    Returns:
        Interest score (integer)
    """
    
    score = 0
    
    if action_type == 'view':
        score = 1
        
    elif action_type == 'hover':
        if hover_duration >= 5:
            score = 10  # Very interested
        elif hover_duration >= 3:
            score = 5   # Interested
        elif hover_duration >= 2:
            score = 3   # Somewhat interested
        else:
            score = 1   # Just passed by
            
    elif action_type == 'click':
        score = 8
        
    elif action_type == 'cart_add':
        score = 15
        
    elif action_type == 'purchase':
        score = 25
        
    elif action_type == 'search':
        score = 4
        
    elif action_type == 'cart_remove':
        score = -5  # Rejected
        
    elif action_type == 'view_multiple_no_action':
        score = -3  # Just browsing
    
    return score


def get_score_interpretation(score):
    """Get human-readable interpretation of score"""
    if score >= 20:
        return "🔥 VERY HIGH INTEREST"
    elif score >= 10:
        return "⚡ HIGH INTEREST"
    elif score >= 5:
        return "✓ MODERATE INTEREST"
    elif score >= 1:
        return "👀 LOW INTEREST"
    else:
        return "❌ NO INTEREST / REJECTED"


if __name__ == "__main__":
    # Test examples
    print("\n" + "="*60)
    print("📊 INTEREST SCORE CALCULATOR - TEST")
    print("="*60 + "\n")
    
    tests = [
        ("view", 0, "User just scrolled past"),
        ("hover", 2.5, "Quick hover"),
        ("hover", 4.2, "Moderate hover"),
        ("hover", 6.8, "Long hover - very interested!"),
        ("click", 0, "User clicked product"),
        ("cart_add", 0, "Added to cart"),
        ("purchase", 0, "Completed purchase"),
    ]
    
    for action, duration, description in tests:
        score = calculate_interest_score(action, duration)
        interpretation = get_score_interpretation(score)
        
        if duration > 0:
            print(f"{action.upper()} ({duration}s): {score} points - {interpretation}")
        else:
            print(f"{action.upper()}: {score} points - {interpretation}")
        print(f"  → {description}")
        print()