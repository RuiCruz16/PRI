from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import traceback
import os
import utils

app = FastAPI()

# Configuration
SOLR_CORE_URL = "http://localhost:8983/solr/your_core_name/select"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORRECT URL based on your previous messages
SOLR_CORE_URL = os.getenv("SOLR_URL", "http://localhost:8984/solr/diseases/select")

def merge_highlighting(doc, highlights):
    """
    Safely merges Solr highlights into the document.
    Solr highlighting keys usually match the document's Unique Key.
    """
    if not highlights:
        return doc
        
    # 1. Try to find the Unique ID of this doc
    # Solr usually returns the unique key as the dictionary key in 'highlighting'
    # We try common field names for the ID:
    doc_id = doc.get("id") or doc.get("source_url") or doc.get("disease_name")
    
    # If we still can't find an ID, we can't map the highlight
    if not doc_id:
        return doc

    # 2. Look up the highlight using the found ID
    # We use str() because sometimes Solr returns IDs as numbers, but keys are strings
    hl = highlights.get(str(doc_id))
    
    if not hl:
        return doc
    
    # 3. Extract the snippet from your specific fields
    # We look for the first field that has a highlight
    snippet_list = (
        hl.get("overview") or 
        hl.get("symptoms_and_causes") or 
        hl.get("diagnosis_and_tests") or
        hl.get("disease_name")
    )
    
    if snippet_list and len(snippet_list) > 0:
        doc["snippet"] = snippet_list[0] # Add 'snippet' field for UI
        
    return doc


