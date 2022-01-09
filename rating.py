import re, datetime, statistics, argparse, sys

def error(msg):
    """Print msg and die."""
    print(f'ERROR! {msg}')
    exit(1)

def read_ratings(file):
    """Read dates and ratings from copy-paste-from-pdga-website-ratings-detail-file.

    For each date/ratings pair in the file there must be a date on the format "[day]-[Abbr. month]-[year]" e.g.
    "5-Jun-2021" and a score+rating pair like "[score][whitespace(s)][rating]" e.g. "54   987".

    Args:
        file (str): Path to file.

    Returns:
        tuple of (list of str, list of int): Dates, ratings.
    """
    ratings = []
    with open(file, 'r') as f:
        content = f.read()
    dates = re.findall(r'\d+-[JFMAJSOND][a-v]{2}-\d{4}', content)
    ratings = [int(r) for r in re.findall(r'\s+\d+\s+(\d+)', content)]
    if len(dates) != len(ratings):
        error('Dates and ratings from file have different length.')
    return dates, ratings

def remove_indeces(list, indeces):
    """Remove items with indeces from list.
    
    Args:
        list (list): The list to remove items from.
        indeces (list of int): The indeces to remove from list.
    """
    for i in sorted(indeces, reverse=True):
        del list[i]

def remove_outside_date_range(dates, ratings, calc_date):
    """Remove ratings that are too old or too recent.
    
    Args:
        dates (list): Dates with format (D)D-Mon-YYYY.
        ratings (list): Corresponding ratings.
        calc_date (datetime): Date at where the calculation takes place (usually last day in a month).
    """
    indeces = []
    period = 12 if len(dates) >= 8 else 24
    for i, date in enumerate(dates):
        try:
            d = datetime.datetime.strptime(date, '%d-%b-%Y')
        except ValueError:
            error(f"Wrong date format: {date}.")
        if ((calc_date.year - d.year) * 12 + calc_date.month - d.month) > period or d.toordinal() > calc_date.toordinal():
            indeces.append(i)
    remove_indeces(ratings, indeces)
    if period == 24 and len(dates) > 8:
        ratings = ratings[:8]

def remove_outliers(ratings):
    """Remove ratings that are more than 100pts or 2.5sd below average (if 7 or more rounds available).
    
    Args:
        ratings (list): Ratings.
    """
    if len(ratings) < 7:
        return
    avg = statistics.mean(ratings)
    sd = statistics.stdev(ratings)
    indeces = []
    for i, rating in enumerate(ratings):
        diff = avg - rating
        if diff > sd * 2.5 or diff > 100:
            indeces.append(i)
    remove_indeces(ratings, indeces)

def double_latest_fourth(ratings):
    """Insert the latest 25% of the rounds twice (if 8 or more rounds available).
    
    Args:
        ratings (list): Ratings.
    """
    if len(ratings) < 8:
        return
    count = round(len(ratings) / 4)
    for i in range(count):
        ratings.append(ratings[i])

def parse_args(args):
    parser = argparse.ArgumentParser(description="Calculate PDGA player rating.")
    parser.add_argument('-f', '--file', help='Copy/paste from PDGA player statistics page.', metavar='FILE')
    parser.add_argument('-r', '--ratings', help='List of ratings.', nargs='*', metavar='RATING')
    parser.add_argument('-d', '--dates', help='List of dates (DD-Mon-YYYY) for corresponding ratings.', nargs='*', metavar='DATE')
    parser.add_argument('-c', '--calc-date', help="Day (DD-Mon-YYYY) to calculate rating from. Default: End of last month.")
    return parser.parse_args(args)

if __name__ == "__main__":
    cmd_dates, cmd_ratings, file_dates, file_ratings = [], [], [], []
    options = parse_args(sys.argv[1:])
    if not options.ratings and not options.file:
        error('No input given.')

    if options.dates or options.ratings:
        try:
            if len(options.dates) != len(options.ratings):
                error('Dates and ratings from command line arguments have different length.')
            cmd_dates = options.dates
            cmd_ratings = [int(r) for r in options.ratings]
        except TypeError:
            error('Ratings given without dates or vice versa.')
    if options.file:
        file_dates, file_ratings = read_ratings(options.file)
    dates = cmd_dates + file_dates
    ratings = cmd_ratings + file_ratings
    try:
        calc_date = datetime.datetime.strptime(options.calc_date, '%d-%b-%Y') if options.calc_date else datetime.datetime.today().replace(day=1) - datetime.timedelta(days=1)
    except ValueError:
        error(f"Wrong date format: {options.calc_date}.")
        

    remove_outside_date_range(dates, ratings, calc_date)
    remove_outliers(ratings)
    double_latest_fourth(ratings)
    rating = statistics.mean(ratings)
    print(round(rating))