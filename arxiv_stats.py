#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Collects stats about the yearly popularity of queries on arxiv.
Enter multiple queries separated by a semicolon (;)
Example of valid queries:
                         electron
                         au:Pearl ; ti:"gradient descent" ; all:"linear regression"
                         abs:dropout AND au:hinton ; cat:cs.AI OR cat:cs.LG
                         abs:"swarm robotics" ; (all:"variational autoencoder" OR all:VAE) AND cat:stat.ML
For a detailed description of the possible query structures, see https://arxiv.org/help/api/user-manual#query_details
"""
__author__ = "Alban Laflaquière"
__license__ = "MIT"
__version__ = "1.1"


import time
import feedparser
from urllib.parse import urlencode
try:
    import matplotlib.pyplot as plt
    plt_found = True
except ImportError:
    plt_found = False


def print_help():
    print(
        """
        Collects stats about the yearly popularity of keywords on arxiv.        
        Enter multiple queries separated by a semicolon (;)
        Example of valid queries:
                                 causality
                                 au:Pearl ; ti:"gradient descent" ; all:"linear regression"
                                 abs:dropout AND au:hinton ; cat:cs.AI OR cat:cs.LG
                                 abs:"swarm robotics" ; (all:"variational autoencoder" OR all:VAE) AND cat:stat.ML
        For a detailed description of the possible query structures, see https://arxiv.org/help/api/user-manual#query_details                         
        """
    )


def get_query_url(params):
    root_url = "http://export.arxiv.org/api/query?"
    return root_url + urlencode(params, safe=":")


def collect_slice(params):
    query_url = get_query_url(params)
    parsing_result = feedparser.parse(query_url)
    # check correct response
    if not parsing_result.get("status") == 200:
        print("HTTP error")
    entries = parsing_result["entries"]
    if len(entries) == 0:
        print("(empty response from arxiv - repeat query)")
    return parsing_result, entries


def check_query_validity(params):
    # make sure a single entry is expected
    params["max_results"] = 1
    # try the query 3 times maximum
    for trial in range(3):
        parsing_result, _ = collect_slice(params)
        total_number_of_entries = int(parsing_result["feed"]["opensearch_totalresults"])
        if total_number_of_entries > 50000:
            print("ERROR - Too many entries to fetch; make your query more specific")
            return 0
        if total_number_of_entries > 0:
            print("Total number of entries to collect:", total_number_of_entries)
            return total_number_of_entries
        time.sleep(3)
    print("ERROR - Malformed query or empty search result")
    return 0


def collect_entries(qu):
    params = {"search_query": qu,
              "sortBy": "lastUpdatedDate",
              "sortOrder": "ascending",
              "start": 0,
              "max_results": 1
              }
    # checking the query's validity and the total number of entries
    tic = time.time()
    total_number_of_entries = check_query_validity(params)
    # collect all the entries
    all_entries = []
    params["max_results"] = 1000
    while len(all_entries) < total_number_of_entries:
        _, entries = collect_slice(params)
        all_entries += entries
        n = len(all_entries)
        print("{} / {} ({:.1f} %) entries collected in {:.2f} seconds".format(n, total_number_of_entries,
                                                                              100 * n / total_number_of_entries, time.time() - tic))
        params["start"] = len(all_entries)
        time.sleep(3)  # do not solicit the server too much
    return all_entries


def get_dates_from_entries(entries):
    print("Extract dates from entries")
    raw_dates = [e["published_parsed"] for e in entries]
    dates_ym = [(d.tm_year, d.tm_mon, d.tm_mday) for d in raw_dates]
    return dates_ym


def generate_histogram_data(dates_ym):
    if len(dates_ym) == 0:
        return []
    years = [d[0] for d in dates_ym]
    year_min = min(years)
    year_max = max(years)
    h_data = []
    for year in range(year_min, year_max + 1):
        count = years.count(year)
        h_data.append((year, count))
    return h_data


def plot_histogram(labels, data):
    plt.figure()
    plt.title("Popularity on arxiv")
    year_min = 9999
    year_max = -9999
    for i, (q, d) in enumerate(zip(labels, data)):
        if len(d) == 0:
            continue
        years = [year for year, _ in d]
        year_min = min(year_min, min(years))
        year_max = max(year_max, max(years))
        counts = [count for _, count in d]
        x = [y + i * 0.8 / len(labels) - (len(labels) - 1) * 0.4 / len(labels) for y in years]
        plt.bar(x, counts, width=0.8 / len(labels), label=q)
    plt.xticks(list(range(year_min, year_max + 1)), rotation=70)
    plt.ylabel("number of papers")
    plt.legend()
    plt.show(block=True)


if __name__ == "__main__":
    print_help()
    queries = input("> enter your queries: ").strip(";").split(";")
    queries = [q.strip(" ;") for q in queries]
    all_hist_data = []
    for query in queries:
        print("--------------\nQuerying arxiv API:", query)
        collected_entries = collect_entries(query)
        dates = get_dates_from_entries(collected_entries)
        hist_data = generate_histogram_data(dates)
        print("RESULTS:\n\tQUERY:", query, "\n\tSTATS:", hist_data)
        all_hist_data.append(hist_data)
    if plt_found:
        plot_histogram(queries, all_hist_data)
