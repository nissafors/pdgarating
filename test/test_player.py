from posixpath import curdir
import unittest, sys, os
from unittest import mock
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pdgatools import Player, RoundRating, RoundResult, TournamentResult

def requests_get(url):
    """Mock requests.get."""
    return get_web_page(url)

class TestPlayer(unittest.TestCase):
    def setUp(self):
        pass

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_included_round_ratings(self):
        # Use Kevin Jones results downloaded January 2022.
        p = Player(41760)
        expected_first_three = [
            RoundRating(date=date(2021, 9, 26), rating=1070),
            RoundRating(date=date(2021, 9, 26), rating=1027),
            RoundRating(date=date(2021, 9, 26), rating=1062)
        ]
        expected_not_included = RoundRating(date=date(2021, 4, 25), rating=970)
        expected_last_three = [
            RoundRating(date=date(2020, 10, 3), rating=1006),
            RoundRating(date=date(2020, 10, 3), rating=1051),
            RoundRating(date=date(2020, 10, 3), rating=999)
        ]
        actual = p.included_round_ratings()
        self.assertListEqual(expected_first_three, actual[:3])
        self.assertListEqual(expected_last_three, actual[-3:])
        self.assertNotIn(expected_not_included, actual)
        self.assertEqual(76, len(actual))

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_events_from_year_kj_2021(self):
        # Use Kevin Jones results from 2021 downloaded January 2022.
        p = Player(41760)
        expected_first = TournamentResult(
            place=7,
            points=1300.0,
            tournament='DGPT - Las Vegas Challenge presented by Innova',
            event_url='https://www.pdga.com/tour/event/47877',
            division='MPO',
            tier='NT',
            start_date=date(2021, 2, 25),
            end_date=date(2021, 2, 28)
        )
        expected_last = TournamentResult(
            place=5,
            points=280.0,
            tournament='DGPT Championship Presented by Guaranteed Rate',
            event_url='https://www.pdga.com/tour/event/48691',
            division='MPO',
            tier='NT',
            start_date=date(2021, 10, 14),
            end_date=date(2021, 10, 17)
        )
        expected_in = TournamentResult(
            place=21,
            points=None,
            tournament='Long Drive Contest at 2021 Pro Worlds',
            event_url='https://www.pdga.com/tour/event/51685',
            division='MPO',
            tier='XC',
            start_date=date(2021, 6, 20),
            end_date=date(2021, 6, 20)
        )
        actual = p.events_from_year(2021)
        self.assertEqual(expected_first, actual[0])
        self.assertEqual(expected_last, actual[-1])
        self.assertIn(expected_in, actual)
        self.assertEqual(27, len(actual))

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_events_from_year_kj_2020(self):
        # Use Kevin Jones results from 2021 downloaded January 2022.
        p = Player(41760)
        expected_first = TournamentResult(
            place=6,
            points=1450.0,
            tournament='Las Vegas Challenge presented by Innova Champion Discs',
            event_url='https://www.pdga.com/tour/event/43105',
            division='MPO',
            tier='A',
            start_date=date(2020, 2, 20),
            end_date=date(2020, 2, 23)
        )
        actual = p.events_from_year(2020)
        self.assertEqual(expected_first, actual[0])
        self.assertEqual(23, len(actual))

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_events_from_year_invalid_year(self):
        # There were no results from 2022 at the time of writing.
        p = Player(41760)
        actual = p.events_from_year(2022)
        self.assertEqual(0, len(actual))

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_events_from_year_multiple_divisions(self):
        # This player played in both recreational and intermediate during 2020.
        p = Player(140592)
        expected = [
            TournamentResult(30, 48.0, 'Smålandstouren Älmhult Open', 'https://www.pdga.com/tour/event/45639', 'MA2', 'C', date(2020, 7, 18), date(2020, 7, 18)),
            TournamentResult(27, 48.0, 'Ljungby Open', 'https://www.pdga.com/tour/event/46771', 'MA2', 'C', date(2020, 8, 15), date(2020, 8, 15)),
            TournamentResult(9, 27.0, '033-Tour Gässlösa', 'https://www.pdga.com/tour/event/47387', 'MA3', 'C', date(2020, 10, 25), date(2020, 10, 25))
        ]
        actual = p.events_from_year(2020)
        self.assertListEqual(expected, actual)

    def test_events_from_period(self):
        # Use Kevin Jones results from 2020-2021 downloaded January 2022.
        p = Player(41760)
        actual = p.events_from_period(date(2020, 11, 10), date(2021, 2, 28))
        expected = [
            TournamentResult(5, 570.0, 'Dynamic Discs Northwest Arkansas Presents: Northwest Arkansas Open', 'https://www.pdga.com/tour/event/43682', 'MPO', 'A', date(2020, 11, 13), date(2020, 11, 15)),
            TournamentResult(7, 1300.0, 'DGPT - Las Vegas Challenge presented by Innova', 'https://www.pdga.com/tour/event/47877', 'MPO', 'NT', date(2021, 2, 25), date(2021, 2, 28))
        ]
        self.assertListEqual(expected, actual)

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_round_results_for_event(self):
        # Ordinary tournament (Las Vegas Challenge 2021) played by Kevin Jones downloaded January 2022.
        p = Player(41760)
        expected = [
            RoundResult('Infinite', 59, 53, 1028),
            RoundResult('Innova', 62, 53, 1041),
            RoundResult('Factory Store', 61, 53, 1046),
            RoundResult('Innova Finals', 62, 50, 1082)
        ]
        actual = p.round_results_for_event('https://www.pdga.com/tour/event/47877')
        self.assertListEqual(expected, actual)

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_round_results_for_event(self):
        # Ordinary tournament (Las Vegas Challenge 2021) played by Kevin Jones downloaded January 2022.
        p = Player(41760)
        expected = [
            RoundResult('Infinite', 59, 53, 1028),
            RoundResult('Innova', 62, 53, 1041),
            RoundResult('Factory Store', 61, 53, 1046),
            RoundResult('Innova Finals', 62, 50, 1082)
        ]
        actual = p.round_results_for_event('https://www.pdga.com/tour/event/47877')
        self.assertListEqual(expected, actual)

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_round_results_for_event_putting_contest(self):
        # Putting Contest at 2021 Pro Worlds played by Kevin Jones downloaded January 2022.
        # This event has no info on course or par, nor on round rating.
        p = Player(41760)
        expected = [
            RoundResult(None, None, 999, None),
        ]
        actual = p.round_results_for_event('https://www.pdga.com/tour/event/51684')
        self.assertListEqual(expected, actual)

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_round_results_for_event_w_link_to_course(self):
        # Savannah Open 2021 played by Nathan Queen downloaded January 2022.
        # This event has the course name partly embedded in an anchor tag.
        p = Player(68286)
        expected = [
            RoundResult('Tom Triplett Disc Golf Course - Black', 62, 59, 1012),
            RoundResult('Tom Triplett Disc Golf Course - Red', 55, 51, 979),
            RoundResult('Tom Triplett Disc Golf Course - Gold', 64, 54, 1061),
            RoundResult('Tom Triplett Disc Golf Course - Black Tees Playoffs', 20, 23, None)
        ]
        actual = p.round_results_for_event('https://www.pdga.com/tour/event/47932')
        self.assertListEqual(expected, actual)

    @mock.patch('pdgatools.requests.get', mock.Mock(side_effect=requests_get))
    def test_estimate_next_rating(self):
        p = Player(44382)
        expected = 1026
        actual = p.estimate_next_rating()
        self.assertEqual(expected, actual)

