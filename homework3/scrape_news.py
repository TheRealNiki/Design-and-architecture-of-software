import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Scrape a single page of news
def scrape_page(page, one_month_ago):
    base_url = "https://www.mse.mk/en/news/latest"
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"{base_url}?page={page}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logging.warning(f"Failed to retrieve page {page}. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all rows containing news items
    rows = soup.find_all("div", class_="row")
    if not rows:
        logging.info(f"No articles found on page {page}.")
        return []

    news_data = []
    for row in rows:
        try:
            # Extract date from the first column (col-md-1)
            date_element = row.find("div", class_="col-md-1")
            if not date_element or not date_element.text.strip():
                continue

            date_text = date_element.text.strip()
            try:
                published_date = datetime.strptime(date_text, "%m/%d/%Y")  # Adjust format if necessary
            except ValueError:
                continue

            # Skip articles older than one month
            if published_date < one_month_ago:
                continue

            # Extract title and link from the second column (col-md-11)
            title_element = row.find("div", class_="col-md-11").find("a")
            if not title_element or not title_element.text.strip():
                logging.warning(f"Missing or empty title on page {page}. Skipping item.")
                continue

            title = title_element.text.strip()
            link = "https://www.mse.mk" + title_element["href"]  # Add base URL to relative link

            news_data.append({
                "Title": title,
                "Link": link,
                "Published Date": published_date.strftime("%Y-%m-%d")
            })
        except Exception as e:
            logging.error(f"Error processing a news item on page {page}: {e}")

    return news_data


# Scrape multiple pages of news
def scrape_news(max_pages=10):
    current_date = datetime.now()
    one_month_ago = current_date - timedelta(days=365)  # Calculate the cutoff date for one month ago

    all_news_data = []
    for page in range(1, max_pages + 1):
        logging.info(f"Scraping page {page}...")
        page_data = scrape_page(page, one_month_ago)
        all_news_data.extend(page_data)

    return all_news_data


# Main function to scrape and save news
def scrape_and_save_news():
    all_news_data = scrape_news()

    if not all_news_data:
        logging.info("No recent news data scraped.")
        return

    # Remove duplicates from the data based on Title and Link
    news_df = pd.DataFrame(all_news_data)

    # Deduplicate based on Title and Link to ensure no overwriting occurs
    news_df.drop_duplicates(subset=["Title", "Link"], inplace=True)

    # Save all unique entries into the CSV file
    news_df.to_csv("static/data/news_articles.csv", index=False)

    logging.info("Filtered and deduplicated news data saved to news_articles.csv.")


if __name__ == "__main__":
    scrape_and_save_news()
