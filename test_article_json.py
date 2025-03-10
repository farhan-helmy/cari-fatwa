import json
from scraper import MuftiWPScraper

def main():
    url = "https://www.muftiwp.gov.my/ms/artikel/irsyad-hukum/umum/6103-irsyad-hukum-siri-ke-881-hukum-penggunaan-kad-diskaun-yang-berbayar"
    
    scraper = MuftiWPScraper()
    article_data = scraper.extract_article_data(url)
    
    if article_data:
        print("Article data extracted successfully")
        
        # Save to JSON
        try:
            with open('article_test.json', 'w', encoding='utf-8') as f:
                json.dump([article_data], f, ensure_ascii=False, indent=2)
            print("Successfully saved to file: article_test.json")
            
            # Read back to verify
            with open('article_test.json', 'r', encoding='utf-8') as f:
                read_data = json.load(f)
            print("Successfully read back from file")
            print(f"Title from JSON: {read_data[0]['title']}")
            print(f"Question from JSON (first 100 chars): {read_data[0]['question'][:100]}")
        except Exception as e:
            print(f"Error during file operations: {e}")
    else:
        print("Failed to extract article data.")

if __name__ == "__main__":
    main() 