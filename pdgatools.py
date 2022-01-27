"""Tools to get and work with player data from the PDGA website."""

__copyright__ = "Copyright (C) 2022 Andreas Andersson"
__license__ = "The MIT License"

import enum
import requests
from bs4 import BeautifulSoup
import datetime, re, dateutil.relativedelta
from dataclasses import dataclass
import math, statistics

@dataclass
class TournamentResult:
    """Dataclass to represent a disc golf tournament result."""
    place: int
    points: float
    tournament: str
    event_url: str
    division: str
    tier: str
    start_date: datetime.date
    end_date: datetime.date


@dataclass
class RoundResult:
    """Dataclass to represent a disc golf round result."""
    course: str
    par: int
    score: int
    rating: float


@dataclass
class RoundRating:
    """Dataclass to represent a disc golf round rating."""
    date: datetime.date
    rating: int


class Player:
    """Tools to scrape stats and info about a disc golf player from the PDGA website.
    
    Attributes:
        pdga_number (int): The players PDGA number.
        name (str): The name of the player.
        location (str): The location of the player.
        since (int): The year that the player became a member of the PDGA.
        rating (int): Tha player current rating.
        classification (str): Wether the player is a professional or not.
        events (int): Number of events played throughout the players career.
        wins (int): Number of wins throughout the players career.
        earnings (float): Career earnings in USD.
    """

    def __init__(self, pdga_number):
        """Create a new Player instance and populate attributes.
        
        NOTE: This function will have to be updated if the PDGA website changes.

        Args:
            pdga_number (int): The players PDGA number.
        """
        self.pdga_number = str(pdga_number)

        # Get and parse player info from pdga.com:
        html = requests.get(f'https://www.pdga.com/player/{self.pdga_number}').text
        soup = BeautifulSoup(html, 'html.parser')
        ul = soup.find('ul', class_='player-info')
        self.name = soup.find('h1', id='page-title').text.split('#')[0].strip()
        # Split at "Classification" to mitigate that the location li-tag isn't closed.
        self.location = ul.find('li', class_='location').text.split('Classification:')[0].removeprefix('Location:').strip()
        self.since = int(re.findall(r'\d+', ul.find('li', class_='join-date').text)[0])
        rating = ul.find('li', class_='current-rating')
        self.rating = int(re.findall(r'\d+', rating.text)[0]) if rating else None
        self.classification = ul.find('li', class_='classification').text.removeprefix('Classification:').strip()
        events = ul.find('li', class_='career-events')
        self.events = int(re.findall(r'\d+', events.text)[0]) if events else 0
        wins = ul.find('li', class_='career-wins')
        self.wins = int(re.findall(r'\d+', wins.text)[0]) if wins else 0
        earnings = ul.find('li', class_='career-earnings')
        self.earnings = float(re.findall(r'[\d,\.]+', earnings.text)[0].replace(',', '')) if earnings else 0.0

    def included_round_ratings(self) -> list[RoundRating]:
        """Get all round ratings included in latest rating.
        
        NOTE: This function will have to be updated if the PDGA website changes.

        Returns:
            list[RoundRating]: Round ratings and their dates included in latest rating.
        """
        # Get ratings detail for player from the PDGA website
        html = requests.get(f'https://www.pdga.com/player/{self.pdga_number}/details').text
        soup = BeautifulSoup(html, 'html.parser')
        # Find all included ratings (<td class="round-rating"> within <tr class="included").
        ratings = []
        for record in soup.find_all('tr', class_='included'):
            _, date = self._parse_dates(record.find('td', class_='date').text)
            rating = int(record.find('td', class_='round-rating').text)
            ratings.append(RoundRating(date=date, rating=rating))
        return ratings

    def events_from_period(self, start_date: datetime.date, end_date: datetime.date) -> list[TournamentResult]:
        """Get all events played given period.
        
        Events that started or ended within the period but part of it was played outside of
        the period will be included.
        
        Args:
            start_date (date): The first date of the period.
            end_date (date): The last day of the period.

        Returns:
            List[TournamentResult]: Tournament results for every event played the given year.
        """
        events = []
        # Error check. Dates cannot be after today.
        if start_date > datetime.date.today():
            start_date = datetime.date.today()
        if end_date > datetime.date.today():
            end_date = datetime.date.today()
        # Get events
        for year in range(start_date.year, end_date.year + 1):
            efy = self.events_from_year(year)
            for event in efy:
                if event.end_date >= start_date and event.start_date <= end_date:
                    events.append(event)
        return events

    def events_from_year(self, year: int) -> list[TournamentResult]:
        """Get all events played given year.

        NOTE: This function will have to be updated if the PDGA website changes.
        
        Args:
            year (int): The year to get events for.

        Returns:
            List[TournamentResult]: Tournament results for every event played the given year.
        """
        html = requests.get(f'https://www.pdga.com/player/{self.pdga_number}/stats/{str(year)}').text
        soup = BeautifulSoup(html, 'html.parser')
        table_containers = soup.find_all(class_='table-container')
        rows = []
        for tc in table_containers:
            table = tc.find('table')
            rows += table.find_all('tr', {"class": ["odd", "even"]})
        results = []
        for r in rows:
            place = int(r.find(class_='place').text)
            try:
                points = float(r.find(class_='points').text)
            except ValueError:
                points = None
            tournament = r.find('a').text
            href = r.find('a').attrs['href'].split('#')
            event_url = 'https://www.pdga.com' + href[0]
            division = href[1]
            tier = r.find(class_='tier').text
            start_date, end_date = self._parse_dates(r.find(class_='dates').text)
            results.append(TournamentResult(place, points, tournament, event_url, division, tier, start_date, end_date))
        # If the year given is invalid the PDGA site will give results for current year. So if given year and
        # and tournament dates doesn't match, return empty list.
        if results and results[0].start_date.year != year and results[0].end_date.year != year:
            results = []
        return results

    def round_results_for_event(self, event_url: str) -> list[RoundResult]:
        """Get round results for a played event.

        NOTE: This function will have to be updated if the PDGA website changes.
        
        Args:
            event_url (str): The URL for the event.

        Returns:
            list[RoundResult]: The round results for the event.
        """
        html = requests.get(event_url).text
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find(class_='pdga-number', text=self.pdga_number).parent 
        head = row.parent.parent.find('thead')
        round_ths = head.find_all(class_='round tooltip')
        scores = row.find_all(class_='round')
        ratings = row.find_all(class_='round-rating')
        round_results = []
        for i in range(len(scores)):
            course = None
            par = None
            if round_ths:
                round_tool_tip = soup.find(id=round_ths[i].attrs['data-tooltip-content'].strip('#'))
                tool_tip_parts = round_tool_tip.text.split(';')
                course = tool_tip_parts[0].strip()
                par = int(re.findall(r'\d+', tool_tip_parts[2])[0])
            try:
                score=int(scores[i].text)
            except:
                # Player did not participate in this round
                continue
            try:
                rating=int(ratings[i].text)
            except:
                # Maybe a play-off or non-standard event?
                rating = None
            round_results.append(RoundResult(course=course, par=par, score=score, rating=rating))
        return round_results

    def estimate_next_rating(self) -> int:
        """Guess next rating based on latest played events.

        Returns:
            int: Estimated new rating.
        """
        round_ratings = self.included_round_ratings()
        # Find date for last round rating included in last rating. We'll search for new events from there.
        last_date = round_ratings[0].date
        # Find new events and append dates and ratings to our list
        new_events = self.events_from_period(last_date + dateutil.relativedelta.relativedelta(days=1), datetime.date.today())
        for e in new_events:
            round_results = self.round_results_for_event(e.event_url)
            for r in round_results:
                # There's no way to extract round dates, so we'll have to go with event date.
                round_ratings.append(RoundRating(e.end_date, r.rating))
        # Calculate new rating
        rating = Rating()
        rating.update(round_ratings, order=Rating.DataOrder.UNSORTED)
        return rating.rating

    def _parse_dates(self, date_str: str) -> tuple[datetime.date, datetime.date]:
        """Return start and end dates from a PDGA table date string.
        
        Args:
            date_str (str): Date(s) in either of the formats "DD-Mon-YEAR" or "DD-Mon to DD-Mon-YEAR".

        Returns:
            tuple[date, date]: Start date and end date.
        """
        dates = date_str.split(' to ')
        year = dates[-1].strip()[-4:]
        start_date = datetime.datetime.strptime(dates[0] if dates[0].endswith(year) else f'{dates[0]}-{year}', '%d-%b-%Y')
        end_date = datetime.datetime.strptime(dates[-1], '%d-%b-%Y')
        return start_date.date(), end_date.date()
        

