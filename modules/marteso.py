"""
Marteso API Module

Handles:
- Loading Netscape cookies
- Creating authenticated session
- Searching keywords
- Returning keyword metrics

Author: Waseem
"""

import json
import requests
from http.cookiejar import MozillaCookieJar


class MartesoClient:

    BASE_URL = "https://app.marteso.com/api/keywords"

    def __init__(self, cookie_file="cookies/cookies.txt"):

        self.cookie_file = cookie_file
        self.session = requests.Session()

        self._load_cookies()

    ##########################################################

    def _load_cookies(self):
        """
        Load Netscape cookies into the requests session.
        """

        jar = MozillaCookieJar()

        jar.load(
            self.cookie_file,
            ignore_discard=True,
            ignore_expires=True
        )

        self.session.cookies.update(jar)

    ##########################################################

    def _headers(self):

        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://app.marteso.com",
            "Referer": "https://app.marteso.com/",
            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/139.0 Safari/537.36"
            )
        }

    ##########################################################

    def search_keyword(
        self,
        keyword,
        country="us",
        language="en",
        bundle_id="com.guess.the.puzzle.games"
    ):
        """
        Search a single keyword.
        """

        payload = {

            "term": keyword,

            "country": country,

            "language": language,

            "bundleId": bundle_id

        }

        response = self.session.post(

            self.BASE_URL,

            json=payload,

            headers=self._headers(),

            timeout=30

        )

        if response.status_code != 200:

            raise Exception(
                f"Marteso Error {response.status_code}\n{response.text}"
            )

        data = response.json()

        if not data.get("ok"):

            raise Exception("Marteso returned unsuccessful response.")

        keyword_data = data["keyword"]

        return {

            "Keyword": keyword_data["term"],

            "Popularity": keyword_data["popularity"],

            "Difficulty": keyword_data["difficulty"],

            "Search Volume": keyword_data["searchVolume"],

            "Country": keyword_data["country"],

            "Language": keyword_data["language"]

        }

    ##########################################################

    def bulk_search(
        self,
        keywords,
        country,
        language,
        bundle_id="com.guess.the.puzzle.games"
    ):

        results = []

        for kw in keywords:

            kw = kw.strip()

            if not kw:
                continue

            try:

                result = self.search_keyword(
                    kw,
                    country,
                    language,
                    bundle_id
                )

                results.append(result)

            except Exception as e:

                results.append({

                    "Keyword": kw,

                    "Popularity": None,

                    "Difficulty": None,

                    "Search Volume": None,

                    "Country": country,

                    "Language": language,

                    "Error": str(e)

                })

        return results
