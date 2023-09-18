import json
import re
from itertools import combinations
from selenium import webdriver
import time



def both_values_are_sizes(combination):
    first_value, second_value = combination
    size_pattern = r"\S{2}x\S{2}"
    is_first_value_size = re.search(size_pattern, first_value)
    is_second_value_size = re.search(size_pattern, second_value)
    return is_first_value_size and is_second_value_size


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


if __name__ == "__main__":
    with open('refs.json', 'r', encoding='utf-8') as file:
        refs_dict = json.load(file)

    values_list = list(refs_dict.values())
    combinations_list = list(combinations(values_list, 2))
    print(len(combinations_list))
    filtered_combinations = [combo for combo in combinations_list if
                             not 'brand' in combo[0] and not both_values_are_sizes(combo)]
    combined_combinations = []

    combined_combinations = []
    print(len(filtered_combinations))
    for combo in filtered_combinations:
        combo_names = [key for key, value in refs_dict.items() if
                       value in combo]
        combo_name = ' '.join(combo_names)
        combined_combinations.append((combo_name, combo))
    for combo in filtered_combinations:
        print(combo)

    driver = webdriver.Chrome()

    working_links = {}
    processed_combinations = 0
    good_links = 0
    for combination in combined_combinations:
        print(combination)
        processed_combinations += 1
        if check_link_availability(driver, combination[1]):
            good_links += 1
            working_links[combination[0]] = combination[1]
        progress_percent = (processed_combinations / len(filtered_combinations)) * 100
        print(f"Прогресс: {progress_percent:.2f}% ({processed_combinations}/{len(filtered_combinations)})")
        print(f"Всего рабочих ссылок {good_links} ")
    driver.quit()
    with open('working_links.json', 'w', encoding='utf-8') as json_file:
        json.dump(working_links, json_file, ensure_ascii=False, indent=4)