from requests import Session

from fake_useragent import UserAgent
from typing import Optional, Any



class InstagramScrap:
    def __init__(self, url: Optional[str] = None) -> None:
        self.url: str = url
        self.headers: dict = {
            'user-agent': UserAgent().random,
            'accept': '*/*',
            'x-asbd-id': '198387',
            'x-csrftoken': 'Syec0DkgHCcwN9bgCBNaNAID2VwENckW',
            'x-ig-app-id': '936619743392459',
        }
    
    def _get_response(self, url: Optional[str] = None) -> Any:
        with Session() as session:
            with session.get(url if url else self.url, headers=self.headers) as response:
                return response.json()

    def get_response_user(self, username: str) -> Any:
        return self._get_response(f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}')

    def get_response_feed(self, username: str) -> Any:
        return self._get_response(f'https://www.instagram.com/api/v1/feed/user/{username}/username/?count=120')
    
    def get_sub(self, username: str) -> tuple[int, int]:
        """Returns the number of subscribers and the number of subscriptions"""
        response = self.get_response_user(username)
        return response['data']['user']['edge_follow']['count'], response['data']['user']['edge_followed_by']['count']


if __name__ == '__main__':
    i = InstagramScrap()
    print(i.get_sub('razeqqo'))
