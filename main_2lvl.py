import json
import re
from itertools import permutations
from selenium import webdriver
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.chrome.options import Options


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
    return (is_first_value_size and is_second_value_size) or (is_first_sm and is_second_sm) or (is_first_value_size and is_second_sm) or (is_first_sm and is_second_value_size)

def process_link(link, working_links):
    """
    Обрабатывает одну ссылку, проверяя наличие страницы "404 Not Found" и извлекая рабочие ссылки.

    Args:
        link (str): Ссылка для проверки.
        working_links (dict): Словарь, в котором сохраняются рабочие ссылки.

    Returns:
        str or None: Возвращает рабочую ссылку или None, если ссылка не существует.
    """
    try:
        driver = webdriver.Chrome()

        driver.get(link)
        time.sleep(2)

        # Проверяем <title> на странице на наличие "404 Not Found"
        if driver.title == "404 Not Found":
            return None

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
        # Закрываем браузер после завершения обработки
        driver.quit()

def data_processing_2lvl_parallel(file_input, file_output, parent_url, num_threads=6):
    """
    Обрабатывает ссылки второго уровня параллельно, используя множество потоков,
    и сохраняет рабочие ссылки в файл.

    Args:
        file_input (str): Путь к файлу с данными в формате JSON.
        file_output (str): Путь к файлу, в который будут сохранены рабочие ссылки второго уровня (JSON формат).
        parent_url (str): Базовый URL для построения полных ссылок.
        num_threads (int, optional): Количество потоков для параллельной обработки ссылок. По умолчанию 5.

    Returns:
        None
    """
    # Загрузка данных из файла
    with open(file_input, 'r', encoding='utf-8') as file:
        data_dict = json.load(file)

        # Извлечение значений из ссылок первого уровня
        values_list = [link.split("/")[-1] for link in data_dict.values()]

        # Создание всех возможных комбинаций пар значений
        permutations_list = list(permutations(values_list, 2))

        # Фильтрация комбинаций: исключение "brand" и комбинаций с размерами или "sm"
        filtered_permutations = [combo for combo in permutations_list if
                                 not combo[0].startswith('brand') and not both_values_are_sizes(combo)]

        # Построение полных ссылок для проверки
        links_to_check = [f"{parent_url}{first}/{second}/" for first, second in filtered_permutations]

        # Разбиваем список ссылок на пакеты
        batches = [links_to_check[i:i + 1000] for i in range(0, len(links_to_check), 1000)]

        processed_links = 0
        good_links = 0
        working_links = {}
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for batch in batches:
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
            del futures
            del batch
# Сохранение окончательного списка рабочих ссылок в файл
    with open(file_output, 'w', encoding='utf-8') as json_file:
        json.dump(working_links, json_file, ensure_ascii=False, indent=4)
    print(f"Второй уровень ссылок успешно сохранен в {file_output}")