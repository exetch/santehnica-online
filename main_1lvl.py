from selenium import webdriver
from bs4 import BeautifulSoup
from main_2lvl import data_processing_2lvl
from main_3lvl import data_processing_3lvl
from to_exel import save_to_excel
import re
import json
import time
WORKING_LINKS_1LVL = 'working_links_1lvl.json'
WORKING_LINKS_2LVL = 'working_links_2lvl.json'
WORKING_LINKS_3LVL = 'working_links_3lvl.json'
EXCEL_FILE = 'combined_links.xlsx'
URL = "https://santehnika-online.ru/dushevye_ograzhdeniya/dushevye_poddony/"
def count_elements_in_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        return len(data)
    except FileNotFoundError:
        return 0

if __name__ == "__main__":
    start_time = time.time()

    driver = webdriver.Chrome()
    driver.maximize_window()
    url = URL
    driver.get(url)
    page_source = driver.page_source
    driver.quit()
    soup = BeautifulSoup(page_source, 'html.parser')
    pattern = r'var __SD__ = {"Location":{"option":.*?};'
    matches = re.findall(pattern, str(soup))
    for match in matches:
        json_match = re.search(r'\{.*\}', match).group()
        data_dict = json.loads(json_match)

    #ACHTUNG!!!!Здесь нужно быть осторожным!!! Смотреть получаемый data_dict и в нем искать словри с сылками, они могут быть разные в разных категориях!!!

    selected_data = {
        'catalogPopularBrandsMaster': data_dict.get('catalogPopularBrandsMaster'),
        'popularManufacturers': data_dict.get('popularManufacturers'),
        'catalogPopularCategories': data_dict.get('catalogPopularCategories')
    }
    result_dict = {}

    for item in selected_data['catalogPopularBrandsMaster']['data']['items']:
        link_parts = item['link'].split("/")
        title = item.get('title', '')
        result_dict[title] = url + link_parts[-2]

    for item in selected_data['popularManufacturers']['data']['items']:
        link_parts = item['link'].split("/")
        title = item.get('title', '')
        result_dict[title] = url + link_parts[-2]

    for category in selected_data['catalogPopularCategories']['data']['items']:
        for item in category['items']:
            link_parts = item['link'].split("/")
            title = item.get('title', '')
            result_dict[title] = url + link_parts[-2]
    with open('working_links_1lvl.json', 'w', encoding='utf-8') as new_json_file:
        json.dump(result_dict, new_json_file, ensure_ascii=False, indent=4)
    print("Первый уровень ссылок успешно сохранен в working_links_1lvl.json")
    data_processing_2lvl(WORKING_LINKS_1LVL, WORKING_LINKS_2LVL, URL)
    data_processing_3lvl(WORKING_LINKS_1LVL, WORKING_LINKS_2LVL, WORKING_LINKS_3LVL)
    count_1lvl = count_elements_in_json_file(WORKING_LINKS_1LVL)
    count_2lvl = count_elements_in_json_file(WORKING_LINKS_2LVL)
    count_3lvl = count_elements_in_json_file(WORKING_LINKS_3LVL)
    count_total = count_1lvl + count_2lvl + count_3lvl
    save_to_excel(WORKING_LINKS_1LVL, WORKING_LINKS_2LVL, WORKING_LINKS_3LVL, EXCEL_FILE)
    end_time = time.time()

    elapsed_time = end_time - start_time

    print(f"Время выполнения скрипта: {elapsed_time} секнуд")
    print(f"Всего найдено {count_total} ссылок")