@app.get("/autocomplete")
async def autocomplete(q: str = Query(..., min_length=1)):
    try:
        # We use a wildcard search on disease_name to find matches starting with the input
        # e.g., q=dia* will find "Diabetes"
        clean_q = q.strip()
        if not clean_q:
            return []
            
        params = {
            "q": f"disease_name:{clean_q}*", # Wildcard prefix search
            "rows": 5,                       # Limit to 5 suggestions
            "fl": "disease_name",            # Only return the name
            "wt": "json",
            "indent": "true"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(SOLR_CORE_URL, params=params, timeout=5.0)
            
        data = response.json()
        print(data)
        docs = data.get("response", {}).get("docs", [])
        
        # Extract names and remove duplicates
        suggestions = []
        seen = set()
        for doc in docs:
            name = doc.get("disease_name")[0]
            if name and name[0] not in seen:
                suggestions.append(name-80)
                seen.add(name)
                
        return suggestions

    except Exception as e:
        print(f"Autocomplete Error: {e}")
        return [] # Return empty list on error so UI doesn't break


TOPIC_MAPPING = {
    "Cardiovascular": "heart cardiac artery vein blood pressure stroke pulse",
    "Respiratory": "lung pulmonary breath airway asthma pneumonia bronchitis",
    "Neurological": "brain nerve mental memory alzheimer dementia headache seizure",
    "Gastrointestinal": "stomach gut intestine digestion bowel liver abdomen",
    "Dermatological": "skin rash itch hair nail dermis eczema acne",
}

@app.get("/semantic_search")
async def semantic_search(
    q: str = "*:*", 
    page: int = 1, 
    rows: int = 10,
    topic: str | None = None
):
    try:
        start = (page - 1) * rows
        
        # Base Solr parameters
        params = {
            "rows": rows,
            "start": start,
            "wt": "json",
            "fl": "id,disease_name,source_url,overview,score", 
            "fq": [] 
        }

        # --- LOGIC: Vector Search vs Standard Search ---
        if q and q != "*:*" and q != "*":
            # 1. Generate Vector
            vector = utils.text_to_embedding(q)
            
            # 2. Use Solr's KNN Query Parser
            # CHANGED: 'f=semantic_vector' to match your schema
            params["q"] = f"{{!knn f=semantic_vector topK={rows}}}{vector}"
        else:
            # Fallback to standard match-all
            params["q"] = "*:*"

        # --- LOGIC: Apply the Virtual Filter ---
        if topic and topic in TOPIC_MAPPING:
            keywords = TOPIC_MAPPING[topic]
            or_query = "(" + " OR ".join(keywords.split()) + ")"
            
            filter_fields = [
                "disease_name", 
                "overview", 
                "symptoms_and_causes",
                "diagnosis_and_tests",
                "management_and_treatment"
            ]
            
            filter_parts = [f"{field}:{or_query}" for field in filter_fields]
            filter_str = " OR ".join(filter_parts)
            
            params["fq"].append(filter_str)

        async with httpx.AsyncClient() as client:
            # Use POST because vector queries can be very long
            response = await client.post(SOLR_CORE_URL, data=params, timeout=10.0)

        if response.status_code != 200:
            print(f"--- SOLR API ERROR ---")
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")
            raise HTTPException(status_code=500, detail=f"Solr Error: {response.text}")

        data = response.json()
        
        # Parse Solr Response Structure
        raw_docs = data.get("response", {}).get("docs", [])
        total_found = data.get("response", {}).get("numFound", 0)
        
        clean_results = []
        
        for doc in raw_docs:
            doc_id = doc.get("id", doc.get("source_url"))
            
            # Create a snippet from overview (since vector search doesn't return highlighting by default)
            full_overview = doc.get("overview", "")
            if isinstance(full_overview, list): full_overview = " ".join(full_overview)
            snippet = full_overview[:200] + "..." if len(full_overview) > 200 else full_overview

            clean_results.append({
                "id": doc_id,
                "title": doc.get("disease_name", "Untitled"),
                "url": doc.get("source_url", "#"),
                "snippet": snippet,
                "meta": "Medical Text" 
            })

        return {
            "results": clean_results,
            "total": total_found,
            "facets": {}
        }

    except Exception as e:
        print("--- PYTHON SERVER ERROR ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# old EP with normal text
@app.get("/search")
async def search_index(
    q: str = "*:*", 
    page: int = 1, 
    rows: int = 10,
    topic: str | None = None
):
    try:
        start = (page - 1) * rows
        
        # --- ENHANCEMENT 1: Expanded Search Scope (qf) ---
        # We assign weights (boosts) to fields based on importance.
        # disease_name (Title) gets the highest boost (^5).
        search_fields = [
            "disease_name^5",
            "overview^3",
            "symptoms_and_causes^2",
            "management_and_treatment^2",  # Crucial for queries about cures/drugs
            "diagnosis_and_tests^1.5",     # Crucial for queries about tests
            "prevention^1",
            "living_with^1",
            "outlook_prognosis^1",
            "additional_common_questions^0.5",
            "suggestions^0.5"
        ]

        # --- ENHANCEMENT 2: Phrase Boosting (pf) ---
        # If the user's terms appear as an exact phrase in these fields, 
        # boost the score significantly.
        phrase_fields = [
            "disease_name^10",
            "overview^5",
            "symptoms_and_causes^3"
        ]

        # Base Solr parameters
        params = {
            "q": q,
            "rows": rows,
            "start": start,
            "wt": "json",
            "defType": "edismax",
            
            # Query Fields with Boosts
            "qf": " ".join(search_fields),
            
            # Phrase Fields: Boosts exact phrase matches
            "pf": " ".join(phrase_fields),
            
            # Phrase Slop: How far apart can words be to still count as a phrase match?
            "ps": "10", 
            
            # Minimum Should Match (mm):
            # "2<-1": If query has 1 or 2 words, require all. 
            # If >2 words, allow 1 to be missing. This makes queries "generic" & forgiving.
            "mm": "2<-1", 
            
            # Tie Breaker: 
            # If a term matches multiple fields (Title AND Overview), 
            # add 0.1 * score of lower fields. Helps dense documents rank higher.
            "tie": "0.1",

            # Highlighting setup
            "hl": "on",
            # Highlight in the most descriptive fields
            "hl.fl": "overview,symptoms_and_causes,management_and_treatment,diagnosis_and_tests",
            "hl.simple.pre": '<em class="highlight">',
            "hl.simple.post": "</em>",
            "hl.snippets": 1,
            "hl.fragsize": 160, # Slightly longer snippets for better context
            
            "fq": [] # Filter Queries container
        }

        # --- LOGIC: Apply the Virtual Filter ---
        if topic and topic in TOPIC_MAPPING:
            keywords = TOPIC_MAPPING[topic]
            # Format keywords for Solr: (word1 OR word2 OR word3)
            # We use .split() to ensure clean separation
            or_query = "(" + " OR ".join(keywords.split()) + ")"
            
            # --- ENHANCEMENT 3: Broader Filter Scope ---
            # Don't limit filtering to just overview. If "Brain" is mentioned in 
            # "Diagnosis" or "Treatment", it should still count for "Neurological".
            filter_fields = [
                "disease_name", 
                "overview", 
                "symptoms_and_causes",
                "diagnosis_and_tests",
                "management_and_treatment"
            ]
            
            # Create a query: disease_name:(...) OR overview:(...) OR ...
            filter_parts = [f"{field}:{or_query}" for field in filter_fields]
            filter_str = " OR ".join(filter_parts)
            
            params["fq"].append(filter_str)

        async with httpx.AsyncClient() as client:
            response = await client.get(SOLR_CORE_URL, params=params, timeout=10.0)

        if response.status_code != 200:
            print(f"--- SOLR API ERROR ---")
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")
            raise HTTPException(status_code=500, detail=f"Solr Error: {response.text}")

        data = response.json()
        
        raw_docs = data.get("response", {}).get("docs", [])
        highlighting = data.get("highlighting", {})
        
        clean_results = []
        
        for doc in raw_docs:
            doc_id = doc.get("id", doc.get("source_url"))
            
            # Smart Snippet Selection
            # 1. Try to find a highlight in 'overview'
            # 2. If not, try 'symptoms_and_causes'
            # 3. If no highlights, fallback to raw 'overview' text
            snippet = ""
            doc_highlights = highlighting.get(doc_id, {})
            
            if doc_highlights.get("overview"):
                snippet = doc_highlights["overview"][0]
            elif doc_highlights.get("symptoms_and_causes"):
                snippet = doc_highlights["symptoms_and_causes"][0]
            elif doc_highlights.get("management_and_treatment"):
                snippet = doc_highlights["management_and_treatment"][0]
            else:
                # Fallback: get first 200 chars of overview
                full_overview = doc.get("overview", "")
                if isinstance(full_overview, list): full_overview = " ".join(full_overview)
                snippet = full_overview[:200] + "..." if len(full_overview) > 200 else full_overview

            clean_results.append({
                "id": doc_id,
                "title": doc.get("disease_name", "Untitled"),
                "url": doc.get("source_url", "#"),
                "snippet": snippet,
                "meta": "Medical Text"
            })

        return {
            "results": clean_results,
            "total": data.get("response", {}).get("numFound", 0),
            "facets": {}
        }

    except Exception as e:
        print("--- PYTHON SERVER ERROR ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)