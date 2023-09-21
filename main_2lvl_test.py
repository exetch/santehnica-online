import json
import re
from itertools import permutations
from selenium import webdriver
import time
from bs4 import BeautifulSoup


def both_values_are_sizes(combination):
    first_value, second_value = combination
    size_pattern = r"\d{2,3}\s*x\s*\d{2,3}"
    sm_pattern = r"\b\d{2,3}_sm\b"
    is_first_value_size = re.search(size_pattern, first_value)
    is_second_value_size = re.search(size_pattern, second_value)
    is_first_sm = re.search(sm_pattern, first_value)
    is_second_sm = re.search(sm_pattern, second_value)
    return (is_first_value_size and is_second_value_size) or (is_first_sm and is_second_sm) or (is_first_value_size and is_second_sm) or (is_first_sm and is_second_value_size)

def check_link_availability(driver, combination):
    first_key, second_key = combination
    url = f"https://santehnika-online.ru/dushevye_ograzhdeniya/ugolki/{first_key}/{second_key}/"
    try:
        driver.get(url)
        time.sleep(2)
        if driver.title != "404 Not Found":
            print(f"Рабочая ссылка {url}")
            return combination, url
    except Exception as e:
        pass
    return None

def data_processing_2lvl(file_input, file_output, parent_url):
    with open(file_input, 'r', encoding='utf-8') as file:
        data_dict = json.load(file)

    values_list = [link.split("/")[-1] for link in data_dict.values()]
    permutations_list = list(permutations(values_list, 2))
    filtered_permutations = [combo for combo in permutations_list if
                             not combo[0].startswith('brand') and not both_values_are_sizes(combo)]
    links_to_check = [f"{parent_url}{first}/{second}/" for first, second
                      in filtered_permutations]
    driver = webdriver.Chrome()
    working_links = {}
    test = links_to_check[:10]
    for link in test:
        try:
            driver.get(link)
            time.sleep(2)

            # Получаем HTML-код страницы
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Проверяем наличие элемента с классом "ZZaEylgLCDvuUySCw8dL heading--lg text--bold"
            error_element = soup.find('div', class_='ZZaEylgLCDvuUySCw8dL heading--lg text--bold')
            if error_element:
                print(f"Ссылка не существует: {link}")

            # Ищем элемент с классом "b-title b-title--h1" и извлекаем текст из него
            title_element = soup.find('h1', class_='b-title b-title--h1')
            if title_element:
                title = title_element.find('span').text.strip()
                working_links[title] = link
                print(f"Рабочая ссылка: {link}")

        except Exception as e:
            pass
    for title, link in working_links.items():
        print(f"Имя: {title}, ссылка: {link}")

    with open(file_output, 'w', encoding='utf-8') as json_file:
        json.dump(working_links, json_file, ensure_ascii=False, indent=4)
    print(f"Второй уровень ссылок успешно сохранен в {file_output}")