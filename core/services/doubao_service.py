import os
import time
import traceback
from typing import Dict, Any

from ..config import Config

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    pass

class DoubaoProvider:
    @staticmethod
    def login(driver_path: str) -> Dict[str, Any]:
        os.makedirs(Config.DOUBAO_USER_DATA_DIR, exist_ok=True)
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={os.path.abspath(Config.DOUBAO_USER_DATA_DIR)}")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_argument("--start-maximized")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        service = webdriver.ChromeService(executable_path=driver_path)
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get("https://www.doubao.com/chat/")
            while True:
                try:
                    _ = driver.window_handles
                    time.sleep(1)
                except WebDriverException:
                    break
        except Exception as e:
            return {"success": False, "error": f"启动浏览器或打开豆包网站失败: {type(e).__name__} - {e}"}
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        return {"success": True}

    @staticmethod
    def get_content(driver_path: str, prompt_text: str) -> Dict[str, Any]:
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={os.path.abspath(Config.DOUBAO_USER_DATA_DIR)}")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        service = webdriver.ChromeService(executable_path=driver_path)
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get("https://www.doubao.com/chat/")
            wait = WebDriverWait(driver, 180)

            textarea = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'textarea[data-testid="chat_input_input"]')))
            num_messages_before = len(driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="receive_message"]'))

            textarea.clear()
            time.sleep(0.2)

            lines = prompt_text.split('\n')
            for i, line in enumerate(lines):
                textarea.send_keys(line)
                if i < len(lines) - 1:
                    ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()

            send_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="chat_input_send_button"]')))
            send_button.click()

            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, 'div[data-testid="receive_message"]')) > num_messages_before)

            try:
                use_dialog_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//div[text()='改用对话直接回答']")))
                print("检测到 AI 写作助手，已点击'改用对话直接回答'。")
                use_dialog_button.click()
                time.sleep(1)
            except TimeoutException:
                pass

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="receive_message"]:last-of-type button[data-testid="message_action_regenerate"]')))
            time.sleep(0.5)

            content_element = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="receive_message"]')[-1].find_element(By.CSS_SELECTOR, 'div[data-testid="message_text_content"]')

            return {"success": True, "text": content_element.text}
        except TimeoutException:
            return {"success": False, "error": "操作超时。可能原因：\n1. 豆包网页响应过慢。\n2. 登录状态失效，请先点击“登录豆包”按钮。\n3. 网络问题。"}
        except Exception as e:
            return {"success": False, "error": f"Selenium 操作失败: {type(e).__name__} - {e}\n{traceback.format_exc()}"}
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass