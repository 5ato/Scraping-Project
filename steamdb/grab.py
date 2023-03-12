from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver

from bs4 import BeautifulSoup

from typing import Optional
from time import sleep
from dataclasses import dataclass, astuple
import logging
import csv
import os


@dataclass
class GameItem:
    name: str
    tags: list[str]
    rating: Optional[str]
    metacritic: Optional[str]
    developer: Optional[str]
    developer_site: Optional[str]
    publisher: Optional[str]
    publisher_site: Optional[str]
    current: int
    peak_24: int
    all_time_peak: int


class GameItemHandler:
    def __init__(self,
        name: str, tags: list[str], rating: Optional[str], metacritic: Optional[str],
        developer: Optional[str], developer_site: Optional[str], publisher: Optional[str], publisher_site: Optional[str],
        current: int, peak_24: int, all_time_peak: int
    ):
        self.game_item: GameItem = GameItem(
            name=name, tags=tags, rating=rating, metacritic=metacritic, developer=developer, developer_site=developer_site,
            publisher=publisher, publisher_site=publisher_site, current=current, peak_24=peak_24, all_time_peak=all_time_peak
        )
    
    def get_list(self) -> list:
        return [getattr(self.game_item, value) for value in self.game_item.__annotations__]


class MainPars:
    def __init__(self, url: str):
        self.url: str = url
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--disable-blink-features=AutomationControlled')

        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.implicitly_wait(5)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            '''
        })
        self.row = (
            'Game name', 'Game genre', 'Rating',
            'Game developer', 'Game developer website',
            'Game publisher', 'Game publisher website',
            'Current players', '24h peak players',
            'all-time peak players'
        )
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(module)s - %(levelname)s: %(message)s'
        )
        LOGGER.setLevel(logging.WARNING)
    
    def main_work(self) -> None:
        try:
            self.driver.get(self.url)
            self.driver.maximize_window()
            action = ActionChains(self.driver)
            next_page = self.check_next_page(By.ID, 'table-apps_next')

            while next_page:
                element_cards = self.driver.find_elements(By.CLASS_NAME, 'app')
                for element_card in element_cards:
                    card_td = element_card.find_elements(By.TAG_NAME, 'td')

                    name = card_td[2].text
                    current = card_td[3].text.replace(',', '')
                    peak_24h = card_td[4].text.replace(',', '')
                    all_time_peak = card_td[5].text.replace(',', '')

                    action.move_to_element(element_card).perform()
                    developer, developer_site = self.get_developer_or_publusher('developer')
                    publisher, publisher_site = self.get_developer_or_publusher('publisher')
                    tags = self.get_tags()
                    rating = self.get_rating()
                    sleep(1.5)

                    yield (name, tags, rating, developer, developer_site,
                        publisher, publisher_site, current, peak_24h, all_time_peak
                    )
                next_page = self.check_next_page(By.ID, 'table-apps_next')
                if next_page:
                    action.click(next_page).perform()
        finally:
            self.driver.close()
            self.driver.quit()

    def get_rating(self):
        try:
            rating = self.driver.find_element(By.CLASS_NAME, 'hover_body.hover_review_summary')\
                .find_element(By.TAG_NAME, 'a').text[10::]
        except Exception as ex:
            rating = 'does not exist'
            logging.info(ex)
        return rating

    def get_tags(self):
        try:
            tags = self.driver.find_element(By.CLASS_NAME, 'hover_body.hover_tag_row').text
        except Exception as ex:
            logging.info(ex)
            tags = 'does not exist'
        return tags

    def get_developer_or_publusher(self, person: str):
        hovers = self.driver.find_elements(By.CLASS_NAME, 'hover_body.hover_meta')
        for hover in hovers:
            if person in hover.text.lower():
                tags_a = hover.find_elements(By.TAG_NAME, 'a')
                dev_or_peb = '; '.join([name.text for name in tags_a])
                dev_or_peb_site = '; '.join(['https://steamdb.info/' + link.get_attribute('href') for link in tags_a])
                return dev_or_peb, dev_or_peb_site
        dev_or_peb = 'does not exist'
        dev_or_peb_site = 'does not exist'
        return dev_or_peb, dev_or_peb_site

    def check_next_page(self, by: By, value: str):
        try:
            next_page = self.driver.find_element(by, value)
        except Exception as ex:
            logging.info(ex)
            next_page = None
        return next_page


class WriteCSV:
    def __init__(self, filename: str):
        self.filename: str = filename

    def write(self, data: list, row: Optional[tuple or list] = None) -> None:
        if not os.path.exists(self.filename):   
            with open(self.filename, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(row)
                writer.writerow(data)
        else:
            with open(self.filename, 'a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(data)
                

if __name__ == '__main__':
    p = MainPars('https://steamdb.info/charts/?sort=peak')
    w = WriteCSV('data.csv')
    for item in p.main_work():
        logging.info(f'Scraping data: {item}')
        w.write(item, p.row)
