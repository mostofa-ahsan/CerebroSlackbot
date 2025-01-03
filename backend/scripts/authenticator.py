import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
LAST_NAME = os.getenv("LAST_NAME")
USER_ID = os.getenv("USER_ID")
COMMUNITY_ID = os.getenv("COMMUNITY_ID")
WORKER_ID = os.getenv("WORKER_ID")
PIN = os.getenv("PIN")
PASSWORD = os.getenv("PASSWORD")

BASE_URL = "https://brandcentral.verizonwireless.com/signin"

def login_to_verizon():
    # Set up Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    try:
        # Step 1: Navigate to login page
        driver.get(BASE_URL)
        time.sleep(3)

        # Step 2: Select "Verizon employees"
        employee_button = driver.find_element(By.XPATH, "//button[contains(text(),'Verizon Employees')]")
        employee_button.click()
        time.sleep(3)

        # Step 3: Enter Last Name and User ID
        driver.find_element(By.NAME, "LastName").send_keys(LAST_NAME)
        driver.find_element(By.NAME, "UserID").send_keys(USER_ID)
        driver.find_element(By.XPATH, "//button[contains(text(),'Continue')]").click()
        time.sleep(3)

        # Step 4: Agree to Terms and Conditions
        driver.find_element(By.XPATH, "//button[contains(text(),'I Agree')]").click()
        time.sleep(3)

        # Step 5: Enter Community ID, Worker ID, and PIN
        driver.find_element(By.NAME, "CommunityID").send_keys(COMMUNITY_ID)
        driver.find_element(By.NAME, "WorkerID").send_keys(WORKER_ID)
        driver.find_element(By.NAME, "PIN").send_keys(PIN)
        driver.find_element(By.XPATH, "//button[contains(text(),'Continue')]").click()
        time.sleep(3)

        # Step 6: Enter Password
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(),'Login')]").click()
        time.sleep(5)

        # Confirm successful login
        current_url = driver.current_url
        if "home" in current_url:
            print("Login successful. Current page:", current_url)
        else:
            print("Login failed. Current page:", current_url)

    finally:
        driver.quit()

if __name__ == "__main__":
    login_to_verizon()
