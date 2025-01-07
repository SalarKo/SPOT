import io
import re
import os
import time
import pytesseract
import fitz
from PIL import Image
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
    regex = r"\b(?:\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2})\b"
    regex_2 = r"(?:\b(?:Tel\.|Tlf\.)?\s*)?"
    regex_3 = r"\b\d(?:\s?\d){7}\b"
    numbers = re.findall(regex, text)
    numbers_2 = re.findall(regex_2, text)
    numbers_3 = re.findall(regex_3, text)
    phone_numbers = [x for n in (numbers,numbers_2,numbers_3) for x in n]
    return phone_numbers

# Function to clean phone numbers
def clean_phone_numbers(phone_numbers):
    cleaned_numbers = [num.replace(" ", "") for num in phone_numbers if "." not in num and "-" not in num]
    valid_numbers = [num for num in cleaned_numbers if len(num) == 8 and num.isdigit()]
    unique_numbers = list(set(valid_numbers))
    print(valid_numbers)
    print(unique_numbers)
    print("unique phone numbers: " + str(len(unique_numbers)))
    return unique_numbers

# Function to fetch company info
def fetch_company_info(phone_numbers, output_path):
    options = Options()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    company_info = []

    for phone_number in phone_numbers:
        formatted_number = phone_number.strip()
        url = f'https://www.krak.dk/{formatted_number}/firmaer'
        driver.get(url)

        relative_divs = driver.find_elements(By.CSS_SELECTOR, 'div.relative')

        for div in relative_divs:
            time.sleep(3)
            phone_link = div.find_elements(By.CSS_SELECTOR, 'a[data-guv-click="company_phone_show"]')

            if phone_link:
                phone_text = phone_link[0].text
                formatted_phone_number = re.sub(r'\s+', '', phone_text.split('...')[0])

                if formatted_phone_number[:6] == formatted_number[:6]:
                    company_name_element = div.find_element(By.CSS_SELECTOR, 'h2#company-link-name')
                    company_name = company_name_element.text

                    # Enhanced postal info extraction
                    postal_info = ""
                    spans = div.find_elements(By.CSS_SELECTOR, 'span')
                    for span in spans:
                        if "Åbent" in span.get_attribute("class") or span.text.strip() == ",":
                            continue

                        # Split text by commas and strip whitespace
                        span_texts = span.text.strip().split(',')

                        for text in span_texts:
                            text = text.strip()
                            # Check for a match with postal code and city format
                            match = re.search(r"(\d{4})\s+([A-Za-zæøåÆØÅ\s]+)", text)
                            if match:
                                postal_info = f"{match.group(1)} {match.group(2).strip()}"
                                break  # Stop once we find the first valid postal info

                        if postal_info:  # Break outer loop if postal info has been found
                            break

                    print(f'Match found: {formatted_phone_number} from URL: {formatted_number}')
                    print(f'Company Name: {company_name}')
                    print(f'Postal Info: {postal_info}')

                    company_info.append((phone_number, company_name, postal_info))

    driver.quit()

    # Save to Excel
    if company_info:
        df = pd.DataFrame(company_info, columns=['Phone Number', 'Company Name', 'Postal Info'])
        excel_filename = os.path.join('output', f"{os.path.splitext(os.path.basename(output_path))[0]}_company_info.xlsx")

        # Check if file already exists and handle it
        if os.path.exists(excel_filename):
            # Generate a new filename to avoid overwriting
            base, ext = os.path.splitext(excel_filename)
            counter = 1
            while os.path.exists(excel_filename):
                excel_filename = f"{base}_{counter}{ext}"
                counter += 1

        df.to_excel(excel_filename, index=False)
        print(f"Company information saved to '{excel_filename}'.")

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
    output_path = os.path.join('output', file.filename)

    file.save(output_path)

    ocr_text = extract_text_from_pdf_images(pdf_path)
    raw_phone_numbers = find_danish_phone_numbers(ocr_text)
    cleaned_phone_numbers = clean_phone_numbers(raw_phone_numbers)

    if cleaned_phone_numbers:
        fetch_company_info(cleaned_phone_numbers, output_path)

        # Construct the path to the Excel file
        company_info_excel_path = os.path.join('output',
                                               f"{os.path.splitext(os.path.basename(output_path))[0]}_company_info.xlsx")

        # Construct the download URL
        download_url = f"/output/{os.path.basename(company_info_excel_path)}"
        print(f"Excel file path: {company_info_excel_path}")
        # Return a JSON response with the download link information
        return {
            "output": {"message": "Processing complete! Check your Excel file."},
            "process": {
                "message": "Company information saved successfully.",
                "excel_file": os.path.basename(company_info_excel_path)  # Filename for downloading
            }
        }, 200
    else:
        return {"error": "No valid Danish phone numbers found."}, 400

# Route to download the Excel file
@app.route('/output/<filename>')
def download_file(filename):
    return send_from_directory('output', filename)

if __name__ == '__main__':
    app.run(debug=True)
