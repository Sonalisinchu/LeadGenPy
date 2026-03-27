import re
import time
import traceback
import requests
from bs4 import BeautifulSoup
from Configs.selenium_config import driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from WebScrapper.store import Store


class Scrappers:
    def scrape(self, industry_name, location):
        try:
            print("\n[LOG] - LOADING ITEMS\n")
            scrapeDetail = ScrapeDetails()
            store = Store()
            query = f'{industry_name} in {location}' if industry_name and location else f'{industry_name} {location}'
            driver.get(f'https://www.google.com/maps/search/{query}')
            time.sleep(3)

            # ✅ FIXED: Use role='feed' instead of fragile CSS chain
            scrollableTable = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")

            count = 0  # ✅ FIXED: count was used before assignment in original
            while True:
                count += 1
                scrollableTable.send_keys(Keys.END)
                time.sleep(1.5)
                # Check if we've reached the end of results
                end_elements = driver.find_elements(
                    By.XPATH, "//span[contains(text(), \"You've reached the end\")]"
                )
                if end_elements or count > 25:
                    break

            print("\n[LOG] - ITEMS LOADED\n")
            soup = BeautifulSoup(driver.page_source, 'lxml')

            # ✅ FIXED: Simpler, stable selector for listing links
            res = soup.select("div[role='feed'] a[href*='/maps/place']")
            links = list(set([link.attrs['href'] for link in res if 'href' in link.attrs]))
            print(f'{len(links)} ITEMS FOUND')

            result = []
            count = 0

            print("\n[LOG] - EXTRACTING DATA \n")
            for link in links:
                if count == 25:
                    break
                driver.get(link)
                print(f"\n[LOG] - VISITING : {link[0:25]}... \n")
                time.sleep(2)
                content = driver.page_source
                soup = BeautifulSoup(content, 'lxml')
                print("\n[LOG] - SOURCE PAGE EXTRACTED\n")
                business_data = scrapeDetail.scrape_data(soup)
                business_data["google_map_link"] = link
                business_data["email"] = scrapeDetail.scrape_email(business_data["Website"]) if business_data["Website"] != 'null' else 'null'
                business_data["status"] = "null"
                print("\n[LOG] - DETAILS EXTRACTED\n")
                result.append(business_data)
                count += 1

            print("\n[LOG] - DATASET LOADED\n")
            store.generate_json(result)
            print("\n[LOG] - EXTRACTION COMPLETED\n")
        except:
            traceback.print_exc()
            time.sleep(3)


class ScrapeDetails:
    def scrape_data(self, soup):
        try:
            print("\n[LOG] - EXTRACTING DETAILS\n")
            business_data = {
                "BusinessName": "null",
                "Address": "null",
                "PhoneNumber": "null",
                "Website": "null",
                "Category": "null",
                "Rating": "null",
                "ReviewCount": "null",
            }

            # ✅ FIXED: Business name - stable h1 selector
            name = soup.select_one("h1.DUwDvf") or soup.select_one("h1")
            business_data["BusinessName"] = name.text.strip() if name else "null"
            print(f"\n[LOG] - Name: {business_data['BusinessName']}\n")

            # ✅ FIXED: Category
            category = soup.select_one("button.DkEaL")
            business_data["Category"] = category.text.strip() if category else "null"

            # ✅ FIXED: Rating
            rating = soup.select_one("div.F7nice span[aria-hidden='true']")
            business_data["Rating"] = rating.text.strip() if rating else "null"

            # ✅ FIXED: Review count via aria-label
            reviews = soup.select_one("div.F7nice span[aria-label]")
            if reviews:
                business_data["ReviewCount"] = reviews.attrs.get('aria-label', 'null') \
                    .replace(' reviews', '').replace(',', '').strip()

            # ✅ FIXED: Address using data-item-id (stable across Google Maps updates)
            address_btn = soup.select_one("button[data-item-id='address']") or \
                          soup.select_one("[aria-label*='ddress']")
            if address_btn:
                business_data["Address"] = address_btn.get_text(strip=True)
                print("[LOG] - ADDRESS FOUND")

            # ✅ FIXED: Phone number
            phone_btn = soup.select_one("button[data-item-id*='phone']") or \
                        soup.select_one("[aria-label*='hone']")
            if phone_btn:
                business_data["PhoneNumber"] = phone_btn.get_text(strip=True)
                print("[LOG] - PHONE NUMBER FOUND")

            # ✅ FIXED: Website using anchor tag with data-item-id='authority'
            website_a = soup.select_one("a[data-item-id='authority']") or \
                        soup.select_one("[aria-label*='ebsite']")
            if website_a:
                href = website_a.get('href', '')
                if href.startswith("http"):
                    from urllib.parse import urlparse
                    business_data["Website"] = urlparse(href).netloc.replace("www.", "")
                else:
                    business_data["Website"] = website_a.get_text(strip=True)
                print("[LOG] - WEBSITE FOUND")

            return business_data

        except Exception as error:
            print(f"[ERROR] scrape_data failed: {error}")
            return {
                "BusinessName": "null", "Address": "null", "PhoneNumber": "null",
                "Website": "null", "Category": "null", "Rating": "null", "ReviewCount": "null"
            }

    def scrape_email(self, url):
        try:
            print(f"\n[LOG] - EXTRACTING EMAIL ADDRESS FROM https://{url}\n")
            response = requests.get(f"https://{url}", timeout=10)
            soup = BeautifulSoup(response.text, 'lxml')
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            emails = re.findall(email_pattern, soup.text)

            if emails:
                result = re.sub(r'\d', '', emails[0])
                print(f"\n[LOG] - EMAIL FOUND : {result}")
                return result
            else:
                print(f'[LOG] - EMAIL NOT FOUND: {emails}')
            return 'null'

        except Exception as error:
            print(error)
            return "null"