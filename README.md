# Mufti WP Scraper

A web scraper to extract articles from the Mufti Wilayah Persekutuan website.

## Description

This project scrapes articles from the Mufti Wilayah Persekutuan website (https://www.muftiwp.gov.my/ms/artikel/irsyad-hukum/umum) and extracts:
- Article titles
- Questions (Soalan)
- Answers (Content after the question)

The data is saved in a structured format for further analysis.

## Setup

1. Install the required dependencies:
```
pip3 install -r requirements.txt
```

2. Run the scraper using the helper script:
```
python3 run_scraper.py --basic
```

## Available Scripts

This project includes several scripts:

- `scraper.py`: Basic scraper that extracts data from the website
- `advanced_scraper.py`: Advanced scraper with caching, resuming, and better error handling
- `analyze_data.py`: Analyzes the scraped data and generates visualizations
- `run_scraper.py`: Helper script to run the scrapers with different options
- `fix_selectors.py`: Diagnoses and fixes selector issues if the website structure changes

## Running the Scraper

You can use the helper script to run the scraper with different options:

```
# Run the basic scraper
python3 run_scraper.py --basic

# Run the advanced scraper
python3 run_scraper.py --advanced

# Run the advanced scraper with custom options
python3 run_scraper.py --advanced --start-page 2 --max-pages 5 --delay-min 2 --delay-max 5

# Analyze the scraped data
python3 run_scraper.py --analyze

# Show help
python3 run_scraper.py --help
```

## Troubleshooting

### OpenSSL Warning

If you encounter the following warning:
```
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL
```

This is fixed by specifying urllib3 version 1.26.18 in the requirements.txt file, which is compatible with older OpenSSL installations.

### Website Structure Changes

If the website structure changes and the scraper stops working, you can use the `fix_selectors.py` script to diagnose and fix the issue:

```
# Analyze both list and detail pages
python3 fix_selectors.py

# Analyze only the list page
python3 fix_selectors.py --analyze-list

# Analyze only the detail page
python3 fix_selectors.py --analyze-detail

# Analyze a specific list page
python3 fix_selectors.py --list-url "https://www.muftiwp.gov.my/ms/artikel/irsyad-hukum/umum?start=25"

# Analyze a specific detail page
python3 fix_selectors.py --detail-url "https://www.muftiwp.gov.my/ms/artikel/irsyad-hukum/umum/6149-irsyad-hukum-siri-ke-887-hukum-penggunaan-inhaler-ketika-siang-ramadan"
```

The script will:
1. Analyze the HTML structure of the pages
2. Identify the correct CSS selectors for article links, titles, and content
3. Automatically update the selectors in the scraper files
4. Save the HTML content to files for manual inspection if needed

## Output

The scraper will generate the following files:

- `mufti_wp_articles.csv`: CSV file containing the extracted data
- `mufti_wp_articles.xlsx`: Excel file containing the extracted data (if openpyxl is installed)
- `mufti_wp_articles.json`: JSON file containing the extracted data (advanced scraper only)
- `scraper.log`: Log file with detailed information about the scraping process (advanced scraper only)
- `content_length_distribution.png`: Visualization of content length distribution (analysis script)
- `common_title_words.png`: Visualization of common words in titles (analysis script)

The data includes the following columns:
- Title
- Question (Soalan)
- Answer (Content)
- URL
- Scraped At (timestamp, advanced scraper only) 