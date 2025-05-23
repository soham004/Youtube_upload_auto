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

"""
TODO:
- Add a config file to set the thumbnail path
- Make it go through all the videos in current folder
- Delete the video after upload
"""

try:
    with open("config.json", "r") as f:
        config = json.load(f)
    thumbnail_file_path = config.get("thumbnail_image_filename", None)
    if thumbnail_file_path == "":
        thumbnail_file_path = None
    description = config.get("video_description", "")
    if description == "":
        description = None
    wait_time_in_mins = int(config["wait_time_in_mins"])
    
    
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
    # Click on the file input element
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='step-badge-0']")))


def enter_description(driver:webdriver.Chrome):
    # Click on the description box
    description_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@aria-label, 'about your video')]")))
    mouse_click(driver, description_box)
    time.sleep(.5)

    ActionChains(driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
    time.sleep(.5)

    # Enter the description
    if description:
        description_box.send_keys(description)
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
    visibility_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@id="step-badge-3"]')))
    mouse_click(driver, visibility_button)
    time.sleep(.5)
    # Click on the "Unlisted" radio button
    unlisted_radio_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//tp-yt-paper-radio-button[@name='UNLISTED']/div[@id='radioContainer']")))
    mouse_click(driver, unlisted_radio_button)
    time.sleep(.5)


def save_video(driver:webdriver.Chrome):
    # Click on the "Save" button
    save_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Save"]')))
    mouse_click(driver, save_button)
    time.sleep(5)
    print("Upload completed")


def wait_for_video_publish(driver:webdriver.Chrome):
    while True:
        try:
            driver.find_element(By.XPATH, "//h1[contains(text(),'Video published')]")
            print("Video published")
            break
        except Exception as e:
            pass
        try:
            driver.find_element(By.XPATH, "//h1[contains(text(),'Video processing')]")
            print("Video processing started")
            break
        except Exception as e:
            pass
        print("Waiting for video to be published ...")
        time.sleep(5)

def execute_upload_sequence(driver:webdriver.Chrome, video_file_path_absolute:str, thumbnail_file_path_absolute:Optional[str]):
    while True:
        try:
            driver.get("https://studio.youtube.com/")
            print("Waiting 10 secs to detect login page")
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
                input("Login page opened,\nPlease login and ADD THE ACCOUNT TO CHROME \nPress enter to continue ...")
            except TimeoutException:
                print("Login page not detected, continuing ...")
            WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//ytcp-icon-button[@id='upload-icon']")))
            start_video_upload(driver, video_file_path_absolute)
            break
        except Exception as e:
            pass
    
    enter_description(driver)

    if thumbnail_file_path_absolute is not None:
        # Click on the thumbnail button
        upload_thumbnail(driver, thumbnail_file_path_absolute)
        time.sleep(1)

    mark_video_as_not_made_for_kids(driver)

    set_unlisted_visibility(driver)

    time.sleep(1)
    save_video(driver)

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

def main():

    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    profile_dir = "Default"
    
    chrome_options = [
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={profile_dir}",
    ]
    # Initialize the driver
    
    thumbnail_file_path_absolute = None

    if thumbnail_file_path is not None:
        thumbnail_file_path_absolute = os.path.abspath(thumbnail_file_path)
        if not os.path.exists(thumbnail_file_path_absolute):
            print(f"Thumbnail file not found: {thumbnail_file_path_absolute}")
            thumbnail_file_path_absolute = None

    while True:
        wait_for_input(wait_time_in_mins * 60)
        video_files = [f for f in os.listdir(os.getcwd()) if (f.endswith(('.mp4', '.avi', '.mov', '.mkv','.mpg','.wmv')) and not is_file_open(f))]
        if not video_files:
            print("No video files found in the current folder.")
            continue
        else:
            print(f"Found {len(video_files)} video files in the current folder.")
            for video_file in video_files:
                print(f"Video file: {video_file}")
        driver = Driver(uc=True, headless=False, chromium_arg=chrome_options)
        driver.maximize_window()
        if not video_files:
            print("No video files found in the current folder.")
            sys.exit(1)
        
        for video_file in video_files:
            upload_file = os.path.abspath(video_file)
            try:
                execute_upload_sequence(driver, upload_file, thumbnail_file_path_absolute)
                print(f"Video file {video_file} uploaded successfully.")
                os.remove(upload_file)
                print(f"Video file {video_file} deleted successfully.")
            except Exception as e:
                traceback.print_exc()
        driver.quit()
    

if __name__ == "__main__":
    main()