import json
from scraper import MuftiWPScraper

def main():
    # Create a test article with double quotes and special characters
    test_data = [
        {
            'title': 'Test "Title" with quotes',
            'question': 'This is a "question" with quotes and special characters: \n\t\r',
            'answer': 'This is an "answer" with quotes and special characters: \n\t\r',
            'url': 'https://example.com'
        }
    ]
    
    # Test saving to JSON
    print("Testing JSON serialization...")
    
    # 1. Test with json.dumps directly
    try:
        json_str = json.dumps(test_data, ensure_ascii=False, indent=2)
        print("Direct JSON serialization successful")
        print(f"JSON string (first 100 chars): {json_str[:100]}")
    except Exception as e:
        print(f"Error during direct JSON serialization: {e}")
    
    # 2. Test with the scraper's clean_text method
    try:
        scraper = MuftiWPScraper()
        cleaned_data = [
            {
                'title': scraper.clean_text(test_data[0]['title']),
                'question': scraper.clean_text(test_data[0]['question']),
                'answer': scraper.clean_text(test_data[0]['answer']),
                'url': test_data[0]['url']
            }
        ]
        
        json_str = json.dumps(cleaned_data, ensure_ascii=False, indent=2)
        print("JSON serialization with cleaned text successful")
        print(f"JSON string (first 100 chars): {json_str[:100]}")
    except Exception as e:
        print(f"Error during JSON serialization with cleaned text: {e}")
    
    # 3. Test saving to file
    try:
        with open('test_json_output.json', 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        print("Successfully saved to file: test_json_output.json")
        
        # Read back to verify
        with open('test_json_output.json', 'r', encoding='utf-8') as f:
            read_data = json.load(f)
        print("Successfully read back from file")
        print(f"Read data: {read_data}")
    except Exception as e:
        print(f"Error during file operations: {e}")

if __name__ == "__main__":
    main() 