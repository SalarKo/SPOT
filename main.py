import pytesseract
from PIL import Image
#https://www.educative.io/answers/how-to-extract-text-from-an-image-in-python


#Path to Tesseract (its for Homebrew installation. GPT helped me a TONE to figure this part out)
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

#Open the image and extract text
image = Image.open('image.png')
text = pytesseract.image_to_string(image)

#Save the extracted text to a file
with open('extract.txt', 'w') as file:
    file.write(text)

print("Text extraction completed.")