import requests
from bs4 import BeautifulSoup
import json
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import dns.resolver
import dns
import re
import unicodedata
import time

def main():
    # getting to the link and parsing formatted html document
    URL = "http://quotes.toscrape.com/"
    Q_NAME = "quotes.json"
    A_NAME = "authors.json"
    
    # extracting quotes as a list of dictionaries and writing it into json file
    quotes_list = get_quotes(URL)
    with open(Q_NAME, 'w', encoding='utf-8') as f:
        json.dump(quotes_list, f, ensure_ascii=False, indent=4)
    
    # extracting authors names from quotes_list as a set of unique values
    all_authors = extract_authors(quotes_list)
    # preparing suffixes for all author pages on the web-site
    authors_urls = get_authors_urls(all_authors)
    # extracting authors info as a list of dictionaries and writing it into json file
    authors_list = get_authors(URL, authors_urls)
    with open(A_NAME, 'w', encoding='utf-8') as f:
        json.dump(authors_list, f, ensure_ascii=False, indent=4)
    
    load_to_mongo("quotes", Q_NAME)
    load_to_mongo("authors", A_NAME)

def load_to_mongo(name, filename):
    try:
        # Read JSON file and load data
        with open(filename, "r", encoding='utf-8') as f:
            json_data = f.read()
            catalog = json.loads(json_data)

        # connecting to Mongo DB using Google DNS
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8']  
        dns.resolver.default_resolver = resolver
        client = MongoClient(
            "mongodb+srv://dzvinchukt:rm7Fl0r11pWwy481@cluster0.szgft.mongodb.net/",
            server_api=ServerApi('1')
        )
    
        # Access DB (creates one if not exists)
        db = client.book
        collection = db[name] # Access collection using the variable name
        # inserting data from loaded json
        collection.insert_many(catalog)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")




def get_authors(URL, authors_urls):
    authors_list = []
    # parsing information from each author page of the web site
    for url in authors_urls:
        retries = 3  # Number of retries
        for attempt in range(retries):
            try:
                # getting to the link and parsing formatted html document from the page
                html_doc = requests.get(URL + url)
                html_doc.raise_for_status() # Ensure the request was successful
                soup = BeautifulSoup(html_doc.text, 'lxml')
                # extract information about author
                fullname = soup.find('h3', class_='author-title')
                born_date = soup.find('span', class_='author-born-date')
                born_location = soup.find('span', class_='author-born-location')
                description = soup.find('div', class_='author-description')
                author_dict = {
                        "fullname": fullname.text.strip() if fullname else "N/A",
                        "born_date": born_date.text.strip() if born_date else "N/A",
                        "born_location": born_location.text.strip() if born_location else "N/A",
                        "description": description.text.strip() if description else "N/A"
                    }
                authors_list.append(author_dict)
                
                # If request is successful, no need to retry
                break

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {URL + url}: {e}")
                if attempt < retries - 1:
                    print("Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print("Max retries exceeded. Moving to the next URL.")
    
    return authors_list
    
def get_authors_urls(all_authors):
    formatted_authors = []
    for author in all_authors:
        # Normalize Unicode characters to remove accents
        normalized_author = unicodedata.normalize('NFKD', author)
        # Remove accents by removing all combining characters
        ascii_author = ''.join(c for c in normalized_author if not unicodedata.combining(c))
        # Handle cases like "L'Engle" by removing apostrophes and maintaining the capital letter
        ascii_author = re.sub(r"(?<=\b\w)'(?=\w)", '', ascii_author)
        # Replace periods between initials (e.g., 'C.S.' to 'C-S')
        formatted_author = re.sub(r'(?<=\b\w)\.(?=\w\b)', '-', ascii_author)
        # Remove any remaining periods followed by a space or end of the string
        formatted_author = re.sub(r'\.(?=\s|$)', '', formatted_author)
        # Replace spaces with hyphens
        formatted_author = formatted_author.replace(' ', '-')
        formatted_authors.append(formatted_author)
    return [f"/author/{author}/" for author in formatted_authors]

def extract_authors(quotes_list):
    all_authors = set()  # Initialize an empty set to store unique authors
    for quote in quotes_list:
        all_authors.add(quote["author"])  # Add each author to the set
    return list(all_authors)

def get_quotes(URL):
    quotes_urls = get_quotes_urls()
    quotes_list = []

    # parsing information from each page of the web site
    for url in quotes_urls:
        retries = 3  # Number of retries
        for attempt in range(retries):
            try:
                # getting to the link and parsing formatted html document from the page
                html_doc = requests.get(URL + url)
                html_doc.raise_for_status() # Ensure the request was successful
                soup = BeautifulSoup(html_doc.text, 'lxml')
                # extract the lists of quotes, authors and tags from the page
                quotes = soup.find_all('span', class_='text')
                authors = soup.find_all('small', class_='author')
                tags_divs = soup.find_all('div', class_='tags')
                # formating each quote as a dictionary and adding it to the quotes_list
                for i in range(0, len(quotes)):
                    quote_dict = {
                        "tags": [tag.text for tag in tags_divs[i].find_all('a', class_='tag')],
                        "author": authors[i].text,
                        "quote": quotes[i].text
                    }
                    quotes_list.append(quote_dict)
                
                # If request is successful, no need to retry
                break

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {URL + url}: {e}")
                if attempt < retries - 1:
                    print("Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print("Max retries exceeded. Moving to the next URL.")
        
    return quotes_list

# preparing the list of suffixes to parse all pages on the web-site
def get_quotes_urls():
    return [f"/page/{i}/" for i in range(1, 11)]

if __name__ == "__main__":
    main()