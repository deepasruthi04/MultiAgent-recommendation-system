import logging
from mcp_server import get_user_history

logger = logging.getLogger("UserBehaviorAgent")

class UserBehaviorAgent:
    """
    Analyzes historical customer reviews, clicks, and behavior records in MongoDB.
    Generates a dynamic user profile containing loyalty status, budget bias, and category affinity.
    """
    def __init__(self):
        pass

    async def analyze(self, user_id: str) -> dict:
        logger.info(f"Analyzing behavior history for user: {user_id}")
        
        # Handle cold-start new users
        if not user_id:
            return {
                "user_id": "NEW_USER",
                "tier": "Bronze",
                "category_bias": "General",
                "budget_tier": "Flexible",
                "avg_rating_given": 5.0,
                "history_summary": "First-time visitor with no prior shopping records. Cold-start recommendation rules applied."
            }

        # Retrieve reviews history written by this user
        history = await get_user_history(user_id)
        
        if not history:
            return {
                "user_id": user_id,
                "tier": "Bronze",
                "category_bias": "General",
                "budget_tier": "Flexible",
                "avg_rating_given": 5.0,
                "history_summary": f"User ID '{user_id}' has no historical purchases. General RAG suggestions enabled."
            }

        # 1. Determine Loyalty Tier based on historical reviews count
        review_count = len(history)
        if review_count >= 4:
            tier = "Gold"
        elif review_count >= 1:
            tier = "Silver"
        else:
            tier = "Bronze"

        # 2. Determine Category Bias and Average Rating Given
        scores = []
        pet_toy_words = ["toy", "ball", "puppet", "alligator", "bite", "tunnel"]
        aquarium_words = ["clarifier", "fish", "pond", "aquarium", "marine", "test kit", "silicone"]
        apparel_words = ["collar", "shirt", "apparel", "harness", "leash", "boots"]
        food_words = ["treat", "oil", "food", "supplement", "chews", "salmon", "potato"]
        habitat_words = ["bedding", "cedar", "cage", "stairs", "feeder","kennel"]
        
        toy_hits = 0
        fish_hits = 0
        apparel_hits = 0
        food_hits = 0
        habitat_hits = 0
        
        profile_name = history[0].get("profile_name", f"User {user_id}")
        
        for r in history:
            score = r.get("score", 5.0)
            scores.append(score)
            
            text = (r.get("summary", "") + " " + r.get("review_text", "")).lower()
            if any(w in text for w in pet_toy_words):
                toy_hits += 1
            if any(w in text for w in aquarium_words):
                fish_hits += 1
            if any(w in text for w in apparel_words):
                apparel_hits += 1
            if any(w in text for w in food_words):
                food_hits += 1
            if any(w in text for w in habitat_words):
                habitat_hits += 1

        avg_rating = round(sum(scores) / len(scores), 2) if scores else 5.0

        # Classify the primary category interest
        hits = {
            "Pet Toys": toy_hits,
            "Aquarium & Fish Care": fish_hits,
            "Apparel & Collars": apparel_hits,
            "Food & Supplements": food_hits,
            "Habitat & Bedding": habitat_hits
        }
        max_category = max(hits, key=hits.get)
        if hits[max_category] == 0:
            category_bias = "General"
        else:
            category_bias = max_category

        # Formulate history summary text
        history_summary = (
            f"Active customer '{profile_name}' (Tier: {tier}). Has posted {review_count} reviews "
            f"with an average rating of {avg_rating} stars. Showing strong preference for '{category_bias}'."
        )

        return {
            "user_id": user_id,
            "profile_name": profile_name,
            "tier": tier,
            "category_bias": category_bias,
            "avg_rating_given": avg_rating,
            "review_count": review_count,
            "history_summary": history_summary
        }