class Rating:
    """Represents a PDGA rating with methods to calculate new rating.
    
    Attributes:
        rating (int): PDGA rating.
        as_of (date): Date when this rating was published.
        included (list[RoundRating]): List of round ratings that was used to calculate the rating.
    """

    class DataOrder(enum.Enum):
        UNSORTED = enum.auto(),
        RECENT_FIRST = enum.auto(),
        RECENT_LAST = enum.auto()

    def __init__(self, rating: int=None, as_of: datetime.date=None):
        """Initialize a new Rating.
        
        Args:
            rating (int): PDGA rating.
            as_of (date): Date when this rating was published.
        """
        self.rating = rating
        self.as_of = as_of
        self.included: list[RoundRating] = None

    def update(self, round_ratings: list[RoundRating], order: DataOrder=DataOrder.RECENT_FIRST, as_of: datetime.date=None, most_recent_round_date: datetime.date=None):
        """Update rating using given data. This will update the rating, included and (optionally) as_of attributes.

        Calulcations aren't perfect, but get's very close. According to a PDGA official "additional, minor items are kept
        confidential by the PDGA". Also, we can only access published round ratings which are "converted to integers, but¨
        the ratings algorithm uses round ratings as real numbers". This means our calculations will sometimes be rounded
        to the wrong integer.

        Args:
            round_ratings (list[RoundRatings]): A list of round ratings.
            order (DataOrder): Indicate if and how round_ratings is sorted. (Default: RECENT_FIRST)
            as_of (date): Date when this rating will be published. The as_of attribute will not be updated if this is
                set to None. (Default: None)
            most_recent_round_date (date): The date of the most recent round, or None to use the date of the most recent
                round included in round_ratings. (Default: None)
        """
        # Calculate
        included = Rating.round_ratings_in_date_range(round_ratings, most_recent_round_date, order)
        included = Rating.remove_outliers(included)
        with_doubled = Rating.double_most_recent_quarter(included)
        rating = statistics.fmean([x.rating for x in with_doubled])

        # Update attributes
        self.rating = round(rating) # Is this the correct?
        self.included = sorted(included, key=lambda i: (i.date, i.rating))
        if as_of:
            self.as_of = as_of

    @staticmethod
    def round_ratings_in_date_range(round_ratings: list[RoundRating], most_recent_round_date: datetime.date=None, order: DataOrder=DataOrder.RECENT_FIRST) -> list[RoundRating]:
        """Return round ratings within the last 12 or 24 months from given date.
        
        From the PDGA Ratings System Guide:
        "A player's PDGA rating is based on rounds in the 12 months prior to the date of their most recently rated round.
        ...
        If a player has fewer than 8 rounds within the 12-month period, the system will go back up to 24 months until it
        either finds 8 total rounds, or all rounds within the 24-month period if fewer than 8."

        Args:
            round_ratings (list[RoundRatings]): A list of round ratings.
            most_recent_round_date (date): The date of the most recent round, or None to use the date of the most recent
                round included in round_ratings. (Default: None)
            order (DataOrder): Indicate if and how round_ratings is sorted. (Default: RECENT_FIRST)

        Returns:
            list[RoundRating]: Round ratings sorted by date.
        """
        if not round_ratings:
            return []
        # Things get easier if sorted by date.
        if order == Rating.DataOrder.RECENT_FIRST:
            sorted_rr = round_ratings[::-1]
        elif order == Rating.DataOrder.RECENT_LAST:
            sorted_rr = round_ratings
        else:
            sorted_rr = sorted(round_ratings, key=lambda r : r.date)
        
        # Get date of most recent round, if not given by user.
        if not most_recent_round_date:
            most_recent_round_date = sorted_rr[-1].date

        # Find ratings within a 12 month period
        m12 = most_recent_round_date - dateutil.relativedelta.relativedelta(months=12)
        ratings = [r for r in sorted_rr if r.date >= m12 and r.date <= most_recent_round_date]

        # If needed, find more ratings within a 24 month period
        m24 = most_recent_round_date - dateutil.relativedelta.relativedelta(months=24)
        while len(ratings) < 8:
            # Find the index in round_ratings for the first item in ratings
            i = sorted_rr.index(ratings[0]) if ratings else len(sorted_rr)
            # Insert the item on the index before that (if it's within the 24 month period)
            if i <= 0 or sorted_rr[i - 1].date < m24:
                break
            ratings.insert(0, sorted_rr[i - 1])
        return ratings

    @staticmethod
    def remove_outliers(round_ratings: list[RoundRating]) -> list[RoundRating]:
        """Remove ratings that are more than 100pts or 2.5sd below average (if 7 or more rounds available).

        From the PDGA Ratings System Guide:
        "Rounds more than 2.5 standard deviations or more than 100 points below a player's average are excluded from
        the player's rating if there are at least 7 rounds included in the player's rating."

        Args:
            ratings (list[RoundRating]): Round ratings.

        Returns:
            list[RoundRating]: Round ratings without outliers, sorted by date then rating.        
        """
        sorted_rr = sorted(round_ratings, key=lambda r : r.rating, reverse=True)
        ratings = [r.rating for r in sorted_rr]
        avg = statistics.fmean(ratings)
        sd = statistics.pstdev(ratings)
        result = []
        for r in sorted_rr:
            diff = avg - r.rating
            if (diff < sd * 2.5 and diff < 100.0) or len(result) < 7:
                result.append(r)
        return sorted(result, key=lambda r : (r.date, r.rating))

    @staticmethod
    def double_most_recent_quarter(round_ratings: list[RoundRating]) -> list[RoundRating]:
        """Duplicate the most recent 25% of the round ratings (if there are 9 or more rounds available).
        
        From the PDGA Ratings System Guide:
        "The most recent 25% (1/4) of rounds will count double once there are at least 9 round ratings."

        Args:
            round_ratings (list[RoundRating]): Round ratings.

        Returns:
            list[RoundRating]: Round ratings with the most recent 25% records appearing twice.
        """
        i = len(round_ratings) if len(round_ratings) < 9 else math.ceil(0.75 * len(round_ratings))
        return round_ratings + round_ratings[i:]
