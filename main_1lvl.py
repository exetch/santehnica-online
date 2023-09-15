from selenium import webdriver
from bs4 import BeautifulSoup
import re
import json

if __name__ == "__main__":
    driver = webdriver.Chrome()
    driver.maximize_window()

    url = "https://santehnika-online.ru/vanny/"
    driver.get(url)
    page_source = driver.page_source
    driver.quit()
    soup = BeautifulSoup(page_source, 'html.parser')
    pattern = r'var __SD__ = {"Location":{"option":.*?};'
    matches = re.findall(pattern, str(soup))
    for match in matches:
        json_match = re.search(r'\{.*\}', match).group()
        data_dict = json.loads(json_match)

    with open('data_vanny.json', 'w', encoding='utf-8') as json_file:
        json.dump(data_dict, json_file, ensure_ascii=False, indent=4)

    with open('data_vanny.json', 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    selected_data = {
        'catalogPopularBrandsMaster': data.get('catalogPopularBrandsMaster'),
        'popularManufacturers': data.get('popularManufacturersMobile'),
        'catalogPopularCategories': data.get('catalogPopularCategories')
    }
    with open('popular_categories_vanny.json', 'w', encoding='utf-8') as new_json_file:
        json.dump(selected_data, new_json_file, ensure_ascii=False, indent=4)
    print("Данные успешно сохранены")
