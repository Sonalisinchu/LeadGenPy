import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Suppress webdriver_manager logs to prevent terminal spam
os.environ['WDM_LOG'] = '0'
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('WDM').setLevel(logging.ERROR)

def __initialize():
    chrome_options = webdriver.ChromeOptions()
    mode_input = input("<== SELENIUM: ==>\n1 - Launch headless Mode\n2 - Development Mode (Browser Mode)\nEnter the value : ")
    mode = int(mode_input) if mode_input.strip().isdigit() else 2
    
    if mode == 1:
        chrome_options.add_argument("--headless=new")
    
    prefs = {'profile.default_content_setting_values': {'cookies': 2, 'images': 2,
                                                        'plugins': 2, 'popups': 2, 'geolocation': 2,
                                                        'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2,
                                                        'mouselock': 2, 'mixed_script': 2, 'media_stream': 2,
                                                        'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2,
                                                        'ppapi_broker': 2, 'automatic_downloads': 2, 'midi_sysex': 2,
                                                        'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2,
                                                        'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2,
                                                        'durable_storage': 2}}
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option('prefs', prefs)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    
    # Supress annoying Chrome diagnostic logs in terminal
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    print("[LOG] - INITIALIZING SELENIUM DRIVER (Please wait...)")
    
    try:
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"[WARNING] - webdriver_manager failed (Network issue?): {e}")
        print("[LOG] - Falling back to local chromedriver in assets folder...")
        service = Service('../assets/chromedriver.exe')
        return webdriver.Chrome(service=service, options=chrome_options)

driver = __initialize()