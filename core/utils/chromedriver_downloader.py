import os
import sys
import zipfile
import platform
import requests
import subprocess
from PyQt5.QtWidgets import QMessageBox

class ChromedriverDownloader:
    def __init__(self, status_callback=print, error_callback=None):
        self.status_callback = status_callback
        self.error_callback = error_callback if error_callback else self._default_error_handler
        self.driver_filename = self._get_driver_filename()
        self.versions_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"

    def _default_error_handler(self, message):
        print(f"ERROR: {message}")
        QMessageBox.critical(None, "ChromeDriver 错误", message)

    def _get_driver_filename(self):
        return "chromedriver.exe" if sys.platform == "win32" else "chromedriver"

    def _get_chrome_version(self):
        os_name = platform.system()
        try:
            if os_name == "Windows":
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                return version
            elif os_name == "Darwin":
                process = subprocess.run(
                    ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                    capture_output=True, text=True, check=True
                )
                return process.stdout.strip().split(" ")[-1]
            elif os_name == "Linux":
                process = subprocess.run(
                    ["google-chrome", "--version"],
                    capture_output=True, text=True, check=True
                )
                return process.stdout.strip().split(" ")[-1]
        except Exception as e:
            self.status_callback(f"无法自动找到 Chrome 版本: {e}")
            return None
        return None

    def ensure_chromedriver(self):
        driver_path = self.driver_filename
        if os.path.exists(driver_path):
            return True, "ChromeDriver 已存在。"

        self.status_callback("ChromeDriver 未找到，正在尝试自动下载...")
        chrome_version = self._get_chrome_version()
        if not chrome_version:
            msg = "无法自动找到 Chrome 版本。请确保已安装 Google Chrome 浏览器。"
            self.error_callback(msg)
            return False, msg

        chrome_major_version = chrome_version.split('.')[0]
        self.status_callback(f"检测到 Chrome 主版本号为: {chrome_major_version}")

        try:
            self.status_callback("正在从官方源获取版本信息...")
            response = requests.get(self.versions_url, timeout=15)
            response.raise_for_status()
            versions_data = response.json()

            best_match = next(
                (v for v in reversed(versions_data['versions']) if v['version'].startswith(chrome_major_version)),
                None
            )

            if not best_match:
                msg = f"无法为您的 Chrome 版本 ({chrome_major_version}) 找到匹配的 chromedriver。"
                self.error_callback(msg)
                return False, msg

            self.status_callback(f"找到匹配的 chromedriver 版本: {best_match['version']}")

            os_name = platform.system()
            platform_map = {"Windows": "win64", "Darwin": "mac-x64", "Linux": "linux64"}
            plat = platform_map.get(os_name)

            if not plat:
                msg = f"不支持的操作系统: {os_name}"
                self.error_callback(msg)
                return False, msg

            driver_info = next((d for d in best_match['downloads']['chromedriver'] if d['platform'] == plat), None)

            if not driver_info:
                msg = f"无法找到适用于 {plat} 的 chromedriver 下载链接。"
                self.error_callback(msg)
                return False, msg

            download_url = driver_info['url']
            zip_filename = "chromedriver.zip"

            self.status_callback(f"开始下载: {os.path.basename(download_url)}...")
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()

            with open(zip_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.status_callback("下载完成，正在解压...")
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                driver_path_in_zip = next(
                    (name for name in zip_ref.namelist() if name.endswith(self.driver_filename)),
                    None
                )
                if not driver_path_in_zip:
                    raise FileNotFoundError("无法在下载的压缩包中找到 chromedriver。")

                with zip_ref.open(driver_path_in_zip) as source_file:
                    with open(self.driver_filename, "wb") as target_file:
                        target_file.write(source_file.read())

            if sys.platform != "win32":
                os.chmod(self.driver_filename, 0o755)

            os.remove(zip_filename)
            self.status_callback("Chromedriver 已成功准备就绪。")
            return True, f"{self.driver_filename} 已成功准备就绪。"

        except Exception as e:
            msg = f"下载或解压过程中发生错误: {e}"
            self.error_callback(msg)
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
            return False, msg