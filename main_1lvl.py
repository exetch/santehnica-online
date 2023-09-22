from selenium import webdriver
from bs4 import BeautifulSoup
from main_2lvl import data_processing_2lvl_parallel
from main_3lvl import data_processing_3lvl_parallel
from multiprocessing_2lvl import data_processing_2lvl_multiprocessing
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from to_exel import save_to_excel
import re
import json
import time


URL = "https://santehnika-online.ru/unitazy/"
working_directory = URL.rstrip('/').split('/')[-1]
WORKING_LINKS_1LVL = f'working_links_{working_directory}_1lvl.json'
WORKING_LINKS_2LVL = f'working_links_{working_directory}_2lvl.json'
WORKING_LINKS_3LVL = f'working_links_{working_directory}_3lvl.json'
EXCEL_FILE = f'combined_links_{working_directory}.xlsx'
def count_elements_in_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        return len(data)
    except FileNotFoundError:
        return 0

if __name__ == "__main__":
    # Запускаем таймер для измерения времени выполнения
    start_time = time.time()
    driver = webdriver.Chrome()
    # chrome_service = Service('C:\\chromedriver')
    # chrome_options = Options()
    # chrome_options.add_argument(
    #     'user_agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
    # chrome_options.add_argument('--headless')
    #
    # driver = webdriver.Chrome(options=chrome_options)
    url = URL
    driver.get(url)

    # Получаем HTML-код страницы
    page_source = driver.page_source
    # Закрываем веб-драйвер
    driver.quit()

    # Создаем объект BeautifulSoup для парсинга HTML
    soup = BeautifulSoup(page_source, 'html.parser')

    # Используем регулярное выражение для извлечения данных из JavaScript объекта
    pattern = r'var __SD__ = {"Location":{"option":.*?};'
    matches = re.findall(pattern, str(soup))
    for match in matches:
        json_match = re.search(r'\{.*\}', match).group()
        data_dict = json.loads(json_match)
    # Выбираем интересующие нас данные из data_dict
    selected_data = {
        'catalogPopularBrandsMaster': data_dict.get('catalogPopularBrandsMaster'),
        'popularManufacturers': data_dict.get('popularManufacturers'),
        'catalogPopularCategories': data_dict.get('catalogPopularCategories')
    }
    result_dict = {}


    # Обрабатываем данные о популярных брендах
    for item in selected_data['catalogPopularBrandsMaster']['data']['items']:
        link_parts = item['link'].split("/")
        title = item.get('title', '')
        result_dict[title] = url + link_parts[-2]

    # Обрабатываем данные о популярных производителях
    for item in selected_data['popularManufacturers']['data']['items']:
        link_parts = item['link'].split("/")
        title = item.get('title', '')
        result_dict[title] = url + link_parts[-2]

    # Обрабатываем данные о популярных категориях
    for category in selected_data['catalogPopularCategories']['data']['items']:
        for item in category['items']:
            link_parts = item['link'].split("/")
            title = item.get('title', '')
            result_dict[title] = url + link_parts[-2]

    # Сохраняем данные о первом уровне ссылок в файл JSON
    with open(WORKING_LINKS_1LVL, 'w', encoding='utf-8') as new_json_file:
        json.dump(result_dict, new_json_file, ensure_ascii=False, indent=4)
    print(f"Первый уровень ссылок успешно сохранен в {WORKING_LINKS_1LVL}")

    # # Обрабатываем ссылки второго и третьего уровней параллельно
    data_processing_2lvl_parallel(WORKING_LINKS_1LVL, WORKING_LINKS_2LVL, URL)
    data_processing_3lvl_parallel(WORKING_LINKS_1LVL, WORKING_LINKS_2LVL, WORKING_LINKS_3LVL)
    # Считаем количество обработанных ссылок на каждом уровне и общее количество
    count_1lvl = count_elements_in_json_file(WORKING_LINKS_1LVL)
    count_2lvl = count_elements_in_json_file(WORKING_LINKS_2LVL)
    count_3lvl = count_elements_in_json_file(WORKING_LINKS_3LVL)
    count_total = count_1lvl + count_2lvl + count_3lvl

    # Сохраняем данные в Excel файл
    save_to_excel(WORKING_LINKS_1LVL, WORKING_LINKS_2LVL, WORKING_LINKS_3LVL, EXCEL_FILE)

    # Завершаем таймер и выводим информацию о времени выполнения и общем количестве ссылок
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Время выполнения скрипта: {elapsed_time} секунд")
    print(f"Всего найдено {count_total} ссылок")