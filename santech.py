from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

import time
import random

if __name__ == "__main__":
    # Инициализация драйвера браузера
    driver = webdriver.Chrome()  # Укажите путь к вашему драйверу браузера
    driver.maximize_window()

    # Открываем страницу сайта
    url = "https://santehnika-online.ru/dushevye_ograzhdeniya/dushevye_poddony/"
    driver.get(url)
    elements = driver.find_elements(By.CSS_SELECTOR, ".t_siYekLql2C238n1Gtd.text--md.text--bold")

    action = ActionChains(driver)

    for element in elements:

        action.click(element).perform()
        selectors =
    page_source = driver.page_source

    # Закрываем браузер
    driver.quit()