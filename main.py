import config as _

import time
import os
import json
from json import JSONDecodeError

import cloudscraper
import pandas
from loguru import logger
from selenium.webdriver.common.by import By

from utils import extract_part_links_basic, extract_part_links, extract_final_part_links
from proxy import get_chromedriver


EXTRACT_NEW = False  # This variable decides whether to run everything from scratch or use previously scraped information from JSON files. True means run from scratch.

scraper = cloudscraper.create_scraper()


def main():

    logger.info('Starting script!')

    if not os.path.exists('data'):
        os.mkdir('data')

    if EXTRACT_NEW:
        with open('data/visited.json', 'w') as f:
            json.dump([], f, indent=4)
        with open('data/parts.json', 'w') as f:
            json.dump([], f, indent=4)
        with open('data/links.json', 'w') as f:
            json.dump([], f, indent=4)
    
    models = phase_one(extract_new=EXTRACT_NEW)
    links = phase_two(models=models)
    driver, parts = phase_three(links=links)
    phase_four(driver=driver, parts=parts)

    driver.quit()

    logger.info('Script has run to completion!')


# HELPER FUNCTION FOR READABILITY. SAFE TO IGNORE
def get_modal_body(path = ''):
    """Path should start with /"""
    
    return {
        'pathUrl': path,
        'fitmentLevel': ''
    } 


def phase_one(extract_new = True):
    """
    Extracts all the top level links for all combinations of models, years and types
    """

    logger.info('-'*20)
    logger.info('Starting phase 1')

    # if extract_new is False: simply reads from json file and returns the previously extracted links
    if not extract_new:
        try:
            with open('data/models.json', 'r') as f:
                models = json.load(f)
            logger.info('models.json found, phase 1 completed')
            logger.info('-'*20)
            return models
        except (FileNotFoundError, JSONDecodeError):
            logger.warning('models.json NOT FOUND OR CORRUPTED, but phase 1 was executed with "extract_new = False". If this was unexpected, please terminate the script and check models.json. Otherwise, leave the script running and it will extract the top level links')

    """
    If extract_new is True: extract new links
    """

    models = {}  # All models information
    modal_link = 'https://parts.lexus.com/wm.aspx/GetInterpretForModal'  # Not to be confused with "model link"

    # Getting all model paths

    top = scraper.post(modal_link, 
                    json=get_modal_body()).json()
    for model in top['d'][:-1]:
        link = model['LinkUrl']
        ms = scraper.post(modal_link,
                            json=get_modal_body(link)).json()
        for m in ms['d']:
            name = m['SimpleString']
            link = m['LinkUrl']
            models[name] = {
                'path': link
            }    
    other = scraper.post(modal_link, 
                                json=get_modal_body(top['d'][-1]['LinkUrl'])).json()
    for model in other['d']:
        name = model['SimpleString']
        link = model['LinkUrl']
        models[name] = {
            'path': link
        }

    logger.debug('All model paths extracted (Part 1 of Phase one completed)')

    # Getting years and types for all models

    for model, info in models.items():
        models[model]['years'] = {}

        years = scraper.post(modal_link,
                                    json=get_modal_body(info['path'])).json()
        
        for year in years['d']:
            year_str = year['SimpleString']
            year_link = year['LinkUrl']

            models[model]['years'][year_str] = {
                'path': year_link
            }

        for year, year_info in models[model]['years'].items():
            models[model]['years'][year]['types'] = {}

            types = scraper.post(modal_link,
                                        json=get_modal_body(year_info['path'])).json()
            
            for type_ in types['d']:
                type_name = type_['SimpleString']
                type_link = type_['LinkUrl']
                models[model]['years'][year]['types'][type_name] = type_link

        logger.debug(f'Links for {model} extracted')

    with open('data/models.json', 'w') as f:
        json.dump(models, f, indent=4)

    logger.info('Phase 1 completed, written results to models.json')
    logger.info('-'*20)
    return models


