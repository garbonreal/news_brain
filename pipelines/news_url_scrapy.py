import requests
import newspaper

def download_html(url, filename="downloaded_page.html"):
    """
    Downloads HTML content from a given URL and saves it as a file.

    :param url: The website URL to download.
    :param filename: The filename to save the HTML content.
    """
    try:
        # Set User-Agent to prevent blocking
        headers = {"User-Agent": "Mozilla/5.0"}
        
        # Send HTTP GET request
        response = requests.get(url, headers=headers, timeout=10)

        # Check if request was successful (status code 200)
        if response.status_code == 200:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(response.text)
            print(f"Successfully downloaded HTML from {url} and saved as {filename}")
        else:
            print(f"Failed to fetch page. HTTP Status Code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")

# Example usage
url = "https://www.ft.com/content/3847def5-9c3b-4a1f-96db-caad010faa49"
download_html(url, "example.html")
article = newspaper.Article(url)
article.download()
article.parse()
print(article.text.strip())
