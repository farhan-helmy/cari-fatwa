#!/usr/bin/env python3
"""
Helper script to diagnose and fix selector issues with the Mufti WP scraper.
This script will fetch a page and print out the HTML structure to help identify the correct selectors.
"""

import requests
from bs4 import BeautifulSoup
import argparse
import json
import os
import re

def get_page_content(url, headers=None):
    """Get the HTML content of a page."""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def save_html(html_content, filename="page.html"):
    """Save HTML content to a file for inspection."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML content saved to {filename}")

def analyze_list_page(url):
    """Analyze the list page structure to find article links."""
    html_content = get_page_content(url)
    if not html_content:
        return
    
    save_html(html_content, "list_page.html")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try different selectors for article links
    selectors = [
        '.article-list-item',
        '.article-list',
        '.items-row',
        '.item',
        'article',
        '.article',
        '.blog-item',
        '.blog-post',
        'div.item'
    ]
    
    results = {}
    
    for selector in selectors:
        elements = soup.select(selector)
        results[selector] = len(elements)
        print(f"Selector '{selector}': {len(elements)} elements found")
        
        if elements:
            # Check for links within these elements
            for i, element in enumerate(elements[:3]):  # Show first 3 elements
                links = element.select('a')
                if links:
                    print(f"  Element {i+1} contains {len(links)} links:")
                    for j, link in enumerate(links[:2]):  # Show first 2 links
                        print(f"    Link {j+1}: {link.get('href', 'No href')} - Text: {link.text.strip()[:50]}")
    
    # Find the most promising selector
    best_selector = max(results.items(), key=lambda x: x[1])[0] if results else None
    
    if best_selector:
        print(f"\nRecommended selector for article list: '{best_selector}'")
        
        # Check for title links
        elements = soup.select(best_selector)
        link_selectors = [
            'a',
            'a.article-list-title',
            'h2 a',
            '.item-title a',
            '.title a',
            '.entry-title a'
        ]
        
        link_results = {}
        
        for link_selector in link_selectors:
            total_links = 0
            for element in elements:
                links = element.select(link_selector)
                total_links += len(links)
            
            link_results[link_selector] = total_links
            print(f"Link selector '{link_selector}' within '{best_selector}': {total_links} links found")
        
        best_link_selector = max(link_results.items(), key=lambda x: x[1])[0] if link_results else None
        
        if best_link_selector:
            print(f"\nRecommended selector for article links: '{best_selector} {best_link_selector}'")
            
            # Update the scraper files
            update_selectors_in_files(best_selector, best_link_selector)

def analyze_detail_page(url):
    """Analyze the detail page structure to find article content."""
    html_content = get_page_content(url)
    if not html_content:
        return
    
    save_html(html_content, "detail_page.html")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try different selectors for article title
    title_selectors = [
        'h2.article-details-title',
        'h1.article-title',
        'h1.entry-title',
        'h1.title',
        'h2.title',
        '.article-title',
        '.entry-title',
        '.page-title'
    ]
    
    print("\nSearching for article title:")
    for selector in title_selectors:
        elements = soup.select(selector)
        print(f"Selector '{selector}': {len(elements)} elements found")
        
        if elements:
            for i, element in enumerate(elements[:2]):  # Show first 2 elements
                print(f"  Element {i+1} text: {element.text.strip()[:100]}")
    
    # Try different selectors for article content
    content_selectors = [
        'div[itemprop="articleBody"]',
        '.article-content',
        '.entry-content',
        '.content',
        '.article-body',
        '.article-text',
        '#article-content',
        '.item-page'
    ]
    
    print("\nSearching for article content:")
    for selector in content_selectors:
        elements = soup.select(selector)
        print(f"Selector '{selector}': {len(elements)} elements found")
        
        if elements:
            for i, element in enumerate(elements[:1]):  # Show first element
                content_text = element.text.strip()
                print(f"  Element {i+1} text (first 100 chars): {content_text[:100]}")
                
                # Check if it contains "Soalan:" and "Jawapan:"
                has_soalan = "Soalan:" in content_text
                has_jawapan = "Jawapan:" in content_text
                
                print(f"  Contains 'Soalan:': {has_soalan}")
                print(f"  Contains 'Jawapan:': {has_jawapan}")
    
    # Find the most promising selectors
    best_title_selector = None
    best_content_selector = None
    
    # Check for title with "IRSYAD HUKUM" in it
    for selector in title_selectors:
        elements = soup.select(selector)
        for element in elements:
            if "IRSYAD HUKUM" in element.text.strip().upper():
                best_title_selector = selector
                break
        if best_title_selector:
            break
    
    # Check for content with "Soalan:" in it
    for selector in content_selectors:
        elements = soup.select(selector)
        for element in elements:
            if "Soalan:" in element.text.strip():
                best_content_selector = selector
                break
        if best_content_selector:
            break
    
    if best_title_selector:
        print(f"\nRecommended selector for article title: '{best_title_selector}'")
    
    if best_content_selector:
        print(f"Recommended selector for article content: '{best_content_selector}'")
        
    if best_title_selector and best_content_selector:
        # Update the scraper files
        update_detail_selectors_in_files(best_title_selector, best_content_selector)

def update_selectors_in_files(article_selector, link_selector):
    """Update the selectors in the scraper files."""
    files_to_update = ['scraper.py', 'advanced_scraper.py']
    
    for file in files_to_update:
        if not os.path.exists(file):
            print(f"File {file} not found, skipping...")
            continue
        
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update article selector
        content = re.sub(
            r'(articles\s*=\s*soup\.select\()[\'"].*?[\'"]\)',
            f"\\1'{article_selector}')",
            content
        )
        
        # Update link selector
        content = re.sub(
            r'(link_element\s*=\s*article\.select_one\()[\'"].*?[\'"]\)',
            f"\\1'{link_selector}')",
            content
        )
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated selectors in {file}")

def update_detail_selectors_in_files(title_selector, content_selector):
    """Update the detail page selectors in the scraper files."""
    files_to_update = ['scraper.py', 'advanced_scraper.py']
    
    for file in files_to_update:
        if not os.path.exists(file):
            print(f"File {file} not found, skipping...")
            continue
        
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update title selector
        content = re.sub(
            r'(title_element\s*=\s*soup\.select_one\()[\'"].*?[\'"]\)',
            f"\\1'{title_selector}')",
            content
        )
        
        # Update content selector
        content = re.sub(
            r'(article_body\s*=\s*soup\.select_one\()[\'"].*?[\'"]\)',
            f"\\1'{content_selector}')",
            content
        )
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated detail page selectors in {file}")

def main():
    parser = argparse.ArgumentParser(description='Diagnose and fix selector issues with the Mufti WP scraper')
    parser.add_argument('--list-url', default='https://www.muftiwp.gov.my/ms/artikel/irsyad-hukum/umum', 
                        help='URL of the article list page')
    parser.add_argument('--detail-url', 
                        default='https://www.muftiwp.gov.my/ms/artikel/irsyad-hukum/umum/5972-irsyad-hukum-siri-ke-863-adakah-diwajibkan-seseorang-itu-untuk-menjaga-anak-saudaranya-yang-kematian-bapa-jika-dia-menolak-bahagiannya-dalam-harta-pusaka',
                        help='URL of an article detail page')
    parser.add_argument('--analyze-list', action='store_true', help='Analyze the list page structure')
    parser.add_argument('--analyze-detail', action='store_true', help='Analyze the detail page structure')
    
    args = parser.parse_args()
    
    # If no specific analysis is requested, do both
    if not args.analyze_list and not args.analyze_detail:
        args.analyze_list = True
        args.analyze_detail = True
    
    if args.analyze_list:
        print(f"Analyzing list page: {args.list_url}")
        analyze_list_page(args.list_url)
    
    if args.analyze_detail:
        print(f"\nAnalyzing detail page: {args.detail_url}")
        analyze_detail_page(args.detail_url)

if __name__ == "__main__":
    main() 