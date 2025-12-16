from sentence_transformers import SentenceTransformer

def snake_to_camel_case(word):
    parts = word.split('_')
    return parts[0] + ''.join(x.title() for x in parts[1:])

def text_to_embedding(text):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embedding = model.encode(text, convert_to_tensor=False).tolist()

    # Convert the embedding to the expected format
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    return embedding_str