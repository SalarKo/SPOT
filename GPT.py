import openai
import re
import csv
from dotenv import load_dotenv
import os

#Load environment variables
load_dotenv()

#OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")


#Function to extract names and phone numbers from the text
def extract_names_and_numbers(text):
    #Regx for tlf nr
    phone_pattern = r'\+?\d[\d -]{7,}\d'
    phone_numbers = re.findall(phone_pattern, text)

    #Prepare the output data structure
    extracted_data = []

    for phone in phone_numbers:
        #Prompt GPT-3 to find the name associated with the phone number
        prompt = f"In the following text, find out who the phone number belongs to, such as the person's name or company name. If unknown, respond with 'Unknown'.\n\nText:\n{text}\n\nPhone Number: {phone}"

        try:
            #Use ChatCompletion for the new API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  #Use the desired model (e.g., gpt-3.5-turbo)
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.5,
            )

            name = response['choices'][0]['message']['content'].strip()
            extracted_data.append((name, phone))

        except Exception as e:
            print(f"Error occurred while contacting OpenAI API: {e}")

    return extracted_data


#Read text from the extract.txt file
with open('extract.txt', 'r') as file:
    text = file.read()

#Extract names and phone numbers
results = extract_names_and_numbers(text)

#Save the results in a CSV file
with open('contacts.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(['Name', 'Telephone'])  # Header row
    csv_writer.writerows(results)  # Data rows

print("Extraction completed and saved to 'contacts.csv'.")