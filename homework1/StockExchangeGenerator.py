import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import groupby
import os


def is_valid_company(company_name):
    return not any(char.isdigit() for char in company_name) and not company_name.startswith('E')


def get_date_chunks():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 10)  # 10 years
    date_chunks = []

    current_start_date = start_date
    while current_start_date < end_date:
        current_end_date = current_start_date + timedelta(days=365)
        if current_end_date > end_date:
            current_end_date = end_date  # Adjust the last chunk to the current date

        date_chunks.append((current_start_date.strftime("%Y-%m-%d"), current_end_date.strftime("%Y-%m-%d")))
        current_start_date = current_end_date + timedelta(days=1)  # Move to the next chunk

    return date_chunks


def get_missing_date_chunks(existing_df, company_code):
    if company_code in existing_df["CompanyCode"].unique():
        company_dates = pd.to_datetime(existing_df[existing_df["CompanyCode"] == company_code]["Date"], dayfirst=True)
        all_dates = pd.date_range(start=company_dates.min(), end=company_dates.max())
        missing_dates = set(all_dates) - set(company_dates)

        # Group missing dates into continuous ranges (chunks)
        missing_chunks = []
        for k, g in groupby(enumerate(sorted(missing_dates)), lambda x: x[0] - x[1].toordinal()):
            dates = list(map(lambda x: x[1], g))
            missing_chunks.append((dates[0], dates[-1]))

        return [(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")) for start, end in missing_chunks]
    else:
        # If no data exists for this company, fetch all historical chunks
        return get_date_chunks()


def format_number(value):
    try:
        return "{:,.2f}".format(float(value)).replace(",", "X").replace(".", ",").replace("X", ".")
    except ValueError:
        return value


def scrape_company_data(company_name, company_code, start_date, end_date):
    company_url = f"https://www.mse.mk/en/stats/symbolhistory/{company_code}?fromDate={start_date}&toDate={end_date}"
    company_response = requests.get(company_url)

    company_data = []
    if company_response.status_code == 200:
        company_soup = BeautifulSoup(company_response.content, 'html.parser')
        table = company_soup.select_one('table.table')

        if table:
            for row in table.find_all('tr')[1:]:
                cells = row.find_all('td')
                if len(cells) >= 8:
                    date = cells[0].text.strip()
                    last_trade_price = cells[1].text.strip()
                    max_price = cells[2].text.strip()
                    min_price = cells[3].text.strip()
                    avg_price = cells[4].text.strip()
                    percent_change = cells[5].text.strip()
                    volume = cells[6].text.strip()
                    turnover_best = cells[7].text.strip()
                    turnover_total = cells[8].text.strip()

                    try:
                        date = pd.to_datetime(date).strftime("%d.%m.%Y")
                    except ValueError:
                        print(f"Error formatting date: {date}")
                        continue

                    company_data.append({
                        "CompanyCode": company_code,
                        "Date": date,
                        "LastTradePrice": last_trade_price,
                        "Max": max_price,
                        "Min": min_price,
                        "AvgPrice": avg_price,
                        "%Change": percent_change,
                        "Volume": volume,
                        "TurnoverBESTMKD": turnover_best,
                        "TurnoverTotalMKD": turnover_total
                    })
    else:
        print(f"Failed to load data for {company_name} from {start_date} to {end_date}.")
    return company_data


if __name__ == '__main__':
    start_time = time.time()

    # Load existing CSV if available
    file_path = "company_data.csv"
    if os.path.exists(file_path):
        try:
            # Explicitly specify dtype for 'Volume' column as string to avoid DtypeWarning
            existing_data = pd.read_csv(file_path, dtype={"Volume": str}, low_memory=False)
            print("CSV file loaded successfully without DtypeWarning.")
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            existing_data = pd.DataFrame()
    else:
        # If file does not exist, create an empty DataFrame
        existing_data = pd.DataFrame()
        print("No existing CSV file found. Starting fresh.")

    url = "https://www.mse.mk/en/stats/symbolhistory/KMB"  # URL to fetch the list of companies
    response = requests.get(url)
    all_data = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        dropdown = soup.select_one('select#Code')
        company_links = []

        if dropdown:
            for option in dropdown.find_all('option'):
                company_name = option.text.strip()
                company_code = option.get('value')

                if is_valid_company(company_name):
                    company_links.append((company_name, company_code))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for company_name, company_code in company_links:
                # Get missing date chunks for this company
                missing_chunks = get_missing_date_chunks(existing_data, company_code)

                for start_date, end_date in missing_chunks:
                    futures.append(
                        executor.submit(scrape_company_data, company_name, company_code, start_date, end_date))

            for future in as_completed(futures):
                data = future.result()
                all_data.extend(data)

        # Combine with existing data and remove duplicates
        new_data_df = pd.DataFrame(all_data)

        if not existing_data.empty:
            combined_data = pd.concat([existing_data, new_data_df])
            updated_data = combined_data.drop_duplicates(subset=["CompanyCode", "Date"], keep="last")
        else:
            updated_data = new_data_df

        # Save updated data to CSV
        updated_data.to_csv("company_data.csv", index=False)
        print("CSV file successfully updated.")

    else:
        print("Failed to load the main URL.")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Execution time: {elapsed_time:.2f} seconds.")
