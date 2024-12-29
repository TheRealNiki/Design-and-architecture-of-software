import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import groupby

def get_first_date_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        first_date_str = df['Date'].iloc[0]
        first_date = pd.to_datetime(first_date_str, dayfirst=True)
        return first_date.strftime("%d.%m.%Y")
    except Exception as e:
        print(f"Error parsing date: {e}")
        return None

def is_valid_company_upd(company_name):
    return not any(char.isdigit() for char in company_name) and not company_name.startswith('E')

def get_date_chunks():
    end_date = datetime.now()
    start_date = get_first_date_from_csv("C:/Users/User/PyCharmProjects/pyBerza/company_data.csv")
    date_chunks = []
    if start_date:
        date_chunks.append((start_date, end_date.strftime("%d.%m.%Y")))
    return date_chunks

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
                    last_trade_price = format_number(last_trade_price)
                    max_price = format_number(max_price)
                    min_price = format_number(min_price)
                    avg_price = format_number(avg_price)
                    percent_change = format_number(percent_change)
                    volume = format_number(volume)
                    turnover_best = format_number(turnover_best)
                    turnover_total = format_number(turnover_total)
                    company_data.append({
                        "Company": company_name,
                        "CompanyCode": company_code,
                        "Date": date,
                        "Last Trade Price": last_trade_price,
                        "Max": max_price,
                        "Min": min_price,
                        "Avg. Price": avg_price,
                        "% Change": percent_change,
                        "Volume": volume,
                        "Turnover BEST (denars)": turnover_best,
                        "Total Turnover (denars)": turnover_total
                    })
    else:
        print(f"Failed to load data for {company_name} from {start_date} to {end_date}.")
    return company_data

def append_company_data_sorted(new_data, file_path="company_data.csv"):
    try:
        existing_data = pd.read_csv(file_path, dtype=str)
    except FileNotFoundError:
        new_data.to_csv(file_path, index=False)
        print(f"Data successfully saved to '{file_path}'.")
        return

    new_data_sorted = sorted(new_data.to_dict('records'), key=lambda x: x['CompanyCode'])
    grouped_new_data = {key: list(group) for key, group in groupby(new_data_sorted, key=lambda x: x['CompanyCode'])}

    for company_code, records in grouped_new_data.items():
        first_index = existing_data[existing_data['CompanyCode'] == company_code].index.min()
        records_df = pd.DataFrame(records)
        if first_index is not None:
            before_company = existing_data.iloc[:first_index]
            after_company = existing_data.iloc[first_index:]
            updated_data = pd.concat([before_company, records_df, after_company], ignore_index=True)
        else:
            updated_data = pd.concat([existing_data, records_df], ignore_index=True)
        existing_data = updated_data

    existing_data.to_csv(file_path, index=False)
    print(f"Data successfully updated in '{file_path}'.")

if __name__ == '__main__':
    start_time = time.time()
    url = "https://www.mse.mk/en/stats/symbolhistory/KMB"
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
                if is_valid_company_upd(company_name):
                    company_links.append((company_name, company_code))

        date_chunks = get_date_chunks()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for company_name, company_code in company_links:
                for start_date, end_date in date_chunks:
                    futures.append(
                        executor.submit(scrape_company_data, company_name, company_code, start_date, end_date))
            for future in as_completed(futures):
                data = future.result()
                if data:
                    all_data.extend(data)

        all_data_sorted = sorted(all_data, key=lambda x: x['CompanyCode'])
        all_data_sorted = [
            row
            for _, group in groupby(all_data_sorted, key=lambda x: x['CompanyCode'])
            for row in sorted(group, key=lambda x: pd.to_datetime(x['Date'], dayfirst=True), reverse=True)
        ]
        all_data_df = pd.DataFrame(all_data_sorted)
        append_company_data_sorted(all_data_df, "C:/Users/User/PyCharmProjects/pyBerza/company_data.csv")
        print("Data successfully saved to 'company_data.csv'.")
    else:
        print("Failed to load the main URL.")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Execution time: {elapsed_time:.2f} seconds.")
