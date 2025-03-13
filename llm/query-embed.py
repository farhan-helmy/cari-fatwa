import chromadb
from openai import OpenAI

# Initialize OpenAI client for embeddings
openai_client = OpenAI(api_key="")

# Load existing Chroma database
chroma_client = chromadb.PersistentClient(path="./chroma_db")  # Adjust path if different
collection = chroma_client.get_collection("mufti_fatwas")

def test_query(query):
    # Step 1: Embed the query using the same model
    query_embedding = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=[query]
    ).data[0].embedding

    # Step 2: Query Chroma for top 3 results
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    # Step 3: Display results
    print(f"Query: '{query}'\n")
    for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        print(f"Result {i+1}:")
        print(f"Title: {metadata['title']}")
        print(f"Text Snippet: {doc[:500]}...")  # Limit to 500 chars for readability
        print(f"URL: {metadata['url']}")
        print(f"Distance: {results['distances'][0][i]}")  # Similarity score (lower = closer)
        print("-" * 50)

# Test with some queries
test_queries = [
    "apa hukum mandi wajib puasa?",
    "bolehkah solat tanpa wudhu?",
    "hukum azan lebih awal"
]
for q in test_queries:
    test_query(q)
    print("=" * 50)