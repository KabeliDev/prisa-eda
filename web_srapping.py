from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
import time


def search_product_url(base_url, product_code):
    options = webdriver.ChromeOptions()
    # options.add_argument("--window-size=1920,1080")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--disable-software-rasterizer")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(base_url)

        wait = WebDriverWait(driver, 15)

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
            f'//span[normalize-space(text())="Código {product_code}"]'
        )))

        time.sleep(10)
        return exist_product

    except Exception as e:
        print("Error:", traceback.format_exc())
        return None

    finally:
        driver.quit()


if __name__ == "__main__":
    base_url = "https://www.prisa.cl"
    product_code = "89295"
    result = search_product_url(base_url, product_code)
    print("Resultado:", result)