import pandas as pd
import matplotlib.pyplot as plt
import re
import os
import json
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import seaborn as sns

# Download NLTK resources (uncomment if needed)
# nltk.download('punkt')
# nltk.download('stopwords')

def load_data(file_path):
    """Load data from CSV or JSON file."""
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return pd.DataFrame(json.load(f))
    else:
        raise ValueError("Unsupported file format. Use CSV or JSON.")

def basic_stats(df):
    """Print basic statistics about the dataset."""
    print(f"Total articles: {len(df)}")
    print("\nColumns in the dataset:")
    for col in df.columns:
        print(f"- {col}")
    
    # Check for missing values
    print("\nMissing values:")
    for col in df.columns:
        missing = df[col].isna().sum()
        if missing > 0:
            print(f"- {col}: {missing} ({missing/len(df)*100:.2f}%)")
    
    # Content length statistics
    if 'question' in df.columns:
        df['question_length'] = df['question'].str.len()
        print("\nQuestion length statistics:")
        print(df['question_length'].describe())
    
    if 'answer' in df.columns:
        df['answer_length'] = df['answer'].str.len()
        print("\nAnswer length statistics:")
        print(df['answer_length'].describe())

def plot_content_length_distribution(df):
    """Plot the distribution of content lengths."""
    plt.figure(figsize=(12, 6))
    
    if 'question_length' in df.columns and 'answer_length' in df.columns:
        plt.subplot(1, 2, 1)
        sns.histplot(df['question_length'], kde=True)
        plt.title('Question Length Distribution')
        plt.xlabel('Length (characters)')
        
        plt.subplot(1, 2, 2)
        sns.histplot(df['answer_length'], kde=True)
        plt.title('Answer Length Distribution')
        plt.xlabel('Length (characters)')
    
    plt.tight_layout()
    plt.savefig('content_length_distribution.png')
    print("Saved content length distribution plot to 'content_length_distribution.png'")

def extract_common_words(text_series, top_n=20, min_length=3):
    """Extract the most common words from a series of text."""
    # Combine all text
    all_text = ' '.join(text_series.fillna('').astype(str))
    
    # Tokenize
    tokens = word_tokenize(all_text.lower())
    
    # Filter out short words and non-alphabetic tokens
    tokens = [word for word in tokens if len(word) >= min_length and word.isalpha()]
    
    # Get Malay stopwords if available, otherwise use English
    try:
        stop_words = set(stopwords.words('malay'))
    except:
        stop_words = set(stopwords.words('english'))
    
    # Filter out stopwords
    filtered_tokens = [word for word in tokens if word not in stop_words]
    
    # Count frequencies
    word_freq = Counter(filtered_tokens)
    
    # Return top N words
    return word_freq.most_common(top_n)

def analyze_common_topics(df):
    """Analyze and visualize common topics in the dataset."""
    if 'title' in df.columns:
        common_title_words = extract_common_words(df['title'])
        print("\nMost common words in titles:")
        for word, count in common_title_words:
            print(f"- {word}: {count}")
        
        # Plot common words
        plt.figure(figsize=(12, 6))
        words, counts = zip(*common_title_words)
        plt.barh(words, counts)
        plt.gca().invert_yaxis()  # Display the most common at the top
        plt.title('Most Common Words in Titles')
        plt.xlabel('Count')
        plt.tight_layout()
        plt.savefig('common_title_words.png')
        print("Saved common title words plot to 'common_title_words.png'")
    
    if 'question' in df.columns:
        common_question_words = extract_common_words(df['question'])
        print("\nMost common words in questions:")
        for word, count in common_question_words:
            print(f"- {word}: {count}")

def main():
    # Check if the data file exists
    csv_file = 'mufti_wp_articles.csv'
    json_file = 'mufti_wp_articles.json'
    
    if os.path.exists(csv_file):
        df = load_data(csv_file)
        print(f"Loaded data from {csv_file}")
    elif os.path.exists(json_file):
        df = load_data(json_file)
        print(f"Loaded data from {json_file}")
    else:
        print("No data file found. Please run the scraper first.")
        return
    
    # Perform analysis
    basic_stats(df)
    
    try:
        plot_content_length_distribution(df)
        analyze_common_topics(df)
    except Exception as e:
        print(f"Error during visualization: {e}")
        print("You may need to install additional dependencies: pip install matplotlib seaborn nltk")

if __name__ == "__main__":
    main() 