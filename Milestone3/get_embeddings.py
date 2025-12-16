import sys
import csv
import json
from sentence_transformers import SentenceTransformer

# Load the SentenceTransformer model
# This downloads the model (~80MB) on the first run
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    """
    Generates a 384-dimensional vector for the provided text.
    Handles truncation automatically if text is too long.
    """
    if not text or not text.strip():
        return []
    # convert_to_tensor=False ensures we get a standard python list, not a torch tensor
    return model.encode(text, convert_to_tensor=False).tolist()

if __name__ == "__main__":
    # increase field size limit for large medical text fields in CSV
    csv.field_size_limit(sys.maxsize)

    # Read CSV from STDIN
    # We use DictReader so it automatically uses the CSV header row as keys
    reader = csv.DictReader(sys.stdin)
    
    documents = []
    
    for row in reader:
        # 1. Extract the most semantically relevant fields for the vector.
        name = row.get("disease name", "")
        overview = row.get("overview", "")
        symptoms = row.get("symptoms and causes", "")
        diagnosis = row.get("diagnosis and tests", "")
        management = row.get("management and treatment", "")
        prognosis = row.get("outlook_prognosis", "")
        prevention = row.get("prevention", "")
        living_with = row.get("living with", "")
        # 2. Combine them into a single string.
        #    We prioritize the Name and Overview as they are most descriptive.
        combined_text = f"{name} {overview} {symptoms} {diagnosis} {management} {prognosis} {prevention} {living_with}".strip()
        
        # 3. Generate the vector and add it to the 'semantic_vector' field
        #    (This matches the field name in your updated Solr schema)
        if combined_text:
            row["semantic_vector"] = get_embedding(combined_text)
        
        # Clean up empty fields if necessary, or just append the row
        documents.append(row)

    # Output the list of documents as JSON to STDOUT
    # This format [ {doc1}, {doc2} ] is directly compatible with Solr's update handler
    json.dump(documents, sys.stdout, indent=4, ensure_ascii=False)