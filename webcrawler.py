from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def load_keywords(file_path='keywords.txt'):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"Keyword file not found at {file_path}. Please create it with relevant keywords.")
        exit()

# Extract relevant links from elements structured like tables
def extract_links_from_structured_tables(driver):
    relevant_links = []
    try:
        # Finding elements containing rows (using tr) and cells (using td)
        rows = driver.find_elements(By.XPATH, '//*[self::tr or self::div[contains(@class, "row")]]')
        for row in rows:
            # Get all cells in the row
            cells = row.find_elements(By.TAG_NAME, 'td') or row.find_elements(By.TAG_NAME, 'div')
            for cell in cells:
                # Finding all anchor tags within the cell
                links = cell.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and href not in relevant_links:  # Avoid duplicates
                        relevant_links.append(href)
    except Exception as e:
        print(f"Error during structured table link extraction: {e}")
    return relevant_links

# Extract data dynamically based on keywords present in the entire page content
def extract_keyword_from_page(driver, keywords):
    extracted_links = set()
    try:
        # Get the entire page source
        page_content = driver.page_source
        # Check if any keyword exists in the page content
        for keyword in keywords:
            if keyword.lower() in page_content.lower():
                # If keyword is found, extract links from structured tables
                table_links = extract_links_from_structured_tables(driver)
                extracted_links.update(table_links)
                print(f"Keyword '{keyword}' found.")
                break  # Exit loop after finding the first keyword and extracting links
    except Exception as e:
        print(f"Error during data extraction: {e}")
    return extracted_links

# Function to dynamically crawl and extract data based on keywords
def dynamic_crawl(url, driver, keywords):
    try:
        driver.get(url)
        print(f"\nVisiting: {url}")
        # Wait for the page to load (adjust the sleep time as needed)
        time.sleep(10)
        # Extract data based on keywords present in the entire page content
        extracted_links = extract_keyword_from_page(driver, keywords)
        print(f"Extracted {len(extracted_links)} links from {url}")
        return extracted_links
    except Exception as e:
        print(f"Error while crawling {url}: {e}")
        return set()

# Load previous links for comparison
def load_previous_links(filename='previous_links.txt'):
    try:
        with open(filename, 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Save the new links to the output file
def save_links_to_output_file(links, filename='vuln_links.txt'):
    try:
        with open(filename, 'w') as output_file:
            for link in links:
                output_file.write(link + '\n')
    except Exception as e:
        print(f"Error: {e}")

def update_previous_links(old_links, filename='previous_links.txt'):
    try:
        with open(filename, 'w') as file:
            for link in old_links:
                file.write(link + '\n')
    except Exception as e:
        print(f"Error: {e}")

# Main function to handle the crawling process
def crawl_and_save_links():
    try:
        print("SETTING UP SELENIUM. PLEASE WAIT.....")
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no browser window)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_driver_path = "/usr/bin/chromedriver"  # Path to your ChromeDriver executable
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)  # Set up the WebDriver

        # Load keywords and previous links
        keywords = load_keywords()
        previous_links = load_previous_links()
        current_links = set()

        # Read URLs from start_urls.txt
        with open('start_urls.txt', 'r') as file:
            urls = [line.strip() for line in file if line.strip()]
            for url in urls:
                # Crawl each URL and extract data based on the entire page content
                current_links.update(dynamic_crawl(url, driver, keywords))

        # Close the driver
        driver.quit()

        # Check for new links and save to file if there are any
        if current_links != previous_links:
            print("\nNew vulnerabilities tracked:")
            save_links_to_output_file(current_links - previous_links)
            update_previous_links(current_links)
            print("Crawling completed. All new links saved to vuln_links.txt.")
            #call_scraper()
        else:
            print("\nNo new vulnerabilities found.....")
            exit()
    except Exception as e:
        print(f"Error during crawling process: {e}")
        
def call_scraper():
    try:
        import subprocess
        subprocess.run(["python3", "scraper.py"])
        exit()
    except Exception as e:
        print(f"Error occured: {e}")

if __name__ == "__main__":
    crawl_and_save_links()

