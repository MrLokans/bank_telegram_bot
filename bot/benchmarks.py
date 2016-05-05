# We could have user timeit but I'm afraid bank will ban us for that
import time
import random
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

import utils
parser = utils.get_parser("bgp")()

NUMBER_OF_DATES = 20
date_diffs = list(range(10, NUMBER_OF_DATES + 1))
random.shuffle(date_diffs)

dates = [utils.get_date_from_date_diff(d) for d in date_diffs]


def result_date_saver(parser, currency, date):
    return (date, parser.get_currency(currency, date))


def benchmark_multiple_downloads():
    start = time.time()
    c = [parser.get_currency(currency_name="USD",
                                 date=d)
         for d in dates]

    finish = time.time()

    linear_time = finish - start

    q = deque()
    start = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_date = {executor.submit(result_date_saver,
                                          parser,
                                          "USD", date): date
                          for date in dates}
        for future in as_completed(future_to_date):
            data = future.result()
            q.append(data)
    finish = time.time()

    thread_pool_time = finish - start

    print("Linear time: {}".format(linear_time))
    print("Thread Pool executor time: {}".format(thread_pool_time))
    sorted_curs = utils.sort_by_value(q, dates)

    for lin, threaded in zip(c, sorted_curs):
        print("{}  -  {}\n".format(lin, threaded))

    # TODO: check asyncio and gevent


def benchmark_parsing_methods():
    """Checks whether usage of lxml speed ups parsing"""
    global dates
    dates = dates[:]
    html_parser = utils.get_parser("bgp")(parser="html.parser")
    lxml_parser = utils.get_parser("bgp")(parser="lxml")

    html_start = time.time()
    c = [html_parser.get_currency(currency_name="USD",
                                  date=d)
         for d in dates]
    html_finish = time.time()
    lxml_start = time.time()
    # TODO: network factor affects a lot, perhaps we should preliminary
    # get all response texts and then test parsing with them
    c = [lxml_parser.get_currency(currency_name="USD",
                                  date=d)
         for d in dates]
    lxml_finish = time.time()

    print("LXML avg. time: {}".format((lxml_finish - lxml_start) / len(dates)))
    print("HTML avg. time: {}".format((html_finish - html_start) / len(dates)))

if __name__ == '__main__':
    benchmark_multiple_downloads()
    # benchmark_parsing_methods()
