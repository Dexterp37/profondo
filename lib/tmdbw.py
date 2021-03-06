import requests
import requests_cache
import json
import operator
import logging

from skimage.io import imread
from cStringIO import StringIO

requests_cache.install_cache('tmdb_cache', backend='sqlite')


class TMDBW:
    """ TMDB wrapper for retrieving movie posters into numpy arrays.

    Usage example::

        from skimage.viewer import ImageViewer
        from tmdb import TMDB
        t = TMDBW("APIKEY")
        poster = t.get_movie("tt0062622")["poster"]
        ImageViewer(poster).show()

    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.service_url = "http://api.themoviedb.org/3"
        self.api_params = {"api_key": self.api_key}
        self.config = json.loads(self._request("/configuration"))

        self.poster_sizes = self.config["images"]["poster_sizes"]
        self.genres = json.loads(self._request("/genre/movie/list", {"language": "en-US"}))
        self.images_base_url = self.config["images"]["base_url"]

    def _request(self, request, params={}):
        params = dict(self.api_params.items() + params.items())
        return requests.get(self.service_url + request, params).content

    def _request_image(self, request, params={}):
        return requests.get(self.images_base_url + request, self.api_params).content

    def get_top_movies(self, release_year=None, limit=10):
        logging.debug("get_top_movies({}, {})".format(release_year, limit))
        params = {
          "primary_release_year": release_year,
          "sort_by": "popularity.desc"
        }

        page = 1
        pages = json.loads(self._request("/discover/movie", params))["total_pages"]
        while page <= pages:
            logging.debug("get_top_movies - fetching page {}".format(page))
            params["page"] = page
            page += 1

            movies = json.loads(self._request("/discover/movie", params))["results"]
            for movie in movies:
                yield self.get_movie(movie["id"])
                limit -= 1
                if limit == 0:
                    return

    def get_movie(self, imdb_id, size="original"):
        logging.debug("get_movie({}, {})".format(imdb_id, size))
        if size not in self.poster_sizes:
            raise Exception("Poster size {} is not in {}.".format(size, self.poster_sizes))

        movie = json.loads(self._request("/movie/{}".format(imdb_id)))
        poster = StringIO(self._request_image("/{}{}".format(size, movie["poster_path"])))
        return {
          "genres": [g["name"] for g in movie["genres"]],
          "poster": imread(poster),
          "adult": movie["adult"],
          "budget": movie["budget"],
          "language": movie["original_language"],
          "title": movie["title"],
          "overview": movie["overview"],
          "tagline": movie["tagline"],
          "release_date": movie["release_date"],
          "revenue": movie["revenue"]
        }
