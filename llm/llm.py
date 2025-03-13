import json
import chromadb
from openai import OpenAI

# Initialize OpenAI client with your API key
client = OpenAI(api_key="")

# Load your data
with open("llm/mufti_wp_articles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Persistent Chroma client
chroma_client = chromadb.PersistentClient(path="./chroma_db")
# Use get_or_create_collection instead of create_collection to avoid errors if collection already exists
collection = chroma_client.get_or_create_collection("mufti_fatwas")

# Prepare data
texts = [f"{entry['question']} {entry['answer']}" for entry in data]
metadatas = [{"title": entry["title"], "url": entry["url"], "scraped_at": entry["scraped_at"]} for entry in data]
ids = [str(i) for i in range(len(data))]

# Batch processing
batch_size = 10  # Adjust based on your data; 10 is conservative
embeddings = []
successful_indices = []  # Track which texts were successfully embedded

for i in range(0, len(texts), batch_size):
    batch_texts = texts[i:i + batch_size]
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=batch_texts
        )
        batch_embeddings = [e.embedding for e in response.data]
        embeddings.extend(batch_embeddings)
        # Track successful indices
        successful_indices.extend(range(i, i + len(batch_embeddings)))
        print(f"Embedded batch {i // batch_size + 1}: {len(batch_texts)} items")
    except Exception as e:
        print(f"Error in batch {i // batch_size + 1}: {str(e)}")

# Filter documents, metadatas, and ids to match successful embeddings
filtered_texts = [texts[i] for i in successful_indices]
filtered_metadatas = [metadatas[i] for i in successful_indices]
filtered_ids = [ids[i] for i in successful_indices]

print(f"Successfully embedded {len(embeddings)} out of {len(texts)} texts")

# Add to Chroma
collection.add(
    embeddings=embeddings,
    documents=filtered_texts,
    metadatas=filtered_metadatas,
    ids=filtered_ids
)

print("Data successfully added to vector DB!")