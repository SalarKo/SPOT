import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
import csv
import os
from flask import Flask, request, render_template, send_from_directory
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

app = Flask(__name__)

# Function to extract text from PDF using OCR
def extract_text_from_pdf_images(pdf_path, zoom=2):
    doc = fitz.open(pdf_path)
    ocr_text = ""

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        image = Image.open(io.BytesIO(pix.tobytes("png")))
        text_from_image = pytesseract.image_to_string(image)
        ocr_text += text_from_image
        print(f"Processed page {page_num + 1} with OCR.")

    doc.close()
    return ocr_text

# Function to find Danish phone numbers
def find_danish_phone_numbers(text):
    phone_regex = r"\b(?:\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2})\b"
    phone_numbers = re.findall(phone_regex, text)
    return phone_numbers

# Function to clean phone numbers
def clean_phone_numbers(phone_numbers):
    cleaned_numbers = [num.replace(" ", "") for num in phone_numbers if "." not in num and "-" not in num]
    valid_numbers = [num for num in cleaned_numbers if len(num) == 8 and num.isdigit()]
    unique_numbers = list(set(valid_numbers))
    return unique_numbers

# Function to save phone numbers to CSV
def save_to_csv(phone_numbers, pdf_path):
    dir_name = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    cleaned_csv_filename = os.path.join(dir_name, f"{base_name}_cleaned_phone_numbers.csv")

    with open(cleaned_csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Phone Number'])
        for number in phone_numbers:
            writer.writerow([number])

    print(f"Cleaned phone numbers saved to '{cleaned_csv_filename}'.")

# Function to load phone numbers from CSV
def load_phone_numbers_from_csv(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    return df['Phone Number'].astype(str).tolist()

# Function to fetch company info
def fetch_company_info(phone_numbers, pdf_path):
    options = Options()
    #options.add_argument('--headless') #couldnt make this work
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)


    company_info = []

    for phone_number in phone_numbers:
        formatted_number = phone_number.strip()
        url = f'https://www.krak.dk/{formatted_number}/firmaer'
        driver.get(url)

        relative_divs = driver.find_elements(By.CSS_SELECTOR, 'div.relative')

        for div in relative_divs:
            phone_link = div.find_elements(By.CSS_SELECTOR, 'a[data-guv-click="company_phone_show"]')

            if phone_link:
                phone_text = phone_link[0].text
                formatted_phone_number = re.sub(r'\s+', '', phone_text.split('...')[0])

                if formatted_phone_number[:6] == formatted_number[:6]:
                    company_name_element = div.find_element(By.CSS_SELECTOR, 'h2#company-link-name')
                    company_name = company_name_element.text

                    print(f'Match found: {formatted_phone_number} from URL: {formatted_number}')
                    print(f'Company Name: {company_name}')
                    company_info.append((phone_number, company_name))

    dir_name = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    company_info_csv_filename = os.path.join(dir_name, f"{base_name}_company_info.csv")

    if company_info:
        with open(company_info_csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Phone Number', 'Company Name'])
            writer.writerows(company_info)
        print(f"Company information saved to '{company_info_csv_filename}'.")

    driver.quit()

# Flask routes
@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return {"error": "No file uploaded!"}, 400
    file = request.files['file']

    if file.filename == '':
        return {"error": "No file selected!"}, 400

    pdf_path = os.path.join('uploads', file.filename)
    file.save(pdf_path)

    ocr_text = extract_text_from_pdf_images(pdf_path)
    raw_phone_numbers = find_danish_phone_numbers(ocr_text)
    cleaned_phone_numbers = clean_phone_numbers(raw_phone_numbers)

    if cleaned_phone_numbers:
        save_to_csv(cleaned_phone_numbers, pdf_path)

        phone_numbers_csv_path = os.path.join(os.path.dirname(pdf_path),
                                              f"{os.path.splitext(os.path.basename(pdf_path))[0]}_cleaned_phone_numbers.csv")
        phone_numbers = load_phone_numbers_from_csv(phone_numbers_csv_path)
        fetch_company_info(phone_numbers, pdf_path)

        # Construct the path to the _company_info.csv file
        company_info_csv_path = os.path.join(os.path.dirname(pdf_path),
                                             f"{os.path.splitext(os.path.basename(pdf_path))[0]}_company_info.csv")

        # Return a JSON response with the download link information
        return {
            "upload": {"message": "Processing complete! Check your CSV files."},
            "process": {
                "message": "Company information saved successfully.",
                "csv_file": f"{os.path.basename(company_info_csv_path)}"  # just the filename
            }
        }, 200
    else:
        return {"error": "No valid Danish phone numbers found."}, 400

# Route to download the CSV file
@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(debug=True)
