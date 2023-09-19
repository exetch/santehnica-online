import json
import concurrent.futures
from selenium import webdriver


def check_link_availability(driver, link):
    try:
        driver.get(link)
        if driver.title != "404 Not Found":
            print(f"Рабочая ссылка {link}")
            return link
    except Exception as e:
        pass
    return None

if __name__ == "__main__":
    with open('working_links_3lvl.json', 'r', encoding='cp1251') as file:
        working_links_to_check = json.load(file)
    print(working_links_to_check)

    links_to_check = list(working_links_to_check.values())
    link_names = list(working_links_to_check.keys())

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        driver_list = [webdriver.Chrome() for _ in range(5)]  # 5 браузеров одновременно
        working_links = {}
        processed_links = 0
        good_links = 0
        futures = []

        for link, name in zip(links_to_check, link_names):
            future = executor.submit(check_link_availability, driver_list[processed_links % 5], link)
            futures.append((name, link, future))
            processed_links += 1

        for name, link, future in futures:
            try:
                result = future.result()
                if result:
                    good_links += 1
                    working_links[name] = link
                progress_percent = (processed_links / len(links_to_check)) * 100
                print(f"Прогресс: {progress_percent:.2f}% ({processed_links}/{len(links_to_check)})")
                print(f"Всего рабочих ссылок {good_links} ")
            except Exception as e:
                print(f"Ошибка: {e}")

        for driver in driver_list:
            driver.quit()
    print(f'осталось {len(working_links)} из {len(working_links_to_check)}')
