# Contains helper functions for phases 3 and 4

import config as _

from selenium.webdriver.common.by import By


def extract_part_links_basic(driver):
    """Extract all part links on the page (Interior, Exterior and Performance)"""

    links = []

    items = driver.find_elements(By.CLASS_NAME, 'productListColumn')
    for item in items:
        a = item.find_element(By.TAG_NAME, 'a')
        links.append(a.get_attribute('href'))
        
    return links


def extract_part_links(driver):
    """Extract all part links on the page"""

    links = []

    items = driver.find_elements(By.CLASS_NAME, 'assemblyCardLink')
    for item in items:
        links.append(item.get_attribute('href'))

    return links


def extract_final_part_links(driver):
    """Extract all final part links on the page"""

    links = []

    items = driver.find_elements(By.CLASS_NAME, 'btn-tertiary')
    for item in items:
        links.append(item.get_attribute('href'))

    return links