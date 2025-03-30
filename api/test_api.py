import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "dev-api-key-change-me")

def test_health():
    """Test the health endpoint."""
    response = requests.get(f"{API_URL}/health")
    print(f"Health check: {response.status_code}")
    print(response.json())
    print("-" * 50)

def test_search():
    """Test the search endpoint."""
    headers = {"X-API-Key": API_KEY}
    
    # Test queries
    test_queries = [
        "apa hukum mandi wajib puasa?",
        "bolehkah solat tanpa wudhu?",
        "hukum azan lebih awal"
    ]
    
    for query in test_queries:
        data = {"query": query, "limit": 3}
        response = requests.post(f"{API_URL}/search", headers=headers, json=data)
        
        print(f"Query: '{query}'")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Processing time: {results['processing_time']:.4f}s")
            
            for i, result in enumerate(results['results']):
                print(f"Result {i+1}: {result['title']} (Score: {result['score']:.4f})")
                print(f"URL: {result['url']}")
                print()
        else:
            print(f"Error: {response.text}")
        
        print("=" * 50)

def test_rate_limit():
    """Test the rate limiting functionality."""
    headers = {"X-API-Key": API_KEY}
    data = {"query": "test rate limit"}
    
    print("Testing rate limit...")
    for i in range(25):  # Default is 20/minute
        response = requests.post(f"{API_URL}/search", headers=headers, json=data)
        print(f"Request {i+1}: Status {response.status_code}")
        
        if response.status_code != 200:
            print(f"Rate limit hit after {i+1} requests")
            print(f"Response: {response.text}")
            break
    
    print("-" * 50)

if __name__ == "__main__":
    test_health()
    test_search()
    # Uncomment to test rate limiting (will hit limits)
    # test_rate_limit() 