def phase_two(models):
    """Formats the links scraped in phase one"""

    logger.info('Starting phase 2')  

    links = []

    def add_link(path, model, year, type_, category):
        path = path.replace(' ', '-')
        links.append({
            'model': model,
            'year': year,
            'type': type_,
            'category': category,
            'link': f'https://parts.lexus.com{path}'
        })

    for model_name, model_info in models.items():
        for year, year_info in model_info['years'].items():
            path = f'/Lexus_{year}_{model_name}'
            path_basic = f'/accessories/Lexus_{year}_{model_name}'
            if len(year_info['types']) == 0:
                for category in ['Interior', 
                                 'Exterior', 
                                 'Performance']:
                    add_link(f'{path_basic}/{category}.html', 
                             model_name, 
                             int(year), 
                             '',
                             'accessories - ' + category.lower().replace('-', ' '))
                    
                for category in ['Body-and-Interior',
                                 'Brakes-and-Suspension',
                                 'Electrical',
                                 'Engine',
                                 'Exhaust',
                                 'Fuel-System',
                                 'Heating-and-Air-Conditioning',
                                 'Maintenance',
                                 'Tools',
                                 'Transmission-and-Driveline',
                                 'Wheel-Components']:
                    add_link(f'{path}/{category}.html', 
                             model_name, 
                             int(year), 
                             '', 
                             category.lower().replace('-', ' '))
                    
            else:
                for type_, type_path in year_info['types'].items():
                    for category in ['Interior', 
                                     'Exterior', 
                                     'Performance']:
                        add_link(f'/accessories{type_path.split(".html")[0]}/{category}.html',
                                 model_name,
                                 int(year),
                                 type_,
                                 'accessories - ' + category.lower().replace('-', ' '))
                        
                    for category in ['Body-and-Interior',
                                 'Brakes-and-Suspension',
                                 'Electrical',
                                 'Engine',
                                 'Exhaust',
                                 'Fuel-System',
                                 'Heating-and-Air-Conditioning',
                                 'Maintenance',
                                 'Tools',
                                 'Transmission-and-Driveline',
                                 'Wheel-Components']:
                        add_link(f'{type_path.split(".html")[0]}/{category}.html',
                                 model_name,
                                 int(year),
                                 type_,
                                 category.lower().replace('-', ' ')) 
                        
    with open('data/links.json', 'w') as f:
        json.dump(links, f, indent=4)
                        
    logger.info(f'Phase 2 completed, {len(links)} pages to visit, links saved to links.json')
    logger.info('-'*20)

    return links


def phase_three(links):
    """Extracts all the individual part links"""

    logger.info('Starting phase 3')

    fail_count = 0
    failed_links = []

    parts = []

    try:
        with open('data/parts.json', 'r') as f:
            parts = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        parts = []

    try:
        with open('data/visited.json', 'r') as f:
            backup = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        backup = []

    parts_count = len(parts)

    driver = get_chromedriver(use_proxy=True)
    
    for index, link_info in enumerate(links):
        skip = False

        link = link_info['link']

        if link in backup:
            continue

        with open('data/parts.json', 'w') as f:
            json.dump(parts, f, indent=4)

        with open('data/visited.json', 'w') as f:
            json.dump(list(set(backup)), f, indent=4)

        while True:
            try:
                if fail_count >= 10:
                    logger.error(f'Page has failed loading 10 times in a row, skipping. Link -> {link}')
                    skip = True
                    with open('data/skipped.json', 'r') as f:
                        skipped = json.load(f)
                    skipped.append(link)
                    with open('data/skipped.json', 'w') as f:
                        json.dump(skipped, f, indent=4)
                    fail_count = 0
                    break
                driver.get(link)
                driver.find_element(By.CLASS_NAME, 'business-logo')
                fail_count = 0
                break
            except Exception:
                fail_count += 1
                logger.warning(f'Page not loaded successfully, retrying. Link -> {link}')
                driver.quit()
                driver = get_chromedriver(use_proxy=True)
                continue
        
        if skip: continue

        if '/Interior.html' in link or '/Exterior.html' in link or '/Performance.html' in link:
            part_links = extract_part_links_basic(driver)
            part_links = list(set(part_links))
            parts_count += len(part_links)

            for final_part_link in part_links:
                part_info = link_info.copy()
                part_info['url'] = final_part_link
                parts.append(part_info)

            logger.debug(f'{parts_count} part links scraped (source link index: {index + 1}, total source links: {len(links)})')

        else:
            part_links = extract_part_links(driver)
            part_links = list(set(part_links))

            for part_link in part_links:
                skip = False
                part_link = part_link.split('?')[0]
                while True:
                    try:
                        if fail_count >= 10:
                            logger.error(f'Page has failed loading 10 times in a row, skipping. Link -> {part_link}')
                            skip = True
                            with open('data/skipped.json', 'r') as f:
                                skipped = json.load(f)
                            skipped.append(part_link)
                            with open('data/skipped.json', 'w') as f:
                                json.dump(skipped, f, indent=4)
                            fail_count = 0
                            break
                        driver.get(part_link)
                        driver.find_element(By.CLASS_NAME, 'business-logo')
                        fail_count = 0
                        break
                    except Exception:
                        fail_count += 1
                        logger.warning(f'Page not loaded successfully, retrying. Link -> {part_link}')
                        driver.quit()
                        driver = get_chromedriver(use_proxy=True)
                        continue

                if skip: continue

                final_part_links = extract_final_part_links(driver)
                final_part_links = list(set(final_part_links))

                parts_count += len(final_part_links)

                for final_part_link in final_part_links:
                    part_info = link_info.copy()
                    part_info['url'] = final_part_link
                    parts.append(part_info)
                    
                logger.debug(f'{parts_count} part links scraped (source link index: {index + 1}, total source links: {len(links)})')

        backup.append(link)
        
    with open('data/parts.json', 'w') as f:
        json.dump(parts, f, indent=4)

    with open('data/visited.json', 'w') as f:
        json.dump(list(set(backup)), f, indent=4)
    
    logger.info(f'Phase 3 completed, {parts_count} parts to scrape, links to parts saved to parts.json')
    logger.info('-'*20)

    return driver, parts
    

