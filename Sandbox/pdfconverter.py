import pymupdf

doc = pymupdf.open('testpaper.pdf')
out = open("output.txt", "wb")
for page in doc:
    text = page.get_text().encode("utf8")
    out.write(text)  # write text of page
    out.write(bytes((12,)))
out.close()
