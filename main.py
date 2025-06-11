import pyperclip
from seleniumbase import Driver
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from typing import Optional
import sys
import time
import json
import os
import errno
import traceback
import msvcrt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='runtime.log', filemode='a')

try:
    with open("config.json", "r") as f:
        config = json.load(f)
    thumbnail_file_path = config.get("thumbnail_image_filename", None)
    if thumbnail_file_path == "":
        thumbnail_file_path = None
    description_content_filename = config.get("description_content_filename", "")
    if description_content_filename == "":
        description_content_filename = None
    wait_time_in_mins = int(config["wait_time_in_mins"])
    video_has_altered_content = config.get("video_has_altered_content", None)
    turn_monetization_on = config.get("turn_monetization_on", True)
    
    
except FileNotFoundError:
    print("Config file not found. Please create a config.json file.")
    sys.exit(1)

def is_file_open(file_path):
    try:
        with open(file_path, 'r+') as file:
            return False  # File is not open by another program
    except IOError as e:
        if e.errno == errno.EACCES or e.errno == errno.EBUSY:
            return True
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return True

def mouse_click(driver:webdriver.Chrome, element):
    # Move to the element and click
    ActionChains(driver).move_to_element(element).click().perform()
    time.sleep(.5)


def start_video_upload(driver:webdriver.Chrome,video_file_path_absolute:str):
    # Click on the upload button
    upload_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//ytcp-icon-button[@id='upload-icon']")))
    mouse_click(driver, upload_button)

    time.sleep(.5)
    file_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
    file_input.send_keys(video_file_path_absolute)
    logging.info(f"Video file {video_file_path_absolute} path sent for upload.")
    # Click on the file input element
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//button[@id='step-badge-0']")))
    logging.info("step-badge-0 found")
    time.sleep(2)
    try:
        driver.find_element(By.XPATH, '//div[contains(text(),"Daily upload limit reached")]')
        print("Daily upload limit reached. Please try again later.")
        logging.error("Daily upload limit reached. Please try again later.")
        driver.quit()
    except Exception as e:
        print("Video upload started successfully.")
        logging.info("Video upload started successfully.")
        logging.info(traceback.format_exc())


def enter_description(driver:webdriver.Chrome):

    if description_content_filename is None:
        print("Description content filename is not specified in config.json")
        print("Not making any changes")
        return

    # Click on the description box
    description_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[contains(@aria-label, 'about your video')]")))
    mouse_click(driver, description_box)
    logging.info("Description box clicked, ready to enter description.")
    time.sleep(.5)

    try:
        if description_content_filename is None:
            raise FileNotFoundError("Description content filename is not specified in config.json")
        description_file = open(description_content_filename, mode="r", encoding="utf-8")
        description = description_file.read()
        description_file.close()
        ActionChains(driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
        time.sleep(.5)
    except FileNotFoundError:
        print(f"Description file not found: {description_content_filename}")
        print("Please create a description file with the name specified in config.json")
        print("No making any changes")
        description = None
    # Enter the description
    if description:
        pyperclip.copy(description)  # Copy the description to clipboard
        description_box.send_keys(Keys.CONTROL + 'v') # Paste the description
        time.sleep(.5)



def upload_thumbnail(driver:webdriver.Chrome, thumbnail_file_path_absolute:str):
    ActionChains(driver).scroll_to_element(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(),'Playlists')]")))).perform()
    thumbnail_path_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='file' and contains(@class,'ytcp-thumbnail-uploader')]")))
    thumbnail_path_input.send_keys(thumbnail_file_path_absolute)
    time.sleep(.5)


def mark_video_as_not_made_for_kids(driver:webdriver.Chrome):
    # Click on the "Not made for kids" radio button
    not_made_for_kids_radio_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//tp-yt-paper-radio-button[@name='VIDEO_MADE_FOR_KIDS_NOT_MFK']/div[@id='radioContainer']")))
    ActionChains(driver).scroll_to_element(not_made_for_kids_radio_button).perform()
    mouse_click(driver, not_made_for_kids_radio_button)
    time.sleep(.5)

def set_unlisted_visibility(driver:webdriver.Chrome):
    # Click on the "Unlisted" radio button
    unlisted_radio_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//tp-yt-paper-radio-button[@name='UNLISTED']/div[@id='radioContainer']")))
    ActionChains(driver).scroll_to_element(unlisted_radio_button).perform()
    mouse_click(driver, unlisted_radio_button)
    time.sleep(.5)


def save_video(driver:webdriver.Chrome):

    # Click on the "Save" button
    save_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Save"]')))
    mouse_click(driver, save_button)
    time.sleep(5)
    try:
        print("Looking for still checking popup")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//h1[contains(text(),"still checking")]')))
        print("Still checking popup found, clicking publish")
        publish_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Publish"]')))
        mouse_click(driver, publish_button)
    except TimeoutException: 
        print("No still checking popup found, continuing...")


def wait_for_video_publish(driver:webdriver.Chrome):
    print_once = True
    i=0
    while True:
        time.sleep(5)
        try:
            driver.find_element(By.XPATH, "//h1[contains(text(),'uploading') or contains(text(),'Uploading')]")
            print(f"\rVideo still uploading (check no. {i})", end="\r")
            i += 1
        except Exception as e:
            if print_once:
                print("\nVideo upload completed")
                print_once = False
            break

def go_to_next_upload_card(driver:webdriver.Chrome)-> bool:
    try:
        next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Next"]')))
        mouse_click(driver, next_button)
        time.sleep(.5)
        return True
    except TimeoutException:
        return False

def set_monetization(driver:webdriver.Chrome):
    monetization_drop_down = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//ytcp-form-input-container[@label="Monetization"]//div[@id="child-input"]')))
    mouse_click(driver, monetization_drop_down)
    time.sleep(.5)
    if turn_monetization_on:
        monetization_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-radio-button[@id="radio-on"]/div[@id="radioContainer"]')))
    else:
        monetization_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-radio-button[@id="radio-off"]/div[@id="radioContainer"]')))
    mouse_click(driver, monetization_option)
    done_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Done"]')))
    ActionChains(driver).scroll_to_element(done_button).perform()
    mouse_click(driver, done_button)

    go_to_next_upload_card(driver)
    if turn_monetization_on:
        set_ad_suitability(driver)
    

def set_ad_suitability(driver:webdriver.Chrome):
    none_of_the_above_checkbox = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="None of the above"]')))
    ActionChains(driver).scroll_to_element(none_of_the_above_checkbox).perform()
    mouse_click(driver, none_of_the_above_checkbox)

    submit_rating_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Submit rating"]')))
    ActionChains(driver).scroll_to_element(submit_rating_button).perform()
    mouse_click(driver, submit_rating_button)
    time.sleep(.5)
    go_to_next_upload_card(driver)


def execute_upload_sequence(driver:webdriver.Chrome, video_file_path_absolute:str, thumbnail_file_path_absolute:Optional[str], full_sequence:bool=False):
    while True:
        driver.get("https://studio.youtube.com/")
        try:
            WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//ytcp-icon-button[@id='upload-icon']")))
            start_video_upload(driver, video_file_path_absolute)
            break
        except Exception as e:
            print("Upload button not found. Retrying in 5 seconds...")
            time.sleep(5)
    
    if full_sequence:
        enter_description(driver)

    if thumbnail_file_path_absolute is not None:
        # Click on the thumbnail button
        upload_thumbnail(driver, thumbnail_file_path_absolute)
        time.sleep(1)
    
    mark_video_as_not_made_for_kids(driver)

    
    if video_has_altered_content is not None:
        show_more_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Show advanced settings"]')))
        ActionChains(driver).scroll_to_element(show_more_button).perform()
        show_more_button.click()
        time.sleep(1)
        if video_has_altered_content:
            altered_content_radio_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-radio-button[@name="VIDEO_HAS_ALTERED_CONTENT_YES"]')))
        else:
            altered_content_radio_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-radio-button[@name="VIDEO_HAS_ALTERED_CONTENT_NO"]')))
        ActionChains(driver).scroll_to_element(altered_content_radio_button).perform()
        mouse_click(driver, altered_content_radio_button)
        time.sleep(1)

    # press next button
    go_to_next_upload_card(driver)

    # check for monetization
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//h1[contains(text(),"Monetization")]')))
        print("Monetization step detected")
        logging.info("Monetization step detected")
        set_monetization(driver)
        logging.info("Monetization settings applied successfully.")
    except TimeoutException:
        print("Monetization step not detected, skipping...")
        logging.info("Monetization step not detected, skipping...")

    while go_to_next_upload_card(driver):
        print("Next upload card detected, continuing to next step...")
        time.sleep(.5)

    if full_sequence:
        set_unlisted_visibility(driver)

    time.sleep(1)
    save_video(driver)
    time.sleep(20)
    wait_for_video_publish(driver)