def phase_four(driver, parts):
    """Scrapes the information for all individual parts"""

    logger.info(f'Starting phase 4, {len(parts)} total parts to scrape')
    
    try:
        with open('data/data.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        data = []

    try:
        with open('data/visited.json', 'r') as f:
            backup = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        backup = []

    for index, part in enumerate(parts):

        fail_count = 0
        skip = False

        link = part['url']

        if link in backup:
            continue

        logger.debug(f'visiting - {link}')

        if index % 25 == 0:
            if index != 0:
                logger.debug(f'{index + 1} parts information scraped (total: {len(parts)})')
    
        if index % 100 == 0:

            driver.delete_all_cookies()

            with open('data/data.json', 'w') as f:
                json.dump(data, f, indent=4)

            with open('data/visited.json', 'w') as f:
                json.dump(list(set(backup)), f, indent=4)

        while True:
            try:
                if fail_count >= 10:
                    logger.error(f'Page has failed loading 10 times in a row, skipping. Link -> {link}')
                    skip = True
                    with open('data/skipped.json', 'r') as f:
                        skipped = json.load(f)
                    skipped.append(link)
                    with open('data/skipped.json', 'w') as f:
                        json.dump(skipped, f, indent=4)
                    fail_count = 0
                    break
                driver.get(link)
                driver.find_element(By.CLASS_NAME, 'business-logo')
                fail_count = 0
                break
            except Exception:
                fail_count += 1
                logger.warning(f'Part at index {index + 1} not loaded successfully, retrying. Link -> {link}')
                time.sleep(2)
                driver.quit()
                time.sleep(2)
                driver = get_chromedriver(use_proxy=True)
                continue

        if skip: continue

        # Scraping the parts information

        part_info = {}
        part_info['Make'] = 'Lexus'
        part_info['Model'] = part['model']
        part_info['Type'] = part['type']
        part_info['Year'] = part['year']
        part_info['Category'] = part['category']
        part_info['URL'] = part['url']

        part_info['Part Description'] = driver.find_element(By.CLASS_NAME, 'prodDescriptH2').text.strip()

        part_info['Part number'] = driver.find_element(By.CLASS_NAME, 'stock-code-text').get_attribute('innerText').strip()
        part_info['Suppression(s)'] = driver.find_element(By.CLASS_NAME, 'alt-stock-code-text').get_attribute('innerText').strip()

        suggested = driver.find_element(By.CLASS_NAME, 'item-desc').get_attribute('innerText').strip()
        suggested = suggested.split('\n')
        suggested = list(filter(lambda sen: 'fits' in sen.lower(), suggested))

        if suggested:
            suggested = suggested[0]
        else:
            suggested = ''

        part_info['Suggested Fitment'] = suggested

        try:
            part_info['MSRP'] = driver.find_element(By.CLASS_NAME, 'money-3').text.strip()
        except:
            part_info['MSRP'] = 'N/A'

        data.append(part_info)
        backup.append(link)

    with open('data/data.json', 'w') as f:
        json.dump(data, f, indent=4)

    df = pandas.DataFrame(data=data)
    df.to_excel('output.xlsx')

    with open('data/visited.json', 'w') as f:
        json.dump(list(set(backup)), f, indent=4) 

    logger.info(f'Phase 4 completed, results saved to data.json and output.xlsx')
    logger.info('-'*20)


if __name__ == '__main__':
    main()
