# We could have user timeit but I'm afraid bank will ban us for that
import time
import random
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

import utils
parser = utils.get_parser("bgp")()

NUMBER_OF_DATES = 35
date_diffs = list(range(1, NUMBER_OF_DATES + 1))
random.shuffle(date_diffs)

dates = [utils.get_date_from_date_diff(d) for d in date_diffs]


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
        future_to_date = {executor.submit(parser.get_currency, "USD", date): date for date in dates}
        for future in as_completed(future_to_date):
            data = future.result()
            q.append(data)
    finish = time.time()

    thread_pool_time = finish - start

    print("Linear time: {}".format(linear_time))
    print("Thread Pool executor time: {}".format(thread_pool_time))
    print(c)
    # TODO: what about the order? It makes no sence to get data in
    # a wrong order
    print(q)

if __name__ == '__main__':
    benchmark_multiple_downloads()
