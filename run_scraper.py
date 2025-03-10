#!/usr/bin/env python3
"""
Helper script to run the Mufti WP scraper with different options.
"""

import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description='Run the Mufti WP scraper')
    parser.add_argument('--basic', action='store_true', help='Run the basic scraper')
    parser.add_argument('--advanced', action='store_true', help='Run the advanced scraper')
    parser.add_argument('--analyze', action='store_true', help='Analyze the scraped data')
    parser.add_argument('--start-page', type=int, help='Page number to start scraping from')
    parser.add_argument('--max-pages', type=int, help='Maximum number of pages to scrape')
    parser.add_argument('--no-resume', action='store_true', help='Do not resume from checkpoint')
    parser.add_argument('--delay-min', type=float, default=1, help='Minimum delay between requests in seconds')
    parser.add_argument('--delay-max', type=float, default=3, help='Maximum delay between requests in seconds')
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Check if required files exist
    if not os.path.exists('scraper.py'):
        print("Error: scraper.py not found. Make sure you're in the correct directory.")
        return
    
    if args.advanced and not os.path.exists('advanced_scraper.py'):
        print("Error: advanced_scraper.py not found. Make sure you're in the correct directory.")
        return
    
    if args.analyze and not os.path.exists('analyze_data.py'):
        print("Error: analyze_data.py not found. Make sure you're in the correct directory.")
        return
    
    # Run the selected script
    if args.basic:
        print("Running basic scraper...")
        os.system('python3 scraper.py')
    
    if args.advanced:
        cmd = 'python3 advanced_scraper.py'
        if args.start_page is not None:
            cmd += f' --start-page {args.start_page}'
        if args.max_pages is not None:
            cmd += f' --max-pages {args.max_pages}'
        if args.no_resume:
            cmd += ' --no-resume'
        cmd += f' --delay-min {args.delay_min} --delay-max {args.delay_max}'
        
        print(f"Running advanced scraper with command: {cmd}")
        os.system(cmd)
    
    if args.analyze:
        print("Analyzing scraped data...")
        os.system('python3 analyze_data.py')

if __name__ == "__main__":
    main() 