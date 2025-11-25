from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from seleniumbase import Driver
from Addons import config


def get_cookie(config_file,
               css_query,
               cookie_name="osu_session",
               url="https://osu.ppy.sh/",
               ):
    configuration = config.load_config(config_file)

    if cookie_name in configuration:
        print(f"✅ Using saved {cookie_name} from {config_file}")
        return configuration[cookie_name]

    driver = Driver(uc=True)
    print("Driver:", driver)
    driver.uc_open_with_reconnect(url, 4) # type: ignore

    print("\n🔵 Please log in manually in the opened browser.")

    try:
        WebDriverWait(driver, 300).until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, css_query)
            )
        )
        print("✅ CSS_SELECTOR detected, Login complete.")
    except Exception as e:
        print("Error while logging in:", e)

    cookies = driver.get_cookies()

    cookie = None

    for c in cookies:
        if c['name'] == cookie_name:
            cookie = c['value']
            break

    driver.quit()

    if cookie:
        print(f"\n✅ {cookie_name} cookie found. Saving to config...")
        print(f"{cookie_name}:", cookie)
        configuration[cookie_name] = cookie

        config.save_config(configuration, config_file)
        return cookie
    else:
        print(f"\n❌ {cookie_name} cookie NOT found.")
        return None