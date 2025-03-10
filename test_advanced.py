import sys
from advanced_scraper import MuftiWPAdvancedScraper

def main():
    url = "https://www.muftiwp.gov.my/ms/artikel/irsyad-hukum/umum/6103-irsyad-hukum-siri-ke-881-hukum-penggunaan-kad-diskaun-yang-berbayar"
    
    scraper = MuftiWPAdvancedScraper()
    article_data = scraper.extract_article_data(url)
    
    if article_data:
        print("Title:", article_data['title'])
        print("\nQuestion:", article_data['question'])
        print("\nAnswer (first 500 chars):", article_data['answer'][:500])
        print("\nURL:", article_data['url'])
        print("\nScraped at:", article_data['scraped_at'])
    else:
        print("Failed to extract article data.")

if __name__ == "__main__":
    main() 