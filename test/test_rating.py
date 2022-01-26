import unittest, math, sys, os
from datetime import date
from dateutil.relativedelta import relativedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pdgatools import Rating, RoundRating

class TestRating(unittest.TestCase):
    def setUp(self):
        # Create list of round ratings starting at 2020-01-01 with a result from the first day of each month up
        # to and including 2022-01-01. The first rating is 900 and it increases by 5 for each date so that the
        # last rating is 1020.
        self.round_ratings = [RoundRating(date=date(year=2020 + x // 12, month=x % 12 + 1, day=1), rating=900 + x * 5) for x in range(0, 25)]

    def test_round_ratings_in_date_range(self):
        # Return all within a 12 month period
        update_date = date(year=2020, month=12, day=1)
        expected = self.round_ratings[0:12]
        self.assertListEqual(expected, Rating.round_ratings_in_date_range(self.round_ratings, update_date, order=Rating.DataOrder.RECENT_LAST))
        # Use date of most recent round in self.round_ratings (2022-01-01)
        expected = self.round_ratings[12:]
        self.assertListEqual(expected, Rating.round_ratings_in_date_range(self.round_ratings, order=Rating.DataOrder.RECENT_LAST))

    def test_round_ratings_in_date_range_8_records_12_months_back(self):
        # There are 8 records 12 months back from this date, so it should return from 12 months back.
        update_date = date(year=2022, month=6, day=1)
        expected = self.round_ratings[17:]
        self.assertListEqual(expected, Rating.round_ratings_in_date_range(self.round_ratings, update_date, order=Rating.DataOrder.RECENT_LAST))

    def test_round_ratings_in_date_range_less_than_8_records_12_months_back(self):
        # There are only 7 records 12 months back from this date, so it should return 1 additional round.
        update_date = date(year=2022, month=7, day=1)
        expected = self.round_ratings[17:]
        self.assertListEqual(expected, Rating.round_ratings_in_date_range(self.round_ratings, update_date, order=Rating.DataOrder.RECENT_LAST))
        # There are only 6 records 12 months back from this date, so it should return 1 additional round.
        update_date = date(year=2022, month=8, day=1)
        expected = self.round_ratings[17:]
        self.assertListEqual(expected, Rating.round_ratings_in_date_range(self.round_ratings, update_date, order=Rating.DataOrder.RECENT_LAST))

    def test_round_ratings_in_date_range_less_than_8_records_24_months_back(self):
        # There are only 7 records 24 months back from this date, so it should only return those 7.
        update_date = date(year=2023, month=7, day=1)
        expected = self.round_ratings[18:]
        self.assertListEqual(expected, Rating.round_ratings_in_date_range(self.round_ratings, update_date, order=Rating.DataOrder.RECENT_LAST))

    def test_round_ratings_in_date_range_less_than_8_records_available_before_date(self):
        # There are only 7 records available back from this date, so it should return those 7.
        update_date = date(year=2020, month=7, day=1)
        expected = self.round_ratings[:7]
        self.assertListEqual(expected, Rating.round_ratings_in_date_range(self.round_ratings, update_date, order=Rating.DataOrder.RECENT_LAST))

    def test_round_ratings_in_date_range_unordered_list(self):
        # There are only 7 records available back from this date, so it should return those 7.
        order = [6, 7, 5, 8, 4, 9, 3, 10]
        scrambled_round_ratings = [self.round_ratings[i] for i in order]
        update_date = scrambled_round_ratings[order.index(min(order))].date + relativedelta(months=24)
        expected = self.round_ratings[3:11]
        self.assertListEqual(expected, Rating.round_ratings_in_date_range(scrambled_round_ratings, update_date, order=Rating.DataOrder.UNSORTED))

    def test_remove_outliers_100pts(self):
        # 10 ratings, mean=1000, 2.5sd~181. Last three are > 100 pts below average and should be removed.
        round_ratings = [RoundRating(date=date.today(), rating=x) for x in [1045] * 7 + [895] * 3]
        expected = round_ratings[:-3]
        self.assertListEqual(expected, Rating.remove_outliers(round_ratings))

    def test_remove_outliers_2p5sd(self):
        # 11 ratings, mean=900, 2.5sd~41.5. Last one is > 2.5sd below average.
        round_ratings = [RoundRating(date=date.today(), rating=x) for x in [905] * 10 + [850]]
        expected = round_ratings[:-1]
        self.assertListEqual(expected, Rating.remove_outliers(round_ratings))

    def test_remove_outliers_too_few_ratings(self):
        # 8 ratings, mean=900. First 2 are > 100 pts below average, but 7 must remain so only the worst should be removed.
        round_ratings = [RoundRating(date=date.today(), rating=x) for x in [894, 896] + [1035] * 6]
        expected = round_ratings[1:]
        x = Rating.remove_outliers(round_ratings)
        self.assertListEqual(expected, Rating.remove_outliers(round_ratings))

    def test_double_most_recent_quarter(self):
        round_ratings = [RoundRating(date=date.today(), rating=x) for x in [900 + y for y in range(9)]]
        i = math.ceil(len(round_ratings) * 0.75)
        expected = round_ratings + round_ratings[i:]
        self.assertListEqual(expected, Rating.double_most_recent_quarter(round_ratings))

    def test_double_most_recent_quarter_less_than_9_rounds(self):
        round_ratings = [RoundRating(date=date.today(), rating=x) for x in [900 + y for y in range(8)]]
        expected = round_ratings
        self.assertListEqual(expected, Rating.double_most_recent_quarter(round_ratings))

    def test_calculate_paul_mcbeth(self):
        # Test if we can match actual rating from the PDGA website
        round_ratings = [
            RoundRating(date=date(2021, 9, 26), rating=1010), RoundRating(date=date(2021, 9, 26), rating=1053), RoundRating(date=date(2021, 9, 26), rating=1055),
            RoundRating(date=date(2021, 9, 26), rating=1033), RoundRating(date=date(2021, 9, 19), rating=1071), RoundRating(date=date(2021, 9, 19), rating=1049),
            RoundRating(date=date(2021, 9, 19), rating=1060), RoundRating(date=date(2021, 9, 12), rating=1048), RoundRating(date=date(2021, 9, 12), rating=1072),
            RoundRating(date=date(2021, 9, 12), rating=1048), RoundRating(date=date(2021, 9, 12), rating=1044), RoundRating(date=date(2021, 9, 5), rating=1027),
            RoundRating(date=date(2021, 9, 5), rating=1072), RoundRating(date=date(2021, 9, 5), rating=1027), RoundRating(date=date(2021, 8, 15), rating=1053),
            RoundRating(date=date(2021, 8, 15), rating=1066), RoundRating(date=date(2021, 8, 15), rating=1007), RoundRating(date=date(2021, 8, 8), rating=1077),
            RoundRating(date=date(2021, 8, 8), rating=1011), RoundRating(date=date(2021, 8, 8), rating=1020), RoundRating(date=date(2021, 8, 1), rating=1067),
            RoundRating(date=date(2021, 8, 1), rating=1052), RoundRating(date=date(2021, 8, 1), rating=1059), RoundRating(date=date(2021, 7, 25), rating=1032),
            RoundRating(date=date(2021, 7, 25), rating=1047), RoundRating(date=date(2021, 7, 25), rating=1047), RoundRating(date=date(2021, 7, 11), rating=1067),
            RoundRating(date=date(2021, 7, 11), rating=1074), RoundRating(date=date(2021, 7, 11), rating=1045), RoundRating(date=date(2021, 6, 26), rating=1065),
            RoundRating(date=date(2021, 6, 26), rating=1053), RoundRating(date=date(2021, 6, 26), rating=1079), RoundRating(date=date(2021, 6, 26), rating=1065),        
            RoundRating(date=date(2021, 6, 26), rating=1047), RoundRating(date=date(2021, 6, 6), rating=1064), RoundRating(date=date(2021, 6, 6), rating=1052),
            RoundRating(date=date(2021, 6, 6), rating=1035), RoundRating(date=date(2021, 5, 30), rating=1054), RoundRating(date=date(2021, 5, 30), rating=1047),
            RoundRating(date=date(2021, 5, 30), rating=1033), RoundRating(date=date(2021, 5, 16), rating=1051), RoundRating(date=date(2021, 5, 16), rating=1038),        
            RoundRating(date=date(2021, 5, 16), rating=1064), RoundRating(date=date(2021, 5, 9), rating=1035), RoundRating(date=date(2021, 5, 9), rating=1022),
            RoundRating(date=date(2021, 5, 9), rating=1035), RoundRating(date=date(2021, 5, 9), rating=1052), RoundRating(date=date(2021, 5, 1), rating=1041),
            RoundRating(date=date(2021, 5, 1), rating=1073), RoundRating(date=date(2021, 5, 1), rating=1066), RoundRating(date=date(2021, 5, 1), rating=1066),
            RoundRating(date=date(2021, 4, 18), rating=1057), RoundRating(date=date(2021, 4, 18), rating=1065), RoundRating(date=date(2021, 4, 18), rating=1012),        
            RoundRating(date=date(2021, 3, 28), rating=1049), RoundRating(date=date(2021, 3, 28), rating=1056), RoundRating(date=date(2021, 3, 28), rating=1041),        
            RoundRating(date=date(2021, 3, 21), rating=1072), RoundRating(date=date(2021, 3, 21), rating=1080), RoundRating(date=date(2021, 3, 21), rating=1070),        
            RoundRating(date=date(2021, 3, 14), rating=1026), RoundRating(date=date(2021, 3, 14), rating=1043), RoundRating(date=date(2021, 3, 14), rating=1057),        
            RoundRating(date=date(2021, 3, 7), rating=1041), RoundRating(date=date(2021, 3, 7), rating=1051), RoundRating(date=date(2021, 3, 7), rating=1090),
            RoundRating(date=date(2021, 3, 7), rating=1082), RoundRating(date=date(2021, 2, 28), rating=1075), RoundRating(date=date(2021, 2, 28), rating=1038),
            RoundRating(date=date(2021, 2, 28), rating=1013), RoundRating(date=date(2021, 2, 28), rating=1071), RoundRating(date=date(2021, 1, 7), rating=1029),
            RoundRating(date=date(2020, 11, 8), rating=1019), RoundRating(date=date(2020, 11, 8), rating=1037), RoundRating(date=date(2020, 11, 8), rating=1033),        
            RoundRating(date=date(2020, 10, 3), rating=1073), RoundRating(date=date(2020, 10, 3), rating=1058), RoundRating(date=date(2020, 10, 3), rating=1044),
            # This last line was not included in the ratings calculation
            RoundRating(date=date(2020, 9, 13), rating=1056), RoundRating(date=date(2020, 9, 13), rating=1064), RoundRating(date=date(2020, 9, 13), rating=1086)
        ]
        expected_included = sorted(round_ratings[:78], key=lambda e: (e.date, e.rating))
        expected_rating = 1050
        r = Rating()
        r.update(round_ratings, date(2021, 10, 12))
        self.assertEqual(expected_rating, r.rating)
        self.assertListEqual(expected_included, r.included)

    def test_kevin(self):
        round_ratings = [
            RoundRating(date=date(2021, 9, 26), rating=1070), RoundRating(date=date(2021, 9, 26), rating=1027), RoundRating(date=date(2021, 9, 26), rating=1062),
            RoundRating(date=date(2021, 9, 26), rating=1026), RoundRating(date=date(2021, 9, 12), rating=1037), RoundRating(date=date(2021, 9, 12), rating=1040),
            RoundRating(date=date(2021, 9, 12), rating=1017), RoundRating(date=date(2021, 9, 12), rating=1024), RoundRating(date=date(2021, 9, 5), rating=1019),
            RoundRating(date=date(2021, 9, 5), rating=1012), RoundRating(date=date(2021, 9, 5), rating=1042), RoundRating(date=date(2021, 8, 15), rating=1059),
            RoundRating(date=date(2021, 8, 15), rating=1040), RoundRating(date=date(2021, 8, 15), rating=1040), RoundRating(date=date(2021, 8, 8), rating=1053),
            RoundRating(date=date(2021, 8, 8), rating=1034), RoundRating(date=date(2021, 8, 8), rating=1015), RoundRating(date=date(2021, 8, 1), rating=1037),
            RoundRating(date=date(2021, 8, 1), rating=1045), RoundRating(date=date(2021, 8, 1), rating=1037), RoundRating(date=date(2021, 7, 25), rating=1076),
            RoundRating(date=date(2021, 7, 25), rating=1032), RoundRating(date=date(2021, 7, 25), rating=1040), RoundRating(date=date(2021, 7, 11), rating=1024),
            RoundRating(date=date(2021, 7, 11), rating=1038), RoundRating(date=date(2021, 7, 11), rating=1067), RoundRating(date=date(2021, 7, 4), rating=997),
            RoundRating(date=date(2021, 7, 4), rating=1052), RoundRating(date=date(2021, 6, 26), rating=1031), RoundRating(date=date(2021, 6, 26), rating=1064),
            RoundRating(date=date(2021, 6, 26), rating=1052), RoundRating(date=date(2021, 6, 26), rating=1061), RoundRating(date=date(2021, 6, 26), rating=1065),
            RoundRating(date=date(2021, 6, 6), rating=1058), RoundRating(date=date(2021, 6, 6), rating=1046), RoundRating(date=date(2021, 6, 6), rating=1040),
            RoundRating(date=date(2021, 5, 30), rating=1061), RoundRating(date=date(2021, 5, 30), rating=1068), RoundRating(date=date(2021, 5, 30), rating=1013),
            RoundRating(date=date(2021, 5, 16), rating=1024), RoundRating(date=date(2021, 5, 16), rating=1031), RoundRating(date=date(2021, 5, 16), rating=1031),
            RoundRating(date=date(2021, 5, 1), rating=1008), RoundRating(date=date(2021, 5, 1), rating=1008), RoundRating(date=date(2021, 5, 1), rating=1027),
            RoundRating(date=date(2021, 5, 1), rating=1067), RoundRating(date=date(2021, 4, 25), rating=1029), RoundRating(date=date(2021, 4, 25), rating=1019),
            # This record was removed because it was > 2.5sd below average.
            RoundRating(date=date(2021, 4, 25), rating=970),
            RoundRating(date=date(2021, 4, 18), rating=1065), RoundRating(date=date(2021, 4, 18), rating=1050), RoundRating(date=date(2021, 4, 18), rating=1027),
            RoundRating(date=date(2021, 4, 10), rating=1009), RoundRating(date=date(2021, 4, 10), rating=1006), RoundRating(date=date(2021, 4, 10), rating=987),
            RoundRating(date=date(2021, 3, 28), rating=1026), RoundRating(date=date(2021, 3, 28), rating=1072), RoundRating(date=date(2021, 3, 28), rating=1019),
            RoundRating(date=date(2021, 3, 21), rating=1015), RoundRating(date=date(2021, 3, 21), rating=1028), RoundRating(date=date(2021, 3, 21), rating=1048),
            RoundRating(date=date(2021, 3, 14), rating=996), RoundRating(date=date(2021, 3, 14), rating=1043), RoundRating(date=date(2021, 3, 14), rating=989),
            RoundRating(date=date(2021, 2, 28), rating=1082), RoundRating(date=date(2021, 2, 28), rating=1028), RoundRating(date=date(2021, 2, 28), rating=1041),
            RoundRating(date=date(2021, 2, 28), rating=1046), RoundRating(date=date(2020, 11, 15), rating=1085), RoundRating(date=date(2020, 11, 15), rating=1027),        
            RoundRating(date=date(2020, 11, 15), rating=1003), RoundRating(date=date(2020, 11, 1), rating=1002), RoundRating(date=date(2020, 11, 1), rating=1032),
            RoundRating(date=date(2020, 11, 1), rating=1018), RoundRating(date=date(2020, 10, 3), rating=1006), RoundRating(date=date(2020, 10, 3), rating=1051),
            RoundRating(date=date(2020, 10, 3), rating=999)
        ]
        expected_included = sorted(round_ratings[:48] + round_ratings[49:], key=lambda e: (e.date, e.rating))
        expected_rating = 1036
        r = Rating()
        r.update(round_ratings, date(2021, 10, 12))
        self.assertEqual(expected_rating, r.rating)
        self.assertListEqual(expected_included, r.included)

if __name__ == '__main__':
    unittest.main()