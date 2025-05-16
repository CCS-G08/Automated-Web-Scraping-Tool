from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import re
import time
from colorama import Fore, Style

# Define regex patterns for matching data
PATTERNS = {
    'Product Name': r'(Product Name|Title):?\s*(.+)',
    'CVE': r'(CVE-\d{4}-\d+)',  # Matches CVE identifiers like CVE-2024-12345
    'CVSS/Severity': r'((CVSS|Severity)[:\s]*[0-9.]+|Critical|High|Medium|Low)',  # Matches CVSS scores and severity levels
    'Published Date': (
        r'(Published\s*(Date|On|:)\s*\d{4}-\d{2}-\d{2}|'  # Matches 'Published Date: YYYY-MM-DD'
        r'\d{4}/\d{2}/\d{2}|'  # Matches 'YYYY/MM/DD'
        r'(\bJanuary|\bFebruary|\bMarch|\bApril|\bMay|\bJune|\bJuly|\bAugust|\bSeptember|\bOctober|\bNovember|\bDecember)\s+\d{1,2},\s+\d{4}|'  # Matches 'Month DD, YYYY'
        r'\d{1,2}\s+(\bJanuary|\bFebruary|\bMarch|\bApril|\bMay|\bJune|\bJuly|\bAugust|\bSeptember|\bOctober|\bNovember|\bDecember)\s+\d{4})'  # Matches 'DD Month YYYY'
    )
}

def scrape_links():
    try:
        file_exists = os.path.isfile('output.txt')
        with open('output.txt', 'w', encoding='utf-8') as file:
            pass
        if not file_exists:
            with open('output.txt', 'w', encoding='utf-8') as file:
                file.write("Scraped Vulnerability Data:\n\n")  # Write a header to the file
    except Exception as e:
        print(f"Error creating/writing to 'output.txt': {e}")
        exit()

    # Read URLs from 'vuln_links.txt'
    try:
        with open('vuln_links.txt', 'r') as vuln_file:
            urls = [line.strip() for line in vuln_file if line.strip()]
            if not urls:
                print(f"{Fore.RED}{Style.BRIGHT}No URLs found in 'vuln_links.txt'{Style.RESET_ALL}")
                exit()
    except Exception as e:
        print(f"Error reading 'vuln_links.txt': {e}")
        exit()

    # Set up Selenium WebDriver (using Chrome here)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_driver_path = "/usr/bin/chromedriver" 
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options) 

    for url in urls:
        try:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}URL to scrape: {url}{Style.RESET_ALL}")
            print(f"{Fore.RED}{Style.BRIGHT}STARTING SCRAPING....{Style.RESET_ALL}")

            driver.get(url)
            time.sleep(5) 
            # Extract the page content using Selenium (get full text of the page)
            text_content = driver.find_element(By.TAG_NAME, 'body').text
            # Get the page title as the Product Name
            product_name = driver.title.strip() if driver.title else None

            # Search for keywords in the page content using regex
            extracted_data = search_keywords(text_content, product_name, url)

            # If valid data is found, write to the text file
            if extracted_data:
                save_to_text_file(url, extracted_data)
                print(f"{Fore.GREEN}{Style.BRIGHT}DATA SAVED IN 'output.txt'{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}{Style.BRIGHT}No relevant data found for URL: {url}{Style.RESET_ALL}")

        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Close the WebDriver
    driver.quit()
    #call_mail()

def search_keywords(text_content, product_name=None, url=None):
    try:
        # Extract OEM name directly from the URL
        oem_name = extract_oem_name_from_url(url)
        # Initialize extracted data with OEM Name
        extracted_data = {'OEM Name': oem_name, 'Product Name': product_name, 'CVE': None, 'CVSS/Severity': None, 'Published Date': None}

        # Search for each pattern in the text content using regular expressions
        for field, pattern in PATTERNS.items():
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                if field == 'Product Name' and extracted_data['Product Name']:
                    continue
                extracted_data[field] = match.group(0)

        # Return the extracted data if any of the fields are filled
        if any(extracted_data.values()):
            return extracted_data
        return None
    except Exception as e:
        print(f"Error occurred while searching for keywords: {e}")
        return None

def extract_oem_name_from_url(url):
    """Extracts the OEM name from the given URL."""
    try:
        # Assuming the OEM name is in the domain name of the URL
        oem_name = re.search(r'//([a-zA-Z0-9.-]+)\.', url)
        if oem_name:
            return oem_name.group(1)
        return "Unknown OEM"
    except Exception as e:
        print(f"Error extracting OEM name from URL: {e}")
        return "Unknown OEM"

def save_to_text_file(url, data):
    try:
        with open('output.txt', 'a', encoding='utf-8') as file:
            file.write(f"URL: {url}\n")  # Write the URL for reference
            for key, value in data.items():
                if value:
                    file.write(f"{key}: {value}\n")
            file.write("\n" + "-" * 50 + "\n\n")  # Separate each entry with a line
    except Exception as e:
        print(f"Error occurred while saving to text file: {e}")
        
def call_mail():
    try:
        import subprocess
        subprocess.run(["python3", "mail.py"])
        exit()
    except Exception as e:
        print(f"Error occured: {e}")

if __name__ == "__main__":
    scrape_links()
