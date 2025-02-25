import requests
from bs4 import BeautifulSoup

def get_tweet_content(url):
    try:
        # Convert X URL to nitter.net URL (an alternative Twitter frontend)
        nitter_url = url.replace('https://x.com', 'https://nitter.net')
        nitter_url = nitter_url.replace('https://twitter.com', 'https://nitter.net')
        
        # Send request with headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(nitter_url, headers=headers)
        
        # Check if request was successful
        if response.status_code != 200:
            return {'error': f'Failed to fetch tweet: Status code {response.status_code}'}

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the tweet content div
        tweet_content = soup.find('div', class_='tweet-content')
        
        if tweet_content:
            return {'text': tweet_content.get_text().strip()}
        else:
            return {'error': 'Tweet content not found'}

    except Exception as e:
        return {'error': f'Error: {str(e)}'}

# Example usage
tweet_url = 'https://vxtwitter.com/jlippincott_/status/1893008562068320504'
result = get_tweet_content(tweet_url)
print(result)
