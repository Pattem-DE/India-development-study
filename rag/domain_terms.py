"""
Domain-specific terminology mapping for Indian government policy documents.
Many scheme names use Hindi/Sanskrit words that don't semantically match
their English equivalents in vector search - this bridges that gap.
"""

INDIA_POLICY_SYNONYMS = {
    "health": ["arogya", "swasthya", "ayushman"],
    "healthcare": ["arogya", "swasthya seva", "ayushman bharat"],
    "welfare": ["kalyan", "seva"],
    "development": ["vikas", "unnati"],
    "self-reliant": ["atmanirbhar"],
    "clean": ["swachh"],
    "skill": ["kaushal"],
    "employment": ["rozgar"],
    "education": ["shiksha", "vidya"],
    "housing": ["awas"],
    "rural": ["gramin"],
    "digital": ["digital india"],
    "farmer": ["kisan"],
    "youth": ["yuva"],
    "women": ["mahila"],
    "energy": ["urja"],
    "water": ["jal"],
    "food": ["anna", "khadya"],
    "insurance": ["bima"],
    "pension": ["pension yojana"],
    "startup": ["startup india", "udyam"],
}

def expand_query(query):
    """
    Expand a query with Hindi/Sanskrit policy terms if any English
    keyword in the query has a known equivalent used in scheme names.
    """
    query_lower = query.lower()
    additional_terms = []

    for english_term, hindi_terms in INDIA_POLICY_SYNONYMS.items():
        if english_term in query_lower:
            additional_terms.extend(hindi_terms)

    if additional_terms:
        expanded = f"{query} ({', '.join(set(additional_terms))})"
        return expanded
    return query
