import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
LAST_NAME = os.getenv("LAST_NAME")
USER_ID = os.getenv("USER_ID")
COMMUNITY_ID = os.getenv("COMMUNITY_ID")
WORKER_ID = os.getenv("WORKER_ID")
PIN = os.getenv("PIN")
PASSWORD = os.getenv("PASSWORD")

print(LAST_NAME)
print(USER_ID)
print(COMMUNITY_ID)
print(WORKER_ID)
print(PIN)
print(PASSWORD)


BASE_URL = "https://brandcentral.verizonwireless.com/signin"
ENTERPRISE_LOGIN_URL = "https://ilogin.verizon.com/ngauth/verifyusercontroller?method=validateuser"

def login_to_verizon():
    # Set up Selenium WebDriver (Visible Browser)
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Open browser in maximized mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    try:
        # Perform login steps
        print(f"Navigating to {BASE_URL}...")
        driver.get(BASE_URL)
        time.sleep(3)

        print("Waiting for 'Verizon Employees' button...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='bc-root']/main/div[2]/div[1]/button"))
        )
        employee_button = driver.find_element(By.XPATH, "//*[@id='bc-root']/main/div[2]/div[1]/button")
        print("Clicking 'Verizon Employees' button...")
        employee_button.click()
        time.sleep(3)

        print("Entering Last Name and User ID...")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "lastname")))
        driver.find_element(By.ID, "lastname").send_keys(LAST_NAME)
        driver.find_element(By.ID, "user").send_keys(USER_ID)
        driver.find_element(By.ID, "intlcontinue").click()
        time.sleep(3)

        print("Waiting for the 'I Agree' button in the popup...")
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='btnOk']")))
        i_agree_button = driver.find_element(By.XPATH, "//*[@id='btnOk']")
        print("Clicking 'I Agree'...")
        i_agree_button.click()
        time.sleep(3)

        print("Entering Community ID, Worker ID, and PIN...")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@id='userCommunityId']")))
        driver.find_element(By.XPATH, "//*[@id='userCommunityId']").send_keys(COMMUNITY_ID)
        driver.find_element(By.XPATH, "//*[@id='nativeWorkerNumber']").send_keys(WORKER_ID)
        driver.find_element(By.XPATH, "//*[@id='pin']").send_keys(PIN)
        driver.find_element(By.XPATH, "//*[@id='continue']").click()
        time.sleep(3)

        print("Entering Password and logging in...")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "phrase")))
        driver.find_element(By.ID, "phrase").send_keys(PASSWORD)
        driver.find_element(By.ID, "LoginBtn").click()
        time.sleep(5)

        current_url = driver.current_url
        if "home" in current_url or "dashboard" in current_url:
            print("Login successful! Navigating to home page...")
            print(f"Current page: {current_url}")
        else:
            print("Login failed. Current page:", current_url)
            driver.quit()
            return None

        return driver  # Return the authenticated driver instance

    except Exception as e:
        print("Error during login:", e)
        driver.quit()
        return None

if __name__ == "__main__":
    login_to_verizon()