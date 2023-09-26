from utils_1lvl import get_1lvl_links
from utils_2lvl import get_more_components, data_processing_2lvl_parallel, data_processing_3lvl_parallel, \
    data_processing_1lvl_with_new_components
import json
import time
from to_exel import save_to_excel


def count_elements_in_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        return len(data)
    except FileNotFoundError:
        return 0


URLS = ["https://santehnika-online.ru/dushevye_ograzhdeniya/dushevye_kabiny/", 'https://santehnika-online.ru/unitazy/']


if __name__ == "__main__":
    for URL in URLS:
        working_directory = URL.rstrip('/').split('/')[-1]

        WORKING_LINKS_1LVL = f'working_links_{working_directory}_1lvl.json'
        WORKING_LINKS_2LVL = f'working_links_{working_directory}_2lvl.json'
        WORKING_LINKS_3LVL = f'working_links_{working_directory}_3lvl.json'
        EXCEL_FILE = f'combined_links_{working_directory}.xlsx'
        start_time = time.time()

        one_lvl_links = get_1lvl_links(WORKING_LINKS_1LVL, URL)
        with open(WORKING_LINKS_1LVL, 'w', encoding='utf-8') as new_json_file:
            json.dump(one_lvl_links, new_json_file, ensure_ascii=False, indent=4)
        print(f"Первый уровень ссылок успешно сохранен в {WORKING_LINKS_1LVL}")

        # Получаем дополнительные компоненты для создания ссылок
        updated_values_set, new_unique = get_more_components(WORKING_LINKS_1LVL)

        # Проверяем нет ли среди новых компонентов, случайно, рабочей ссылки первого уровня
        data_processing_1lvl_with_new_components(WORKING_LINKS_1LVL, URL, new_unique)

        # Получаем ссылки второго уровня
        data_processing_2lvl_parallel(updated_values_set, WORKING_LINKS_2LVL, URL, 15)

        # Получаем ссылки третьего уровня
        data_processing_3lvl_parallel(updated_values_set, WORKING_LINKS_2LVL, WORKING_LINKS_3LVL, 15)

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
