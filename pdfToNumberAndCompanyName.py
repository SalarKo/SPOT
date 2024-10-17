import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
import csv  
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os  

# Do 
# pip install PyMuPDF pytesseract pillow selenium webdriver-manager pandas
#
# Also download and install the file below into the same folder as this file
# https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe


# This script extracts text from a PDF file using OCR, 
# identifies Danish phone numbers, cleans and saves them to a CSV file, 
# and retrieves company information associated with the phone numbers using web scraping.

# Function to render each page as an image and perform OCR
def extract_text_from_pdf_images(pdf_path, zoom=2):
    doc = fitz.open(pdf_path)
    ocr_text = ""
    
    # Iterate through the pages
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)  # Load the page
        # Use a zoom factor to increase the resolution (optional, default is 2x)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)  # Render the page as a pixmap (image)
        
        # Convert pixmap to an image and run OCR
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        text_from_image = pytesseract.image_to_string(image)
        ocr_text += text_from_image
        print(f"Processed page {page_num + 1} with OCR.")
    
    doc.close()
    return ocr_text

# Function to find Danish phone numbers
def find_danish_phone_numbers(text):
    # Regex for Danish phone numbers (8 digits, optionally grouped in pairs)
    phone_regex = r"\b(?:\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2})\b"
    
    # Find all matches
    phone_numbers = re.findall(phone_regex, text)
    
    return phone_numbers

# Function to clean phone numbers
def clean_phone_numbers(phone_numbers):
    # Step 1: Remove numbers that contain '.' or '-'
    cleaned_numbers = [num.replace(" ", "") for num in phone_numbers if "." not in num and "-" not in num]
    
    # Step 2: Only keep numbers that are exactly 8 digits long
    valid_numbers = [num for num in cleaned_numbers if len(num) == 8 and num.isdigit()]
    
    # Step 3: Remove duplicates by converting the list to a set and back to a list
    unique_numbers = list(set(valid_numbers))
    
    return unique_numbers

# Function to save phone numbers to a CSV file with a dynamic filename
def save_to_csv(phone_numbers, pdf_path):
    # Get the directory and base name of the PDF file
    dir_name = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Create a dynamic filename for cleaned phone numbers
    cleaned_csv_filename = os.path.join(dir_name, f"{base_name}_cleaned_phone_numbers.csv")
    
    with open(cleaned_csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Phone Number'])  # Write header
        for number in phone_numbers:
            writer.writerow([number])  # Write each number
            
    print(f"Cleaned phone numbers saved to '{cleaned_csv_filename}'.")

# Function to load phone numbers from CSV
def load_phone_numbers_from_csv(file_path):
    """Loads phone numbers from a CSV file."""
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()  # Remove leading/trailing spaces from headers
    return df['Phone Number'].astype(str).tolist()  # Adjusted to the correct column name

# Function to fetch company names using Selenium and save to CSV with a dynamic filename
def fetch_company_info(phone_numbers, pdf_path):
    # Set up Chrome options
    options = Options()
    # options.add_argument('--headless')  # Uncomment this line if you want headless mode

    # Initialize the WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # List to store matched phone numbers and company names
    company_info = []

    # Loop through each phone number
    for phone_number in phone_numbers:
        # Format the phone number for the URL
        formatted_number = phone_number.strip()  # Strip any whitespace
        url = f'https://www.krak.dk/{formatted_number}/firmaer'

        # Navigate to the URL
        driver.get(url)

        # Get the div elements with class "relative"
        relative_divs = driver.find_elements(By.CSS_SELECTOR, 'div.relative')

        # Loop through each relative div to find the phone number and company name
        for div in relative_divs:
            # Find the <a> tag containing the phone number
            phone_link = div.find_elements(By.CSS_SELECTOR, 'a[data-guv-click="company_phone_show"]')
            
            # Check if the phone link is found and extract the phone number
            if phone_link:
                # Extract the text from the <a> tag
                phone_text = phone_link[0].text  # Get the first matching phone link
                
                # Format the phone number to remove spaces and the '... Vis' part
                formatted_phone_number = re.sub(r'\s+', '', phone_text.split('...')[0])  # Remove spaces and keep digits
                
                # Compare the first six digits
                if formatted_phone_number[:6] == formatted_number[:6]:
                    # If there's a match, find the company name
                    company_name_element = div.find_element(By.CSS_SELECTOR, 'h2#company-link-name')
                    company_name = company_name_element.text
                    
                    print(f'Match found: {formatted_phone_number} from URL: {formatted_number}')
                    print(f'Company Name: {company_name}')

                    # Store the result
                    company_info.append((phone_number, company_name))
    
    # Create a dynamic filename for company information
    dir_name = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    company_info_csv_filename = os.path.join(dir_name, f"{base_name}_company_info.csv")

    # Save company information to CSV
    if company_info:
        with open(company_info_csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Phone Number', 'Company Name'])  # Write header
            writer.writerows(company_info)  # Write all rows at once
        print(f"Company information saved to '{company_info_csv_filename}'.")
    
    # Close the WebDriver
    driver.quit()

# Example usage:
pdf_file_path = 'downloaded_pdfs\Roskilde Avis - Uge 40\Roskilde Avis - Uge 40.pdf'  # Updated PDF path

# Perform OCR on each page of the PDF
ocr_text = extract_text_from_pdf_images(pdf_file_path)

# Find Danish phone numbers in the OCR result
raw_phone_numbers = find_danish_phone_numbers(ocr_text)

# Clean the found phone numbers
cleaned_phone_numbers = clean_phone_numbers(raw_phone_numbers)

# Print cleaned phone numbers
if cleaned_phone_numbers:
    print("Cleaned Danish Phone Numbers:")
    for phone_number in cleaned_phone_numbers:
        print(phone_number)
    
    # Save cleaned phone numbers to a CSV file
    save_to_csv(cleaned_phone_numbers, pdf_file_path)
    
    # Load phone numbers from the saved CSV
    phone_numbers_csv_path = os.path.join(os.path.dirname(pdf_file_path), f"{os.path.splitext(os.path.basename(pdf_file_path))[0]}_cleaned_phone_numbers.csv")
    phone_numbers = load_phone_numbers_from_csv(phone_numbers_csv_path)
    
    # Fetch company info for cleaned phone numbers and save to CSV
    fetch_company_info(phone_numbers, pdf_file_path)
else:
    print("No valid Danish phone numbers found.")
