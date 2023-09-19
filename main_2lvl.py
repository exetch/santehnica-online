import json
import re
import concurrent.futures
from itertools import permutations
from selenium import webdriver
import time


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
    url = f"https://santehnika-online.ru/dushevye_ograzhdeniya/dushevye_poddony/{first_key}/{second_key}/"
    try:
        driver.get(url)
        time.sleep(2)
        if driver.title != "404 Not Found":
            print(f"Рабочая ссылка {url}")
            return combination, url
    except Exception as e:
        pass
    return None

def data_processing_2lvl(file_input, file_output):
    with open(file_input, 'r', encoding='utf-8') as file:
        data_dict = json.load(file)

    values_list = [link.split("/")[-1] for link in data_dict.values()]
    permutations_list = list(permutations(values_list, 2))
    filtered_permutations = [
        combo for combo in permutations_list if
        not combo[0].startswith('brand') and not both_values_are_sizes(combo)]

    combined_combinations = []

    for combo in filtered_permutations:
        matching_keys = [key for key, value in data_dict.items() if
                         value.endswith(combo[0]) or value.endswith(combo[1])]
        combo_name = ' '.join(matching_keys)
        combined_combinations.append((combo_name, combo))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        driver_list = [webdriver.Chrome() for _ in range(5)]
        working_links = {}
        processed_combinations = 0
        good_links = 0
        processed_links = 0
        futures = []
        for combination in combined_combinations:
            future = executor.submit(check_link_availability, driver_list[processed_combinations % 5], combination[1])
            futures.append((combination, future))

        for combination, future in futures:
            try:
                result = future.result()
                if result:
                    good_links += 1
                    working_links[combination[0]] = combination[1]
                processed_links += 1
                progress_percent = (processed_combinations / len(filtered_permutations)) * 100
                print(f"Прогресс: {progress_percent:.2f}% ({processed_combinations}/{len(filtered_permutations)})")
                print(f"Всего рабочих ссылок {good_links} ")
            except Exception as e:
                print(f"An error occurred: {e}")

        for driver in driver_list:
            driver.quit()

    new_working_links = {}
    for key, value_list in working_links.items():
        url = f"https://santehnika-online.ru/dushevye_ograzhdeniya/dushevye_poddony/{value_list[0]}/{value_list[1]}"
        new_working_links[key] = url

    with open(file_output, 'w', encoding='utf-8') as json_file:
        json.dump(new_working_links, json_file, ensure_ascii=False, indent=4)
    print(f"Второй уровень ссылок успешно сохранен в {file_output}")