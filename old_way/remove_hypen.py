from unidecode import unidecode
corrected_text = []
with open("remove_hypen.txt", "r", encoding='utf-8') as file:
    for row in file:
        corrected_text.append(unidecode(row))

with open("remove_hypen.txt", "w", encoding='utf-8') as file:
    for row in corrected_text:
        file.write(row)