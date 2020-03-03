import time
import feedparser
from urllib.parse import urlencode
import matplotlib.pyplot as plt


# TODO: generalize to multiple queries in a single call
# TODO: check that the query is valid via the first call

def print_help():
    print(
        """
        Collects stats about the yearly popularity of keywords on arxiv.
        For a detailed description of the possible query structures, see https://arxiv.org/help/api/user-manual#query_details
        Example of valid queries:
                                 ti:electron
                                 abs:dropout OR au:hinton
                                 all:"linear regression"
                                 cat:cs.AI OR cat:cs.LG
                                 (all:"variational autoencoder" OR all:VAE) AND cat:stat.ML
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


def collect_entries(params):
    params["sortBy"] = "lastUpdatedDate"
    params["sortOrder"] = "ascending"
    params["start"] = 0
    params["max_results"] = 1
    # checking the total number of entries
    tic = time.time()
    print("Querying arxiv API")
    parsing_result, _ = collect_slice(params)
    total_number_of_entries = int(parsing_result["feed"]["opensearch_totalresults"])
    print("Total number of entries to collect:", total_number_of_entries)
    if total_number_of_entries > 50000:
        print("! Too many entries - reformat your query.")
        return
    # collect all the entries
    all_entries = []
    params["max_results"] = 1000
    while len(all_entries) < total_number_of_entries:
        _, entries = collect_slice(params)
        all_entries += entries
        n = len(all_entries)
        print("{} / {} ({:.1f} %) entries collected in {:.2f} seconds".format(n, total_number_of_entries,
                                                                              100 * n / total_number_of_entries, time.time() - tic))  #, end="")
        params["start"] = len(all_entries)
        time.sleep(3)  # do not solicit the server too much
    return all_entries


def get_dates_from_entries(entries):
    print("Extract dates from entries")
    raw_dates = [e["published_parsed"] for e in entries]
    dates = [(d.tm_year, d.tm_mon, d.tm_mday) for d in raw_dates]
    return dates


def generate_histogram_data(dates):
    years = [d[0] for d in dates]
    year_min = min(years)
    year_max = max(years)
    hist_data = []
    for year in range(year_min, year_max + 1):
        count = years.count(year)
        hist_data.append((year, count))
    return hist_data


def plot_histogram(params, hist_data):
    years = [year for year, _ in hist_data]
    counts = [count for _, count in hist_data]
    plt.figure()
    plt.title("Popularity on arxiv")
    plt.bar(years, counts, label=params["search_query"])
    plt.ylabel("number of papers")
    plt.legend()
    plt.show(block=True)


if __name__ == "__main__":
    print_help()
    query = input("> enter your query: ")
    # query = '(all:"variational autoencoder" OR all:VAE) AND cat:stat.ML'
    parameters = {"search_query": query}
    entries = collect_entries(parameters)
    dates = get_dates_from_entries(entries)
    hist_data = generate_histogram_data(dates)
    print("stats:", hist_data)
    plot_histogram(parameters, hist_data)