def wait_for_input(timeout_in_seconds):
    """Waits for Enter key press with a timeout while displaying a countdown (Windows version)."""
    start_time = time.time()
    while True:
        remaining_time = timeout_in_seconds - (time.time() - start_time)
        if remaining_time <= 0:
            print("\nTime's up!.")
            return False  # Timeout reached
        mins, secs = divmod(remaining_time, 60)
        sys.stdout.write("\rTime left for next check: {:02d}:{:02d}. Press Enter to check for files now... ".format(int(mins), int(secs)) )
        sys.stdout.flush()

        # Check if a key was pressed
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':  # Enter key is detected
                print("\nUser pressed Enter!")
                return True  # Input received

        time.sleep(0.1)  # Reduce CPU usage

def setup_upload_settings_on_youtube(driver:webdriver.Chrome) -> bool:
    for i in range(3):
        driver.get("https://studio.youtube.com/")
        print("Waiting 10 secs to detect login page")
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
            input("Login page opened\nPlease login and ADD THE ACCOUNT TO CHROME \nPress enter to continue ...")
        except TimeoutException:
            print("Login page not detected, continuing ...")

        try:
            settings_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-icon-item[@id="settings-item"]')))
            mouse_click(driver, settings_button)
        except TimeoutException:
            print("Settings button not found. Please ensure you are logged in to YouTube Studio.")
            return False
        
        try:
            upload_defaults_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//span[contains(text(),"Upload defaults")]/parent::li/parent::ytcp-ve')))
            mouse_click(driver, upload_defaults_button)
            enter_description(driver)
            visibility_selection = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//ytcp-form-select[@id="privacy-select"]')))
            time.sleep(.5)
            mouse_click(driver, visibility_selection)
            unlised_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-item[@test-id="VIDEO_PRIVACY_UNLISTED"]')))
            time.sleep(.5)
            mouse_click(driver, unlised_option)
            break
        except TimeoutException:
            print("Upload defaults button not found retrying ...")
            if i == 2:
                print("Failed to find upload defaults button after 3 attempts. Exiting.")
                return False
            continue

    try:
        save_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Save"]')))
        mouse_click(driver, save_button)
        print("Upload defaults saved successfully.")
        return True
    except TimeoutException:
        print("Save button not clickable. No changes made.")
        logging.info("Save button not clickable. No changes made.")
        driver.get("https://studio.youtube.com/")
        return True

def main():
    print("Running startup sequence ...")
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    profile_dir = "Default"
    
    chrome_options = [
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={profile_dir}",
    ]
    # Initialize the driver
    driver = Driver(uc=True, headless=False, chromium_arg=chrome_options)
    driver.maximize_window()
    execute_full_sequence = not setup_upload_settings_on_youtube(driver)
    driver.quit()

    thumbnail_file_path_absolute = None

    if thumbnail_file_path is not None:
        thumbnail_file_path_absolute = os.path.abspath(thumbnail_file_path)
        if not os.path.exists(thumbnail_file_path_absolute):
            print(f"Thumbnail file not found: {thumbnail_file_path_absolute}")
            thumbnail_file_path_absolute = None

    while True:
        wait_for_input(wait_time_in_mins * 60)
        video_files = [f for f in os.listdir(os.getcwd()) if (f.endswith(('.mp4', '.avi', '.mov', '.mkv','.mpg','.wmv')) and not is_file_open(f))]
        logging.info(f"Found {video_files} video files in the current folder.")
        if not video_files:
            print("No video files found in the current folder.")
            logging.info("No video files found in the current folder.")
            continue
        else:
            print(f"Found {len(video_files)} video files in the current folder.")
            for video_file in video_files:
                print(f"Video file: {video_file}")
        try:
            driver = Driver(uc=True, headless=False, chromium_arg=chrome_options)
            driver.maximize_window()            
            for video_file in video_files:
                print("")
                print(f"Processing video file: {video_file}")
                logging.info(f"Processing video file: {video_file}")
                upload_file = os.path.abspath(video_file)
                execute_upload_sequence(driver, upload_file, thumbnail_file_path_absolute, full_sequence=execute_full_sequence)
                print(f"Video file {video_file} uploaded successfully.")
                logging.info(f"Video file {video_file} uploaded successfully.")
                os.remove(upload_file)
                print(f"Video file {video_file} deleted successfully.")
                logging.info(f"Video file {video_file} deleted successfully.")
            driver.quit()
        except Exception as e:
            print(f"An error occurred")
            logging.error(f"An error occurred: {e}")
            logging.error(traceback.format_exc())
            print("Retrying with a new browser instance during next check...")
            driver.quit()
        print("All video files processed. Waiting for next check...")

if __name__ == "__main__":
    main()