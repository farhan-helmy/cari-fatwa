import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from tqdm import tqdm
import os
import json
from urllib.parse import urljoin

class MuftiWPScraper:
    def __init__(self):
        self.base_url = "https://www.muftiwp.gov.my/ms/artikel/irsyad-hukum/umum"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.data = []
        
    def get_page_content(self, url):
        """Get the HTML content of a page."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
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
            return {
                'title': self.clean_text(title),
                'question': "No question found",
                'answer': "No answer found",
                'url': article_url
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
            'url': article_url
        }
    
    def scrape_all_pages(self):
        """Scrape all pages and extract article data."""
        page_num = 0
        more_pages = True
        
        print("Starting to scrape articles...")
        
        while more_pages:
            if page_num == 0:
                page_url = self.base_url
            else:
                page_url = f"{self.base_url}?start={page_num * 25}"
            
            print(f"Scraping page: {page_url}")
            html_content = self.get_page_content(page_url)
            
            if not html_content:
                break
                
            article_links = self.extract_article_links(html_content, page_url)
            
            if not article_links:
                more_pages = False
                continue
            
            print(f"Found {len(article_links)} articles on page {page_num + 1}")
            
            for link in tqdm(article_links, desc=f"Processing page {page_num + 1}"):
                article_data = self.extract_article_data(link)
                if article_data:
                    self.data.append(article_data)
                time.sleep(1)  # Be nice to the server
            
            page_num += 1
            time.sleep(2)  # Be nice to the server between pages
    
    def save_to_json(self, filename="mufti_wp_articles.json"):
        """Save the scraped data to a JSON file."""
        if not self.data:
            print("No data to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        print(f"Data saved to {filename}")
    
    def save_to_csv(self, filename="mufti_wp_articles.csv"):
        """Save the scraped data to a CSV file."""
        if not self.data:
            print("No data to save.")
            return
        
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Data saved to {filename}")
        
        # Also save as Excel if pandas has openpyxl
        try:
            excel_filename = filename.replace('.csv', '.xlsx')
            df.to_excel(excel_filename, index=False)
            print(f"Data also saved to {excel_filename}")
        except Exception as e:
            print(f"Could not save as Excel: {e}")
        
        # Also save as JSON
        self.save_to_json()

def main():
    scraper = MuftiWPScraper()
    scraper.scrape_all_pages()
    scraper.save_to_csv()
    
    print(f"Total articles scraped: {len(scraper.data)}")

if __name__ == "__main__":
    main() 