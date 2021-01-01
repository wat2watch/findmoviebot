import requests
from bs4 import BeautifulSoup
import re

AUTO_COMPLETE_URL = 'https://bestsimilar.com/movies/autocomplete?term=%s'
FIND_SIMILAR_URL = 'https://bestsimilar.com/movies/%s'
HEADERS = {'User-Agent': 'PostmanRuntime/7.26.5'}
PARSER = 'html.parser'

class FindMovieError(Exception):
    def __init__(self, message, code):

        # Call the base class constructor with the parameters it needs
        super(FindMovieError, self).__init__(message)

        self.message = message
        self.code = code

class Movie:

    movie_attrs = ['genre', 'country', 'duration', 'style', 'plot']

    def __init__(self, label):
        self.label = label
        self.webpage = self.get_webpage()
        self.bs = BeautifulSoup(self.webpage, PARSER)

    def get_webpage(self):
        result = requests.get(FIND_SIMILAR_URL % self.label, headers=HEADERS)
        if result.status_code == 200:
            return result.text
        raise FindMovieError('The request was not sent successfully !', result.status_code)
        
    def make(self):
        self.similar_movies = self.find_similar_movies()
        self.fullname = re.findall(r'<div class="name-c"><span>(.*)</span></div>', self.webpage)[0]
        self.thumb = 'https://bestsimilar.com/' + self.bs.find('div', class_='img-c').find('img')['src']
        self.rating = self.similar_movies[0][1]
        self.similar_movies.pop(0)
        self.set_more_attrs()

    def set_more_attrs(self):
        container = self.bs.find('div', class_='item')
        for attr in self.movie_attrs:
            previous = container.find("span", string=attr.capitalize() + ':')
            value = previous.findNext('span', class_='value').text if previous else None
            if value:
                value = " ".join(value.replace('\r\n', '').split()) # Eliminate extra spaces
            setattr(self, attr, value)

    def find_similar_movies(self):
        similar_movies = []
        items = self.bs.find_all('div', class_='item')
        for item in items:
            name = item.find('a', class_='name')
            if name:
                name = name.text
            rating = item.find('span', title='rating', class_='')
            if rating:
                rating = rating.text
            similar_movies.append([name, rating])
        return similar_movies


def autocomplete(term):
    result = requests.get(AUTO_COMPLETE_URL % term.replace(' ', '+'), headers=HEADERS)
    if result.status_code == 200:
        movies = result.json()
        if not movies or movies[0]['label'] == 'No results found ...':
            raise FindMovieError('The request was not sent successfully !', 404)
        return movies
    else:
        raise FindMovieError('The request was not sent successfully !', result.status_code)
