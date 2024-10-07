file = open("output.txt", "r", encoding='utf8')
hardstop = 22
i = 0

for line in file:
    split = line.split(' ')
    print('\n')
    print(split)
    if hardstop:
        i += 1
    if i == hardstop:
        break
