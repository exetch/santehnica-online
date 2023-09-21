import json
import re
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from selenium import webdriver
import time

# Функция для проверки наличия размеров или "_sm" в ссылке и значении
def has_size_or_sm_pattern(link, value):
    size_pattern = r'\d{2,3}x\d{2,3}'
    sm_pattern = r"\d{2,3}_sm"
    is_link_has_size = re.search(size_pattern, link)
    is_link_has_sm = re.search(sm_pattern, link)
    is_value_has_size = re.search(size_pattern, value)
    is_value_has_sm = re.search(sm_pattern, value)
    return (is_link_has_size and (is_value_has_sm or is_value_has_size)) or (is_link_has_sm and (is_value_has_sm or is_value_has_size))
def process_link(link, working_links):
    try:
        driver = webdriver.Chrome()
        driver.get(link)
        time.sleep(2)

        # Проверяем <title> на странице
        if driver.title == "404 Not Found":
            print(f"Ссылка не существует: {link}")
            return

        # Получаем HTML-код страницы
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Ищем элемент с классом "b-title b-title--h1" и извлекаем текст из него
        title_element = soup.find('h1', class_='b-title b-title--h1')
        if title_element:
            title = title_element.find('span').text.strip()
            working_links[title] = link
            print(f"Рабочая ссылка: {link}")
            return link

    except Exception as e:
        pass
    finally:
        driver.quit()

def data_processing_3lvl_parallel(working_links_1lvl, working_links_1lv2, file_output, num_threads=5):
    with open(working_links_1lvl, 'r', encoding='utf-8') as file:
        data_dict_1lvl = json.load(file)
        refs_data = {}
        for key, url in data_dict_1lvl.items():
            last_part = url.split('/')[-1]
            refs_data[key] = last_part
    with open(working_links_1lv2, 'r', encoding='utf-8') as refs_file:
        data_dict_2lvl = json.load(refs_file)
    filtered_links = {}

    for link_name, link_url in data_dict_2lvl.items():
        for name, value in refs_data.items():
            if not 'brand' in link_url and (value not in link_url) and not has_size_or_sm_pattern(link_url, value):
                new_link_name = f"{link_name} {name}"
                new_link_url = f"{link_url}/{value}"
                filtered_links[new_link_name] = new_link_url

    links_to_check = list(filtered_links.values())

    working_links = {}
    processed_links = 0
    good_links = 0

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(process_link, link, working_links): link for link in links_to_check}
        for future in futures:
            future.result()
            if future.result():
                good_links += 1
                processed_links += 1
                progress_percent = (processed_links / len(links_to_check)) * 100
                print(f"Прогресс: {progress_percent:.2f}% ({processed_links}/{len(links_to_check)})")
                print(f"Всего рабочих ссылок {good_links} ")

    with open(file_output, 'w', encoding='utf-8') as json_file:
        json.dump(working_links, json_file, ensure_ascii=False, indent=4)
    print(f"Третий уровень ссылок успешно сохранен в {file_output}")
