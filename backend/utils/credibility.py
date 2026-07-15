import json
from database.models import NewsArticle, NewsSource

class CredibilityEngine:
    # Base scores for publisher reliability
    SOURCE_RELIABILITY = {
        "pib_news": 100,
        "gov_news": 100,
        "police_news": 95,
        "national_news": 85,
        "state_news": 80,
        "google_news": 75,
        "hindi_news": 70,
        "district_news": 65,
        "rss": 60
    }

    @classmethod
    def calculate_score(cls, article: NewsArticle, source: NewsSource) -> int:
        """
        Calculates a dynamic credibility score from 0-100.
        """
        score = 0
        
        # 1. Publisher Reliability (Base Score)
        base_score = cls.SOURCE_RELIABILITY.get(source.type, 50)
        score += base_score
        
        # 2. Number of trusted sources (References/Consensus)
        ref_count = 0
        has_gov_confirmation = False
        
        if article.references:
            try:
                refs = json.loads(article.references)
                ref_count = len(refs)
                
                # Scan URLs for government indicators
                for ref in refs:
                    ref_lower = ref.lower()
                    if ".gov.in" in ref_lower or "pib" in ref_lower or "police" in ref_lower:
                        has_gov_confirmation = True
            except:
                pass
                
        # Add 5 points for every additional source that covered it, up to 20 points
        score += min(ref_count * 5, 20)
        
        # 3. Government confirmation bonus
        if has_gov_confirmation or source.type in ["pib_news", "gov_news", "police_news"]:
            score += 15
            
        # Cap at 100
        return min(score, 100)

    @classmethod
    def generate_fact_check_report(cls, article: NewsArticle, source: NewsSource) -> dict:
        """
        Generates a human-readable Fact Check Helper report.
        """
        score = cls.calculate_score(article, source)
        
        status = "Needs Verification"
        if score >= 90:
            status = "Highly Credible"
        elif score >= 75:
            status = "Credible"
        elif score >= 50:
            status = "Moderate"
            
        has_multiple = False
        if article.references:
            try:
                refs = json.loads(article.references)
                has_multiple = len(refs) > 0
            except:
                pass

        return {
            "credibility_score": score,
            "status": status,
            "publisher_type": source.type,
            "has_multiple_sources": has_multiple,
            "is_government_confirmed": (score >= 90 and (source.type in ["pib_news", "gov_news", "police_news"] or cls._has_gov_refs(article)))
        }

    @staticmethod
    def _has_gov_refs(article: NewsArticle) -> bool:
        if not article.references:
            return False
        try:
            refs = json.loads(article.references)
            for ref in refs:
                ref_lower = ref.lower()
                if ".gov.in" in ref_lower or "pib" in ref_lower or "police" in ref_lower:
                    return True
        except:
            pass
        return False
