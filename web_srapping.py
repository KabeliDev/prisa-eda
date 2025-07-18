from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
import time
import os
import requests


def search_product_url(base_url, product_code):
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(base_url)

        wait = WebDriverWait(driver, 15)
        time.sleep(10)

        # Hacer clic en el ícono de búsqueda
        input_search = wait.until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="oro_website_search_search"]/input')))
        input_search.send_keys(product_code)

        # Escribir el código del producto
        button_search = wait.until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="oro_website_search_search"]/button')))
        button_search.click()

        exist_product = wait.until(EC.visibility_of_element_located((
            By.XPATH,
            f'//span[normalize-space(text())="Código {product_code}"]/../../../../..//a//img'
        )))

        time.sleep(5)
        return exist_product.get_attribute("src")

    except Exception as e:
        print("Error:", traceback.format_exc())
        return None

    finally:
        driver.quit()


def download_and_save(folder, product_code, url, local_folder):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(url)
    filename = f"{str(product_code)}.png"
    filepath = os.path.join(local_folder, filename)

    if response.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Image saved to {filepath}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")



if __name__ == "__main__":
    base_url = "https://www.prisa.cl"
    product_code = "89295"
    result = search_product_url(base_url, product_code)
    print("Resultado:", result)

    LOCAL_FOLDER = "/home/viktoria/Downloads/images"
    download_and_save(LOCAL_FOLDER, product_code, result, LOCAL_FOLDER)

    code = 12596
    result = search_product_url(base_url, code)
    download_and_save(LOCAL_FOLDER, code, result, LOCAL_FOLDER)

    code = 99840
    result = search_product_url(base_url, code)
    download_and_save(LOCAL_FOLDER, code, result, LOCAL_FOLDER)