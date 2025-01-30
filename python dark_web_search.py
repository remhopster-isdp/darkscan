import requests
from bs4 import BeautifulSoup
import urllib.parse
import csv
import time
import random
from requests.exceptions import RequestException


# Function to create a session that routes through Tor
def get_tor_session():
    session = requests.Session()
    session.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session


# Retry logic to handle failed requests
def fetch_with_retry(session, url, retries=5, backoff=2):
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()  # Raises exception for 4xx/5xx responses
            return response
        except (RequestException, requests.exceptions.Timeout) as e:
            print(f"Attempt {attempt + 1}/{retries} failed: {e}")
            time.sleep(backoff * (attempt + 1))  # Exponential backoff
    return None  # Return None after retries are exhausted


# Function to scrape Ahmia search results
def scrape_ahmia(url, keywords, writer):
    session = get_tor_session()

    # Encode the keywords and build the search URL
    encoded_keywords = urllib.parse.quote(','.join(keywords))
    search_url = f"{url}/search/?q={encoded_keywords}"

    response = fetch_with_retry(session, search_url)
    if response:
        # Parse the page content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all the <h4> tags that contain the search results
        results = soup.find_all('h4')

        for result in results:
            # Get the anchor tag inside <h4> for the link and title
            link = result.find('a')
            if link:
                title = link.get_text(strip=True)
                result_url = 'http://ahmia.fi' + link['href'] if link['href'].startswith('/') else link['href']

                # Find the description (if available)
                description = result.find_next('p')
                description_text = description.get_text(strip=True) if description else 'No description provided'

                # Find the site URL (the cite tag)
                site_url = result.find_next('cite')
                site_url_text = site_url.get_text(strip=True) if site_url else 'No site URL available'

                # Write the details to the CSV file
                writer.writerow(['Ahmia', title, result_url, description_text, site_url_text])

                # Print the extracted details (for debugging)
                print(
                    f"[Ahmia] Title: {title}, URL: {result_url}, Description: {description_text}, Site URL: {site_url_text}")
    else:
        print(f"Failed to retrieve Ahmia search results after multiple retries.")


# Function to scrape Torch search results
def scrape_torch(url, keywords, writer):
    session = get_tor_session()

    # Encode the keywords and build the search URL
    encoded_keywords = urllib.parse.quote(','.join(keywords))
    search_url = f"{url}?P={encoded_keywords}&DEFAULTOP=and&DB=default&FMT=query&xDB=default&xFILTERS=.%7E%7E&tkn=8af528e090e196f628c960031b8d8c1c%0D%0A"

    response = fetch_with_retry(session, search_url)
    if response:
        # Parse the page content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all the <td valign="top"> tags that contain the file links
        results = soup.find_all('td', {'valign': 'top'})

        for result in results:
            # Get the file URL (anchor tag inside the <td>)
            link = result.find('a', href=True)
            if link:
                file_url = link['href']
                title = link.get_text(strip=True)

                # Get the matching keyword from the <small> tag
                matching_text = result.find('small')
                matching_keywords = matching_text.get_text(strip=True) if matching_text else 'No matching keyword'

                # Get the file size (from the <span> tag with title attribute)
                size_tag = result.find('span', {'title': True})
                file_size = size_tag.get_text(strip=True) if size_tag else 'No size information'

                # Write the details to the CSV file
                writer.writerow(['Torch', file_url, title, file_size, matching_keywords])

                # Print the extracted details (for debugging)
                print(
                    f"[Torch] URL: {file_url}, Title: {title}, Size: {file_size}, Matching Keywords: {matching_keywords}")
    else:
        print(f"Failed to retrieve Torch search results after multiple retries.")


# Main function to scrape Ahmia and Torch and search for keywords
def main():
    # Ahmia search URL
    ahmia_url = 'http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion'  # Ahmia URL
    # Torch search URL
    torch_url = 'http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion/cgi-bin/omega/omega'

    # Manually input keywords (comma-separated)
    keywords_input = input("Enter keywords (comma-separated): ")
    keywords = [keyword.strip() for keyword in keywords_input.split(",")]

    # Open the CSV file for writing
    with open('search_results.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Site', 'Title', 'URL', 'Description/Size', 'Site URL/Matching Keywords'])  # Write header row

        # Scrape Ahmia search results
        scrape_ahmia(ahmia_url, keywords, writer)

        # Scrape Torch search results
        scrape_torch(torch_url, keywords, writer)

    print("Results saved to 'search_results.csv'.")


# Run the main function
if __name__ == '__main__':
    main()
