import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
import json
import os
from datetime import datetime
from tqdm import tqdm
import logging
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class MuftiWPAdvancedScraper:
    def __init__(self, max_retries=3, delay_between_requests=(1, 3)):
        self.base_url = "https://www.muftiwp.gov.my/ms/artikel/irsyad-hukum/umum"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.data = []
        self.max_retries = max_retries
        self.delay_range = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Create a directory for caching
        self.cache_dir = 'cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # For resuming scraping
        self.checkpoint_file = 'checkpoint.json'
        
    def random_delay(self):
        """Add a random delay between requests to be respectful to the server."""
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        time.sleep(delay)
        
    def get_page_content(self, url, use_cache=True):
        """Get the HTML content of a page with retries and caching."""
        cache_file = os.path.join(self.cache_dir, f"{hash(url)}.html")
        
        # Try to load from cache if enabled
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    logging.info(f"Loading from cache: {url}")
                    return f.read()
            except Exception as e:
                logging.warning(f"Error reading cache for {url}: {e}")
        
        # Fetch from web with retries
        for attempt in range(self.max_retries):
            try:
                logging.info(f"Fetching: {url} (Attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url)
                response.raise_for_status()
                
                # Save to cache
                if use_cache:
                    try:
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                    except Exception as e:
                        logging.warning(f"Error writing cache for {url}: {e}")
                
                return response.text
            except requests.RequestException as e:
                logging.error(f"Error fetching {url}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
            
            self.random_delay()
        
        return None
    
    def extract_article_links(self, html_content, page_url):
        """Extract article links from a page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        article_links = []
        
        # Find all article links in the table structure
        table = soup.select_one('table.category')
        if table:
            rows = table.select('tr')
            for row in rows:
                link_element = row.select_one('td.list-title a')
                if link_element and 'href' in link_element.attrs:
                    # Make sure we have absolute URLs
                    article_url = urljoin(page_url, link_element['href'])
                    article_links.append(article_url)
        
        return article_links
    
    def clean_text(self, text):
        """Clean text to ensure it's properly formatted for JSON."""
        if not text:
            return text
        
        # Replace any problematic characters
        text = text.replace('\u2028', ' ').replace('\u2029', ' ')
        
        # Remove any control characters
        text = re.sub(r'[\x00-\x1F\x7F]', '', text)
        
        return text
    
    def extract_article_data(self, article_url):
        """Extract title, question, and answer from an article."""
        html_content = self.get_page_content(article_url)
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title_element = soup.select_one('h2.article-details-title')
        title = title_element.text.strip() if title_element else "No title found"
        
        # Extract article body
        article_body = soup.select_one('div[itemprop="articleBody"]')
        if not article_body:
            logging.warning(f"No article body found for {article_url}")
            return {
                'title': self.clean_text(title),
                'question': "No question found",
                'answer': "No answer found",
                'url': article_url,
                'scraped_at': datetime.now().isoformat()
            }
        
        # Extract content
        content = article_body.text.strip()
        
        # Initialize variables
        question = "No question found"
        answer = "No answer found"
        ringkasan_jawapan = ""
        huraian_jawapan = ""
        mukadimah = ""
        
        # Try to extract different sections with more flexible patterns
        # 1. Extract Soalan (Question) - with or without colon
        soalan_match = re.search(r'Soalan\s*:?\s*(.*?)(?=Ringkasan\s+Jawapan\s*:?|Huraian\s+Jawapan\s*:?|Jawapan\s*:?|$)', content, re.DOTALL | re.IGNORECASE)
        if soalan_match:
            question = soalan_match.group(1).strip()
        
        # 2. Extract Ringkasan Jawapan (Summary Answer) - with or without colon
        ringkasan_match = re.search(r'Ringkasan\s+Jawapan\s*:?\s*(.*?)(?=Huraian\s+Jawapan\s*:?|$)', content, re.DOTALL | re.IGNORECASE)
        if ringkasan_match:
            ringkasan_jawapan = ringkasan_match.group(1).strip()
        
        # 3. Extract Huraian Jawapan (Detailed Answer) - with or without colon
        huraian_match = re.search(r'Huraian\s+Jawapan\s*:?\s*(.*?)(?=$)', content, re.DOTALL | re.IGNORECASE)
        if huraian_match:
            huraian_jawapan = huraian_match.group(1).strip()
        
        # 4. Extract Jawapan (Answer) if no Ringkasan or Huraian - with or without colon
        jawapan_match = re.search(r'Jawapan\s*:?\s*(.*?)(?=$)', content, re.DOTALL | re.IGNORECASE)
        if jawapan_match and not ringkasan_jawapan and not huraian_jawapan:
            answer = jawapan_match.group(1).strip()
        
        # 5. Extract Mukadimah (Introduction) if no Soalan - with or without colon
        if question == "No question found":
            mukadimah_match = re.search(r'Mukadimah\s*:?\s*(.*?)(?=Ringkasan\s+Jawapan\s*:?|Huraian\s+Jawapan\s*:?|Jawapan\s*:?|$)', content, re.DOTALL | re.IGNORECASE)
            if mukadimah_match:
                mukadimah = mukadimah_match.group(1).strip()
        
        # Combine answers if available
        if ringkasan_jawapan or huraian_jawapan:
            answer_parts = []
            if ringkasan_jawapan:
                answer_parts.append(f"Ringkasan Jawapan: {ringkasan_jawapan}")
            if huraian_jawapan:
                answer_parts.append(f"Huraian Jawapan: {huraian_jawapan}")
            answer = "\n\n".join(answer_parts)
        
        # If no question but has mukadimah, use mukadimah as question
        if question == "No question found" and mukadimah:
            question = f"Mukadimah: {mukadimah}"
        
        # If still no structured content found, try to extract based on paragraphs
        if question == "No question found" and answer == "No answer found":
            paragraphs = article_body.find_all('p')
            if len(paragraphs) >= 2:
                # Assume first paragraph might be the question and the rest is the answer
                question = paragraphs[0].text.strip()
                answer = "\n\n".join([p.text.strip() for p in paragraphs[1:]])
        
        # If still no question found, use the title as the question
        if question == "No question found":
            # Extract the actual question from the title (remove the "IRSYAD HUKUM SIRI KE-XXX: " part)
            title_parts = title.split(":", 1)
            if len(title_parts) > 1:
                question = f"Apa hukum {title_parts[1].strip().lower()}?"
            else:
                question = f"Apa hukum {title.strip().lower()}?"
        
        # If still no answer found but we have content, use all content as answer
        if answer == "No answer found" and content:
            answer = content
        
        # Clean text to ensure it's properly formatted for JSON
        title = self.clean_text(title)
        question = self.clean_text(question)
        answer = self.clean_text(answer)
        
        return {
            'title': title,
            'question': question,
            'answer': answer,
            'url': article_url,
            'scraped_at': datetime.now().isoformat()
        }
    
    def save_checkpoint(self, page_num, processed_urls):
        """Save a checkpoint to resume scraping later."""
        checkpoint_data = {
            'page_num': page_num,
            'processed_urls': processed_urls,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f)
        
        logging.info(f"Checkpoint saved: Page {page_num}, {len(processed_urls)} articles processed")
    
    def load_checkpoint(self):
        """Load the checkpoint if it exists."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
                logging.info(f"Loaded checkpoint: Page {checkpoint_data['page_num']}, {len(checkpoint_data['processed_urls'])} articles processed")
                return checkpoint_data['page_num'], set(checkpoint_data['processed_urls'])
            except Exception as e:
                logging.error(f"Error loading checkpoint: {e}")
        
        return 0, set()
    
    def scrape_all_pages(self, start_page=None, max_pages=None, resume=True):
        """Scrape all pages and extract article data with resuming capability."""
        processed_urls = set()
        
        # Try to load checkpoint if resume is enabled
        if resume:
            page_num, processed_urls = self.load_checkpoint()
            # Load existing data if available
            if os.path.exists('mufti_wp_articles.json'):
                try:
                    with open('mufti_wp_articles.json', 'r', encoding='utf-8') as f:
                        self.data = json.load(f)
                    logging.info(f"Loaded {len(self.data)} articles from previous run")
                except Exception as e:
                    logging.error(f"Error loading previous data: {e}")
        else:
            page_num = 0
            
        # Override start page if specified
        if start_page is not None:
            page_num = start_page
            
        more_pages = True
        
        logging.info("Starting to scrape articles...")
        
        try:
            while more_pages:
                if max_pages is not None and page_num >= max_pages:
                    logging.info(f"Reached maximum number of pages ({max_pages})")
                    break
                    
                if page_num == 0:
                    page_url = self.base_url
                else:
                    page_url = f"{self.base_url}?start={page_num * 25}"
                
                logging.info(f"Scraping page: {page_url}")
                html_content = self.get_page_content(page_url)
                
                if not html_content:
                    logging.error(f"Failed to get content for page {page_url}")
                    break
                    
                article_links = self.extract_article_links(html_content, page_url)
                
                if not article_links:
                    logging.info("No more articles found. Ending scraping.")
                    more_pages = False
                    continue
                
                logging.info(f"Found {len(article_links)} articles on page {page_num + 1}")
                
                # Filter out already processed URLs
                new_links = [link for link in article_links if link not in processed_urls]
                logging.info(f"{len(new_links)} new articles to process")
                
                for link in tqdm(new_links, desc=f"Processing page {page_num + 1}"):
                    article_data = self.extract_article_data(link)
                    if article_data:
                        self.data.append(article_data)
                        processed_urls.add(link)
                        
                        # Save intermediate results periodically
                        if len(self.data) % 10 == 0:
                            self.save_to_json('mufti_wp_articles.json')
                            self.save_checkpoint(page_num, list(processed_urls))
                    
                    self.random_delay()
                
                page_num += 1
                self.save_checkpoint(page_num, list(processed_urls))
                self.random_delay()
                
        except KeyboardInterrupt:
            logging.info("Scraping interrupted by user. Saving progress...")
            self.save_to_json('mufti_wp_articles.json')
            self.save_checkpoint(page_num, list(processed_urls))
        except Exception as e:
            logging.error(f"Error during scraping: {e}")
            self.save_to_json('mufti_wp_articles.json')
            self.save_checkpoint(page_num, list(processed_urls))
            raise
            
        # Final save
        self.save_to_json('mufti_wp_articles.json')
        
        # Clean up checkpoint if completed successfully
        if not more_pages and os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            logging.info("Scraping completed successfully. Checkpoint removed.")
    
    def save_to_json(self, filename="mufti_wp_articles.json"):
        """Save the scraped data to a JSON file."""
        if not self.data:
            logging.warning("No data to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Data saved to {filename}")
    
    def save_to_csv(self, filename="mufti_wp_articles.csv"):
        """Save the scraped data to a CSV file."""
        if not self.data:
            logging.warning("No data to save.")
            return
        
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False, encoding='utf-8')
        logging.info(f"Data saved to {filename}")
        
        # Also save as Excel if pandas has openpyxl
        try:
            excel_filename = filename.replace('.csv', '.xlsx')
            df.to_excel(excel_filename, index=False)
            logging.info(f"Data also saved to {excel_filename}")
        except Exception as e:
            logging.warning(f"Could not save as Excel: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape articles from Mufti WP website')
    parser.add_argument('--start-page', type=int, help='Page number to start scraping from')
    parser.add_argument('--max-pages', type=int, help='Maximum number of pages to scrape')
    parser.add_argument('--no-resume', action='store_true', help='Do not resume from checkpoint')
    parser.add_argument('--delay-min', type=float, default=1, help='Minimum delay between requests in seconds')
    parser.add_argument('--delay-max', type=float, default=3, help='Maximum delay between requests in seconds')
    
    args = parser.parse_args()
    
    scraper = MuftiWPAdvancedScraper(
        delay_between_requests=(args.delay_min, args.delay_max)
    )
    
    scraper.scrape_all_pages(
        start_page=args.start_page,
        max_pages=args.max_pages,
        resume=not args.no_resume
    )
    
    scraper.save_to_csv()
    
    logging.info(f"Total articles scraped: {len(scraper.data)}")

if __name__ == "__main__":
    main() 