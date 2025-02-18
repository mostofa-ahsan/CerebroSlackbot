import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load credentials from .env
load_dotenv()
LAST_NAME = os.getenv("LAST_NAME")
USER_ID = os.getenv("USER_ID")
COMMUNITY_ID = os.getenv("COMMUNITY_ID")
WORKER_ID = os.getenv("WORKER_ID")
PIN = os.getenv("PIN")
PASSWORD = os.getenv("PASSWORD")

BASE_URL = "https://brandcentral.verizonwireless.com/signin"
ENTERPRISE_LOGIN_URL = "https://ilogin.verizon.com/ngauth/verifyusercontroller?method=validateuser"


def login_to_verizon_with_playwright(playwright):
    """Authenticate to Verizon using Playwright and return the authenticated page."""
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    try:
        # Step 1: Navigate to login page
        print(f"Navigating to {BASE_URL}...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # Step 2: Click "Verizon Employees" button
        print("Clicking 'Verizon Employees' button...")
        page.locator("//*[@id='bc-root']/main/div[2]/div[1]/button").click()
        page.wait_for_load_state("networkidle")
        time.sleep(3)


        # Step 3: Enter User Name and Password
        print("Entering USER Name and Pass..")
        page.fill("#idToken1", USER_ID)
        page.fill("#idToken2", PASSWORD)
        page.click("#loginButton_0")
        time.sleep(3)

        # # Step 3: Enter Last Name and User ID
        # print("Entering Last Name and User ID...")
        # page.fill("#lastname", LAST_NAME)
        # page.fill("#user", USER_ID)
        # page.click("#intlcontinue")
        # time.sleep(3)

        # # Step 4: Handle the popup and click "I Agree"
        # print("Clicking 'I Agree'...")
        # page.locator("//*[@id='btnOk']").click()
        # time.sleep(3)

        # # Step 5: Enter Community ID, Worker ID, and PIN on the new page
        # print("Waiting for the new page and entering credentials...")
        # page.wait_for_url(ENTERPRISE_LOGIN_URL)
        # page.fill("//*[@id='userCommunityId']", COMMUNITY_ID)
        # page.fill("//*[@id='nativeWorkerNumber']", WORKER_ID)
        # page.fill("//*[@id='pin']", PIN)
        # page.click("//*[@id='continue']")
        # time.sleep(3)

        # # Step 6: Enter Password
        # print("Entering Password...")
        # page.fill("#phrase", PASSWORD)
        # page.click("#LoginBtn")
        # time.sleep(5)

        # Check for successful login
        # if "brandcentral" not in page.url:
        #     print("Login failed. Check your credentials.")
        #     context.close()
        #     return None

        # print(f"Successfully logged in. Current URL: {page.url}")
        return context, page

    except Exception as e:
        print(f"Error during login: {e}")
        context.close()
        return None


if __name__ == "__main__":
    with sync_playwright() as playwright:
        login_to_verizon_with_playwright(playwright)
