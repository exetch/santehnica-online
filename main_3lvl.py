import json
import re
import concurrent.futures
from selenium import webdriver

# Функция для проверки наличия размеров или "_sm" в ссылке и значении
def has_size_or_sm_pattern(link, value):
    size_pattern = r'\d{2,3}x\d{2,3}'
    sm_pattern = r"\d{2,3}_sm"
    is_link_has_size = re.search(size_pattern, link)
    is_link_has_sm = re.search(sm_pattern, link)
    is_value_has_size = re.search(size_pattern, value)
    is_value_has_sm = re.search(sm_pattern, value)
    return (is_link_has_size and (is_value_has_sm or is_value_has_size)) or (is_link_has_sm and (is_value_has_sm or is_value_has_size))
def check_link_availability(driver, link):
    try:
        driver.get(link)
        if driver.title != "404 Not Found":
            print(f"Рабочая ссылка {link}")
            return link
    except Exception as e:
        pass
    return None

def data_processing_3lvl(working_links_1lvl, working_links_1lv2, file_output):
    with open(working_links_1lvl, 'r', encoding='utf-8') as file:
        data_dict_1lvl = json.load(file)
        refs_data = {}
        for key, url in data_dict_1lvl.items():
            last_part = url.split('/')[-1]
            refs_data[key] = last_part
    with open(working_links_1lv2, 'r', encoding='utf-8') as refs_file:
        data_dict_2lvl = json.load(refs_file)
    print(data_dict_2lvl)
    print(refs_data)
    filtered_links = {}

    for link_name, link_url in data_dict_2lvl.items():
        for name, value in refs_data.items():
            if not 'brand' in link_url and (value not in link_url) and not has_size_or_sm_pattern(link_url, value):
                new_link_name = f"{link_name} {name}"
                new_link_url = f"{link_url}/{value}"
                filtered_links[new_link_name] = new_link_url

    links_to_check = list(filtered_links.values())
    link_names = list(filtered_links.keys())

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        driver_list = [webdriver.Chrome() for _ in range(5)]
        working_links = {}
        processed_links = 0
        good_links = 0
        futures = []

        for link, name in zip(links_to_check, link_names):
            future = executor.submit(check_link_availability, driver_list[processed_links % 5], link)
            futures.append((name, link, future))
        for name, link, future in futures:
            try:
                result = future.result()
                if result:
                    good_links += 1
                    working_links[name] = link
                processed_links += 1
                progress_percent = (processed_links / len(links_to_check)) * 100
                print(f"Прогресс: {progress_percent:.2f}% ({processed_links}/{len(links_to_check)})")
                print(f"Всего рабочих ссылок {good_links} ")
            except Exception as e:
                print(f"An error occurred: {e}")

        for driver in driver_list:
            driver.quit()

    with open(file_output, 'w', encoding='utf-8') as json_file:
        json.dump(working_links, json_file, ensure_ascii=False, indent=4)
    print(f"Третий уровень ссылок успешно сохранен в {file_output}")
