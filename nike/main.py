from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.common.by import By

from fake_useragent import UserAgent
from typing import Optional, Iterable
from time import sleep
from bs4 import BeautifulSoup

import logging
import csv
import os


def percentage_calculation(standart_price: int, discount_price: int):
    return str(100 - (round((100 * discount_price) / standart_price))) + '%'


class Scraping:
    def __init__(self, url: str):
        self.url: str = url

        self.options: ChromeOptions = ChromeOptions()
        self.options.add_argument("--headless")
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument(f"user-agent={UserAgent().random}")

        self.driver: Chrome = Chrome(options=self.options)
        self.driver.implicitly_wait(5)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            '''
        })

        self.action: ActionChains = ActionChains(self.driver)

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(module)s - %(levelname)s: %(message)s'
        )
        LOGGER.setLevel(logging.WARNING)

    def main(self, url: Optional[str] = None):
        try:
            self.driver.get(url if url else self.url)
            sleep(5)
            self.close_location()
            parser = Parsing(self.driver.page_source)
            cards = parser.get_cards()
            while cards:
                for card in cards:
                    name = parser.get_title(card)
                    subtitle = parser.get_subtitle(card)
                    image = parser.get_image(card)
                    standart_price = parser.get_standart_price(card)
                    discount_price = parser.get_discount_price(card)
                    if standart_price and discount_price:
                        standart = float(standart_price.strip('$'))
                        disc = float(discount_price.strip('$'))
                        discount = percentage_calculation(standart, disc)
                    else:
                        discount = None
                    messaning = parser.get_messaning(card)
                    yield name, subtitle, image, standart_price, discount_price, discount, messaning
                
                self.action.scroll_to_element(self.driver.find_element(By.CLASS_NAME, 'loader-bar.css-19k7nfv')).perform()
                sleep(3)
                cards = parser.get_cards(self.driver.page_source)
        finally:
            self.driver.close()
            self.driver.quit()
            sleep(5)
    
    def close_location(self):
        try:
            self.action.move_to_element(self.driver.find_element(By.CLASS_NAME, 'hf-modal-btn-close')).click().perform()
            sleep(2)
        except Exception as ex:
            logging.exception(ex)

    def scrolling_element(self):
        try:
            element = self.driver.find_element(By.CLASS_NAME, 'loader-bar.css-19k7nfv')
        except AttributeError:
            element = None
        return element


class Parsing:
    def __init__(self, html_code: str):
        self.html_response: BeautifulSoup = BeautifulSoup(html_code, 'lxml')
        self.last_element: int = 0

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(module)s - %(levelname)s: %(message)s'
        )
    
    def get_cards(self, html_code: Optional[str] = None):
        if self.last_element >= 900:
            return None
        if html_code:
            self.html_response = BeautifulSoup(html_code, 'lxml')
        try:
            cards = self.html_response.find_all('div', attrs={'data-testid': 'product-card'})[self.last_element::]
            logging.info(self.last_element)
            self.last_element = int(cards[-1].get('data-product-position'))
            logging.info(self.last_element)
        except AttributeError:
            cards = None
            self.last_element = None
        return cards
    
    def get_messaning(self, card: BeautifulSoup):
        try:
            messaning = card.find('div', attrs={'class': 'product-card__messaging accent--color'}).text.strip()
        except AttributeError:
            messaning = None
        return messaning

    def get_title(self, card: BeautifulSoup):
        try:
            title = card.find('div', attrs={'class': 'product-card__title'}).text.strip()
        except AttributeError:
            title = None
        return title
    
    def get_subtitle(self, card: BeautifulSoup):
        try:
            sub_title = card.find('div', attrs={'class': 'product-card__subtitle'}).text.strip()
        except AttributeError:
            sub_title = None
        return sub_title
    
    def get_standart_price(self, card: BeautifulSoup):
        try:
            price = card.find('div', attrs={'data-testid': 'product-price'}).text.strip()
        except AttributeError:
            price = None
        return price
    
    def get_discount_price(self, card: BeautifulSoup):
        try:
            discount_price = card.find('div', attrs={'data-testid': 'product-price-reduced'}).text.strip()
        except AttributeError:
            discount_price = None
        return discount_price

    def get_image(self, card: BeautifulSoup):
        try:
            image = card.find('img', attrs={'class': 'product-card__hero-image css-1fxh5tw'}).get('src')
        except AttributeError:
            image = None
        return image
    

class WriteCSV:
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def write(self, data: Iterable[str]) -> None:
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(['Title', 'Subtitle', 'Image', 'Standart Price', 'Discount Price', 'Discount', 'Messaning'])
                writer.writerow(data)
        else:
            with open(self.filename, 'a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(data)


if __name__ == '__main__':
    s = Scraping('https://www.nike.com/w/sale-clothing-3yaepz6ymx6')
    filename = s.url.split('-')[1]
    c = WriteCSV(f'data_{filename}.csv')
    for data in s.main():
        logging.info(data)
        c.write(data)
