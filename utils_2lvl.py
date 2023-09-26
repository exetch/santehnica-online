import json
from curl_cffi import requests
from bs4 import BeautifulSoup
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor
import re


def process_link(link, working_links):
    try:
        response = requests.get(link, impersonate="chrome110", max_redirects=3)

        # Проверяем <title> на странице на наличие "404 Not Found"
        if response.text == "404 Not Found":
            return None

        soup = BeautifulSoup(response.text, "lxml")
        title_element = soup.find('h1', class_='b-title b-title--h1')
        if title_element:
            title = title_element.find('span').text.strip()
            working_links[title] = link
            print(f"Рабочая ссылка: {link}")
            return link
    except Exception as e:
        print(f'ошибка {e}')


def both_values_are_sizes(combination):
    """
    Проверяет, являются ли оба значения в комбинации размерами или "sm".

    Args:
        combination (tuple): Кортеж из двух значений для проверки.

    Returns:
        bool: True, если оба значения являются размерами или "sm", иначе False.
    """
    first_value, second_value = combination
    size_pattern = r"\d{2,3}\s*x\s*\d{2,3}"
    sm_pattern = r"\b\d{2,3}_sm\b"
    is_first_value_size = re.search(size_pattern, first_value)
    is_second_value_size = re.search(size_pattern, second_value)
    is_first_sm = re.search(sm_pattern, first_value)
    is_second_sm = re.search(sm_pattern, second_value)
    return (is_first_value_size and is_second_value_size) or (is_first_sm and is_second_sm) or (
                is_first_value_size and is_second_sm) or (is_first_sm and is_second_value_size)


def get_more_components(path, num_threads=10):
    with open(path, 'r', encoding='utf-8') as file:
        data_dict = json.load(file)
    links_list = [link for link in data_dict.values()]

    new_components = set()

    def process_link(link, num):
        segments = link.split("/")
        levels = len([segment for segment in segments if segment not in ('', 'https:')])
        response = requests.get(link, impersonate="chrome110", max_redirects=3)
        soup = BeautifulSoup(response.text, "lxml")
        container = soup.find("div", class_="zDlIRyYr79ULUEWkhuXu")
        if container:
            page_links = container.find_all("a", class_="btn btn--secondary btn--sm TKq4b_Yrh4HHeHFwEm1l")
            print(f'Проверяем {num} страницу из {len(links_list)}')
            for url in page_links:
                href = url.get("href")
                path_components = href.strip('/').split('/')

                if len(path_components) == levels:
                    new_components.add(path_components[levels - 2])
                    new_components.add(path_components[levels - 1])

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for num, link in enumerate(links_list, start=1):
            executor.submit(process_link, link, num)

    print(f'Удалось найти {len(new_components)} новых компонентов для ссылок')

    values_list = [link.split("/")[-1] for link in data_dict.values()]
    values_set_popular = set(values_list)
    new_unique = new_components - values_set_popular
    updated_values_set = values_set_popular | new_components
    return updated_values_set, new_unique


def data_processing_2lvl_parallel(values_set, file_output, parent_url, num_threads=6):
    # Создание всех возможных комбинаций пар значений
    permutations_list = list(permutations(values_set, 2))

    # Фильтрация комбинаций: исключение "brand" и комбинаций с размерами или "sm"
    filtered_permutations = [combo for combo in permutations_list if
                             not combo[0].startswith('brand') and not both_values_are_sizes(combo)]

    # Построение полных ссылок для проверки
    links_to_check = [f"{parent_url}{first}/{second}/" for first, second in filtered_permutations]

    # Разбиваем список ссылок на пакеты
    batches = [links_to_check[i:i + 1000] for i in range(0, len(links_to_check), 1000)]

    processed_links = 0
    good_links = 0

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for num, batch in enumerate(batches, start=1):
            try:
                with open(file_output, 'r', encoding='utf-8') as file:
                    working_links = json.load(file)
            except FileNotFoundError:
                working_links = {}
            batch_working_links = {}
            futures = {executor.submit(process_link, link, batch_working_links): link for link in batch}
            for future in futures:
                future.result()
                processed_links += 1
                if future.result():
                    good_links += 1
                progress_percent = (processed_links / len(links_to_check)) * 100
                print(f"Прогресс: {progress_percent:.2f}% ({processed_links}/{len(links_to_check)})")
                print(f"Всего рабочих ссылок {good_links} ")
            working_links.update(batch_working_links)
            with open(file_output, 'w', encoding='utf-8') as json_file:
                json.dump(working_links, json_file, ensure_ascii=False, indent=4)
            print(f"Пакет ссылок {num} успешно сохранен в {file_output}")
            del futures
            del batch

    print(f"Второй уровень ссылок успешно сохранен в {file_output}")


def data_processing_3lvl_parallel(values_set, working_links_1lv2, file_output, num_threads=6):
    with open(working_links_1lv2, 'r', encoding='utf-8') as refs_file:
        data_dict_2lvl = json.load(refs_file)

    links_to_check = []

    for link_url in data_dict_2lvl.values():
        for value in values_set:
            combination = (link_url, value)
            if not 'brand' in link_url and (value not in link_url) and not both_values_are_sizes(combination):
                new_link_url = f"{link_url}{value}"
                links_to_check.append(new_link_url)
    batches = [links_to_check[i:i + 1000] for i in range(0, len(links_to_check), 1000)]
    processed_links = 0
    good_links = 0

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for num, batch in enumerate(batches, start=1):
            try:
                with open(file_output, 'r', encoding='utf-8') as file:
                    working_links = json.load(file)
            except FileNotFoundError:
                working_links = {}
            batch_working_links = {}
            futures = {executor.submit(process_link, link, batch_working_links): link for link in batch}
            for future in futures:
                future.result()
                processed_links += 1
                if future.result():
                    good_links += 1
                progress_percent = (processed_links / len(links_to_check)) * 100
                print(f"Прогресс: {progress_percent:.2f}% ({processed_links}/{len(links_to_check)})")
                print(f"Всего рабочих ссылок {good_links} ")
            working_links.update(batch_working_links)
            with open(file_output, 'w', encoding='utf-8') as json_file:
                json.dump(working_links, json_file, ensure_ascii=False, indent=4)
            print(f"Пакет ссылок {num} успешно сохранен в {file_output}")
            del futures
            del batch

    print(f"Третий уровень ссылок успешно сохранен в {file_output}")


def data_processing_1lvl_with_new_components(file_output, parent_link, new_components, num_threads=10):
    with open(file_output, 'r', encoding='utf-8') as file:
        working_links = json.load(file)

    new_links_to_check_for_1lvl = [parent_link + component for component in new_components]
    processed_links = 0
    good_links = 0

    def process_and_update(link):
        result = process_link(link, working_links)
        nonlocal processed_links, good_links
        processed_links += 1
        if result:
            good_links += 1
        progress_percent = (processed_links / len(new_links_to_check_for_1lvl)) * 100
        print(f"Прогресс: {progress_percent:.2f}% ({processed_links}/{len(new_links_to_check_for_1lvl)})")
        print(f"Всего рабочих ссылок {good_links} ")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(process_and_update, new_links_to_check_for_1lvl)

    with open(file_output, 'w', encoding='utf-8') as json_file:
        json.dump(working_links, json_file, ensure_ascii=False, indent=4)

    print(f"Новые ссылки первого уровня успешно сохранены в {file_output}")
