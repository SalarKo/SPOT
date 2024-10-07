# Make Skimmer work. RegEx
import re
file = open("output.txt", "r", encoding='utf8')
content = file.read()

def check_telephone_number(text):  
    pattern = r'[\+\(]?[0-9() -]{8,15}'  # Adjusted length for phone numbers
    return re.findall(pattern, text)

def check_duplicates(list):


numbers = check_telephone_number(content)
print(numbers)