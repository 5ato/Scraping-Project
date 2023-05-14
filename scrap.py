from requests import Session
from fake_useragent import UserAgent
from typing import Optional


class Graber:
    def __init__(self, article: str):
        self.article: str = article
        self.url: str = self.get_url(article=article)
        self.headers: dict = {
            'User-Agent': UserAgent().random,
            'Connection': 'keep-alive',
        }

    @classmethod
    def get_url(cls, article: str) -> str:
        return f'https://card.wb.ru/cards/detail?spp=0&locale=ru&lang=ru&curr=rub&nm={article}'

    def get_request(self, url: Optional[str] = None):
        with Session() as session:
            with session.get(self.url if url is None else url, headers=self.headers) as response:
                return response.json()


def main():
    p = Graber(article='13912984')
    print(p.get_request())


if __name__ == '__main__':
    main()
