import requests
from bs4 import BeautifulSoup
import pandas as pd


def scrape_page(page_number):
    url = f"http://gpi.geminiviridae.com/virus/{page_number}"
    response = requests.get(url)

    if response.status_code != 200:
        return {
            'Virus Id': page_number
        }

    soup = BeautifulSoup(response.text, 'html.parser')

    name_tag = soup.find('h3')
    name = name_tag.find('span').find('i').text if name_tag else None

    table_data = {}
    table = soup.find('table')
    if table:
        rows = table.find_all('tr')
        for row in rows:
            key = row.find('th').text.strip()
            if key == 'Download':
                continue

            value = row.find('td').text.strip().replace("\n", "")
            table_data[key] = value

    return {
        'Virus Id': page_number,
        'Virus Name': name,
        **table_data
    }

def scrape_multiple_pages(start, end):
    all_data = []

    indexes_to_retry = []
    for i in range(start, end + 1):
        try:
            print(f"Scraping page {i}...")
            all_data.append(scrape_page(i))
        except Exception as e:
            indexes_to_retry.append(i)
            print(f"Error processing page {i}")
            print(e)


    while len(indexes_to_retry) > 0:
        i = indexes_to_retry.pop()

        try:
            print(f"Scraping page {i}...")
            name, table_data = scrape_page(i)
            if name and table_data:
                all_data.append({'Virus Name': name, **table_data})
        except Exception as e:
            indexes_to_retry.append(i)
            print(f"Error processing page {i}")
            print(e)

    return all_data


data = scrape_multiple_pages(1, 520)
df = pd.DataFrame(data)

df.to_csv('scraped_virus_data.csv', index=False)