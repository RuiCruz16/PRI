from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import List, Optional
import traceback # Used to print the exact error to terminal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORRECT URL based on your previous messages
SOLR_CORE_URL = "http://localhost:8984/solr/diseases/select"

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

@app.get("/search")
async def search_index(
    q: str = "*:*", 
    page: int = 1, 
    rows: int = 10
):
    try:
        start = (page - 1) * rows

        # Explicitly list the fields present in your schema
        params = {
            "q": q,
            "rows": rows,
            "start": start,
            "wt": "json",
            "defType": "edismax",
            # Search these specific fields from your schema
            "qf": "disease_name^3 overview^2 symptoms_and_causes diagnosis_and_tests",
            
            # Highlighting
            "hl": "on",
            "hl.fl": "overview,symptoms_and_causes,diagnosis_and_tests",
            "hl.simple.pre": '<em class="highlight">',
            "hl.simple.post": "</em>",
            
            # Disable facets for now to prevent errors
            "facet": "off",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(SOLR_CORE_URL, params=params, timeout=10.0)
            
        # Check if Solr itself returned an error (e.g., 400 Bad Request)
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
            # Safe merge
            doc = merge_highlighting(doc, highlighting)
            
            # Map Solr fields to UI fields
            clean_results.append({
                # Use source_url as ID if regular id is missing
                "id": doc.get("id", doc.get("source_url")), 
                "title": doc.get("disease_name", "Untitled"),
                "url": doc.get("source_url", "#"),
                # Use the highlighted snippet we created, or fall back to plain overview
                "snippet": doc.get("snippet", doc.get("overview", "")),
                "meta": "Medical Text"
            })

        return {
            "results": clean_results,
            "total": data.get("response", {}).get("numFound", 0),
            "facets": {}
        }

    except Exception as e:
        # Print the FULL error to your terminal so we can see what's wrong
        print("--- PYTHON SERVER ERROR ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)