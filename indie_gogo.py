import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time
import base64

# Function to perform web scraping
def scrape_data(search_term):
    base_url = "https://www.indiegogo.com"
    url = f"https://www.indiegogo.com/explore/health-fitness?project_timing=all&product_stage=all&sort=trending&q={search_term}"

    # Firefox options
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")

    # Firefox WebDriver Service
    service = FirefoxService(executable_path=GeckoDriverManager().install())

    # WebDriver with Firefox
    driver = webdriver.Firefox(options=firefox_options, service=service)

    try:
        driver.get(url)
        time.sleep(2)  # Adjust the sleep time if necessary

        # Scroll to bottom of page logic
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Adjust the sleep time if necessary

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        page_source = driver.page_source

    finally:
        driver.quit()

    soup = BeautifulSoup(page_source, 'html.parser')
    divs = soup.find_all('div', class_='fundingDiscoverableCard discoverableCard')

    projects_data = []

    for div in divs:
        
        link_elem = div.find('a', href=True)
        project_link = base_url + link_elem['href'] if link_elem else 'N/A'
        
        title = div.find('div', class_='baseDiscoverableCard-title').get_text(strip=True) if div.find('div', class_='baseDiscoverableCard-title') else 'N/A'
        description = div.find('div', class_='baseDiscoverableCard-body').get_text(strip=True) if div.find('div', class_='baseDiscoverableCard-body') else 'N/A'
        category = div.find('small', class_='baseDiscoverableCard-categoryLink').get_text(strip=True) if div.find('small', class_='baseDiscoverableCard-categoryLink') else 'N/A'
        
        raised_amount_elem = div.find('span', class_='fundingDiscoverableCard-unitsRaisedNumber')
        raised_amount = raised_amount_elem.get_text(strip=True) if raised_amount_elem else 'N/A'

        raised_percentage_elem = div.find(lambda tag: tag.name == 'div' and 'fundingDiscoverableCard-raisedPercentage' in tag.get('class', []))
        raised_percentage = raised_percentage_elem.get_text(strip=True) if raised_percentage_elem else 'N/A'

        days_left_elem = div.find('span', class_='fundingDiscoverableCard-timeLeft')
        days_left = days_left_elem.get_text(strip=True) if days_left_elem else 'N/A'

        projects_data.append({
            'Title': title,
            'Description': description,
         #   'Category': category,
            'Raised Amount': raised_amount,
            'Raised Percentage': raised_percentage,
            'Days Left': days_left,
            'Link': project_link
        })
        
    df = pd.DataFrame(projects_data)
    
    return df

#Function to generate download link for a DataFrame
def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="indiegogo_projects.csv">Download csv file</a>'
    return href

##############################################################################

# Streamlit UI Components
st.set_page_config(layout="wide")
st.title("Indiegogo Project Scraper")

# Input for search term
search_term = st.text_input("Enter search term:", "sports")

# Initialize session state
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame()

# Button to start scraping
if st.button("Scrape Data"):
    with st.spinner('Scraping data...'):
        st.session_state['data'] = scrape_data(search_term)
        st.success('Scraping completed!')

# Display data
st.dataframe(st.session_state['data'])

# Button to download CSV
if st.button('Export as CSV') and not st.session_state['data'].empty:
    tmp_download_link = get_table_download_link(st.session_state['data'])
    st.markdown(tmp_download_link, unsafe_allow_html=True)
