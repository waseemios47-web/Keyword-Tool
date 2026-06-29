"""
Marteso API Module

Features
--------
✓ Search keyword
✓ Bulk keyword search
✓ Get all tracked keywords
✓ Get tracked keywords by country
✓ Get tracked keyword count
✓ Delete keyword
✓ Delete all keywords in one country

Author: Waseem
"""

import requests
from http.cookiejar import MozillaCookieJar


class MartesoClient:

    BASE_URL = "https://app.marteso.com/api"
    KEYWORDS_URL = f"{BASE_URL}/keywords"

    def __init__(
        self,
        cookie_file="cookies/cookies.txt",
        bundle_id="com.guess.the.puzzle.games"
    ):

        self.bundle_id = bundle_id
        self.cookie_file = cookie_file

        self.session = requests.Session()

        self._load_cookies()

    ######################################################################

    def _load_cookies(self):

        jar = MozillaCookieJar()

        jar.load(
            self.cookie_file,
            ignore_discard=True,
            ignore_expires=True
        )

        self.session.cookies.update(jar)

    ######################################################################

    def _headers(self):

        return {

            "Accept": "application/json",

            "Content-Type": "application/json",

            "Origin": "https://app.marteso.com",

            "Referer": "https://app.marteso.com/",

            "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/139.0 Safari/537.36"

        }

    ######################################################################

    def search_keyword(
        self,
        keyword,
        country="us",
        language="en"
    ):

        payload = {

            "term": keyword,

            "country": country,

            "language": language,

            "bundleId": self.bundle_id

        }

        response = self.session.post(

            self.KEYWORDS_URL,

            json=payload,

            headers=self._headers(),

            timeout=30

        )

        response.raise_for_status()

        data = response.json()

        if not data.get("ok"):

            raise Exception(data)

        keyword_data = data["keyword"]

        if keyword_data is None:

            raise Exception("Keyword not returned.")

        return {

            "ID": keyword_data["id"],

            "Keyword": keyword_data["term"],

            "Popularity": keyword_data["popularity"],

            "Difficulty": keyword_data["difficulty"],

            "Search Volume": keyword_data["searchVolume"],

            "Country": keyword_data["country"],

            "Language": keyword_data["language"],

            "Updated": keyword_data["updatedAt"]

        }

    ######################################################################

    def bulk_search(
        self,
        keywords,
        country,
        language
    ):

        results = []

        for kw in keywords:

            kw = kw.strip()

            if not kw:
                continue

            try:

                results.append(

                    self.search_keyword(
                        kw,
                        country,
                        language
                    )

                )

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

    ######################################################################

    def get_all_keywords(self):

        response = self.session.get(

            self.KEYWORDS_URL,

            params={

                "bundleId": self.bundle_id

            },

            headers=self._headers(),

            timeout=30

        )

        response.raise_for_status()

        data = response.json()

        return data.get("items", [])

    ######################################################################

    def get_keywords_by_country(
        self,
        country
    ):

        items = self.get_all_keywords()

        return [

            x

            for x in items

            if x["country"] == country

        ]

    ######################################################################

    def tracked_count(
        self,
        country=None
    ):

        if country is None:

            return len(
                self.get_all_keywords()
            )

        return len(

            self.get_keywords_by_country(
                country
            )

        )

    ######################################################################

    def remaining_slots(
        self,
        country,
        limit=50
    ):

        return max(

            0,

            limit - self.tracked_count(country)

        )

    ######################################################################

    def keyword_exists(
        self,
        keyword,
        country
    ):

        keyword = keyword.lower()

        for item in self.get_keywords_by_country(country):

            if item["term"].lower() == keyword:

                return True

        return False

    ######################################################################

    def delete_keyword(
        self,
        keyword_id
    ):

        response = self.session.delete(

            f"{self.KEYWORDS_URL}/{keyword_id}",

            headers=self._headers(),

            timeout=30

        )

        return response.status_code == 200

    ######################################################################

    def delete_country_keywords(
        self,
        country
    ):

        deleted = 0

        keywords = self.get_keywords_by_country(
            country
        )

        for item in keywords:

            if self.delete_keyword(item["id"]):

                deleted += 1

        return deleted
