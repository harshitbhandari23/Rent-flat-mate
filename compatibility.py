import os, json

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

def rule_based_score(profile, listing):
    """Fallback scoring: budget fit (60%) + location match (40%)."""
    score = 0
    if profile.budget_min <= listing.rent <= profile.budget_max:
        score += 60
    else:
        diff = min(abs(listing.rent - profile.budget_min), abs(listing.rent - profile.budget_max))
        span = max(profile.budget_max - profile.budget_min, 1)
        score += max(0, 60 - int(60 * diff / span))
    if profile.preferred_location.strip().lower() in listing.location.strip().lower() or \
       listing.location.strip().lower() in profile.preferred_location.strip().lower():
        score += 40
    score = max(0, min(100, score))
    explanation = f"Rule-based match: rent Rs.{listing.rent} vs budget Rs.{profile.budget_min}-{profile.budget_max}, location '{listing.location}' vs preferred '{profile.preferred_location}'."
    return score, explanation

def get_compatibility_score(profile, listing):
    if not ANTHROPIC_API_KEY:
        return rule_based_score(profile, listing)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = f"""Given this room listing: location={listing.location}, rent={listing.rent}, room_type={listing.room_type}, furnishing={listing.furnishing}, available_from={listing.available_from}
and this tenant profile: preferred_location={profile.preferred_location}, budget_min={profile.budget_min}, budget_max={profile.budget_max}, move_in_date={profile.move_in_date}

Compute a compatibility score from 0 to 100 based on budget and location match.
Return ONLY JSON: {{"score": number, "explanation": string}}"""
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = resp.content[0].text.strip()
        text = text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        return int(data['score']), data['explanation']
    except Exception as e:
        print(f"LLM scoring failed, using fallback: {e}")
        return rule_based_score(profile, listing)