def get_web_page(url):
    """Mock for requests.get. Returns an object with the text attribute set to html for given url."""
    class MockResponse:
        def __init__(self, html, status_code):
            self.text = html
            self.status_code = status_code
    cur_dir = os.path.abspath(os.path.curdir)
    test_dir = cur_dir if cur_dir.endswith('test') else os.path.join(cur_dir, 'test')
    html_dir = 'html'
    file = ''
    content = ''
    status_code = 404
    if url == 'https://www.pdga.com/player/41760/details':
        file = 'kj_included.html'
        status_code = 200
    elif url == 'https://www.pdga.com/player/44382/details':
        file = 'ab_included.html'
        status_code = 200
    elif url == 'https://www.pdga.com/player/41760/stats/2020':
        file = 'kj_stats_2020.html'
        status_code = 200
    elif url == 'https://www.pdga.com/player/41760/stats/2021':
        file = 'kj_stats_2021.html'
        status_code = 200
    elif url == 'https://www.pdga.com/player/41760/stats/2022':
        # The PDGA site returns the results from the last year they had records.
        # In this case, we pretend that 2021 was the last year they did so.
        file = 'kj_stats_2021.html'
        status_code = 200
    elif url == 'https://www.pdga.com/player/140592/stats/2020':
        file = 'tn_stats_2020.html'
        status_code = 200
    elif url == 'https://www.pdga.com/player/44382/stats/2021':
        file = 'ab_stats_2021.html'
        status_code = 200
    elif url == 'https://www.pdga.com/player/44382/stats/2022':
        file = 'ab_stats_2022.html'
        status_code = 200
    elif url == 'https://www.pdga.com/tour/event/47877':
        # Las Vegas Challenge presented by Innova 2021
        file = 'lvc_event.html'
        status_code = 200
    elif url == 'https://www.pdga.com/tour/event/51685':
        # Long Drive Contest at 2021 Pro Worlds 2021
        file = 'ldc_event.html'
        status_code = 200
    elif url == 'https://www.pdga.com/tour/event/51684':
        # Putting Contest at 2021 Pro Worlds
        file = 'pcw_event.html'
        status_code = 200
    elif url == 'https://www.pdga.com/tour/event/47932':
        # Savannah Open 2021
        file = 'so_event.html'
        status_code = 200
    elif url == 'https://www.pdga.com/tour/event/55325':
        # Shelly Sharpe Memorial 2022
        file = 'ssm_event.html'
        status_code = 200
    if file:
        with open(os.path.join(test_dir, html_dir, file), 'r') as f:
            content = f.read()
    return MockResponse(content, status_code)

if __name__ == '__main__':
    unittest.main()
