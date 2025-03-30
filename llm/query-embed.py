import chromadb
from openai import OpenAI

# Initialize OpenAI client for embeddings
openai_client = OpenAI(api_key="")

# Load existing Chroma database
chroma_client = chromadb.PersistentClient(
    path="./chroma_db")  # Adjust path if different
collection = chroma_client.get_collection("mufti_fatwas")


def test_query(query):
    # Step 1: Embed the query using the same model
    query_embedding = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=[query]
    ).data[0].embedding

    # Step 2: Query Chroma for only metadata (title and URL)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        include=["metadatas"]  # Only include metadata, not documents
    )

    # Step 3: Display results
    print(f"Query: '{query}'\n")
    for i, metadata in enumerate(results["metadatas"][0]):
        print(f"Result {i+1}:")
        print(f"Title: {metadata['title']}")
        print(f"URL: {metadata['url']}")
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
