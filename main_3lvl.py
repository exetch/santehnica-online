import json
import re
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from selenium import webdriver
import time

# Функция для проверки наличия размеров или "_sm" в ссылке и значении
def has_size_or_sm_pattern(link, value):
    """
    Проверяет, содержит ли ссылка или значение шаблон размера или "sm".

    Args:
        link (str): Строка, представляющая ссылку.
        value (str): Строка, представляющая значение.

    Returns:
        bool: True, если ссылка или значение содержат шаблон размера или "sm", иначе False.
    """
    # Шаблон для размера в формате "123x456"
    size_pattern = r'\d{2,3}x\d{2,3}'

    # Шаблон для "sm" в формате "123_sm"
    sm_pattern = r"\d{2,3}_sm"

    # Проверяем наличие шаблона размера и "sm" в ссылке и значении
    is_link_has_size = re.search(size_pattern, link)
    is_link_has_sm = re.search(sm_pattern, link)
    is_value_has_size = re.search(size_pattern, value)
    is_value_has_sm = re.search(sm_pattern, value)

    # Возвращаем True, если хотя бы одно из условий выполняется
    return (is_link_has_size and (is_value_has_sm or is_value_has_size)) or (
                is_link_has_sm and (is_value_has_sm or is_value_has_size))
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
        # Создаем экземпляр браузера
        driver = webdriver.Chrome()
        driver.get(link)
        time.sleep(2)

        # Проверяем <title> на странице на наличие "404 Not Found"
        if driver.title == "404 Not Found":
            print(f"Ссылка не существует: {link}")
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


def data_processing_3lvl_parallel(working_links_1lvl, working_links_1lv2, file_output, num_threads=5):
    """
    Обрабатывает ссылки третьего уровня, используя рабочие ссылки первого и второго уровней,
    и сохраняет рабочие ссылки третьего уровня в файл.

    Args:
        working_links_1lvl (str): Путь к файлу с рабочими ссылками первого уровня (JSON формат).
        working_links_1lv2 (str): Путь к файлу с рабочими ссылками второго уровня (JSON формат).
        file_output (str): Путь к файлу, в который будут сохранены рабочие ссылки третьего уровня (JSON формат).
        num_threads (int, optional): Количество потоков для параллельной обработки ссылок. По умолчанию 5.

    Returns:
        None
    """
    # Загрузка рабочих ссылок первого уровня
    with open(working_links_1lvl, 'r', encoding='utf-8') as file:
        data_dict_1lvl = json.load(file)
        refs_data = {}
        for key, url in data_dict_1lvl.items():
            last_part = url.split('/')[-1]
            refs_data[key] = last_part

    # Загрузка рабочих ссылок второго уровня
    with open(working_links_1lv2, 'r', encoding='utf-8') as refs_file:
        data_dict_2lvl = json.load(refs_file)

    filtered_links = {}

    # Фильтрация ссылок третьего уровня
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

    # Сохранение рабочих ссылок третьего уровня в файл
    with open(file_output, 'w', encoding='utf-8') as json_file:
        json.dump(working_links, json_file, ensure_ascii=False, indent=4)
    print(f"Третий уровень ссылок успешно сохранен в {file_output}")
