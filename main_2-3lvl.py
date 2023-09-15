import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
import xlsxwriter


def extract_tuples(data):
    unique_tuples = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'title':
                title = value
            elif key == 'link':
                link = f"https://santehnika-online.ru{value}" if value.startswith('/') else value
        if 'title' in locals() and 'link' in locals():
            unique_tuples.add((title, link))
        for key, value in data.items():
            unique_tuples.update(extract_tuples(value))
    elif isinstance(data, list):
        for item in data:
            unique_tuples.update(extract_tuples(item))
    return unique_tuples


def get_links_data(links):
    data = []
    driver = webdriver.Chrome()
    driver.maximize_window()
    for title, link in links:
        driver.get(link)
        elements = driver.find_elements(By.CSS_SELECTOR, 'a.nGNQa6w4jpFIwgnG03bq.e5iBLIpq0DMp8E7lcAKa')
        for element in elements:
            title = element.get_attribute('title')
            href = element.get_attribute('href')
            data.append({'title': title, 'href': href})
    driver.quit()
    return data


if __name__ == "__main__":
    start_time = time.time()
    with open('popular_categories_vanny.json', 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    workbook = xlsxwriter.Workbook('popular_categories_vanny.xlsx')
    unique_tuples = extract_tuples(data)
    print(len(unique_tuples))
    worksheet_unique = workbook.add_worksheet('1_lvl')
    row = 0
    col = 0
    for item in unique_tuples:
        worksheet_unique.write(row, col, item[0])
        worksheet_unique.write(row, col + 1, item[1])
        row += 1
    count_total = len(unique_tuples)
    links_data_lvl1 = get_links_data(unique_tuples)
    worksheet_lvl1 = workbook.add_worksheet('2_lvl')
    row = 0
    col = 0
    for item in links_data_lvl1:
        worksheet_lvl1.write(row, col, item['title'])
        worksheet_lvl1.write(row, col + 1, item['href'])
        row += 1
    links_data_lvl2 = get_links_data([(item['title'], item['href']) for item in links_data_lvl1])
    worksheet_lvl2 = workbook.add_worksheet('3_lvl')
    row = 0
    col = 0
    for item in links_data_lvl2:
        worksheet_lvl2.write(row, col, item['title'])
        worksheet_lvl2.write(row, col + 1, item['href'])
        row += 1
    workbook.close()
    print("Данные успешно сохранены в exel'")
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Время выполнения скрипта: {execution_time} секунд")
