# Make Skimmer work. RegEx
import re
import csv

file = open("output.txt", "r", encoding='utf8')
content = file.read()

def check_telephone_number(text):  
    pattern = r'[\+\(]?[0-9() -]{8,15}'  # Adjusted length for phone numbers
    return re.findall(pattern, text)

def check_duplicates(list):
    templist = []
    for element in list:
        try:
            e = element.replace(" ", "")
            e = e.replace("-", "")
            e = e.replace("+", "")
            number = int(e)
            ismatch = False
            for i in list:
                if number == i:
                    ismatch = True
                    break
            if not ismatch:
                templist.append(number)
        except:
            print("faulty number")
            continue
    return templist

numbers = check_telephone_number(content)
refined = check_duplicates(numbers)

formatted_numbers = [[str(number)] for number in refined]

with open("output.csv", 'w', newline='') as csvfile:
    print("yes")
    writer = csv.writer(csvfile)
    writer.writerows(formatted_numbers)


print("file made")
