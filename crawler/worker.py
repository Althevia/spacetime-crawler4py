from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import scraper
import time
import shelve
import re
from urllib.parse import urlparse

wordCounts = shelve.open("wordCounts.shelve")
uniqueURLs = shelve.open("uniqueURLs.shelve")

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                self.reportAnswers()
                break
            try:
                resp = download(tbd_url, self.config, self.logger)
                self.logger.info(
                    f"Downloaded {tbd_url}, status <{resp.status}>, "
                    f"using cache {self.config.cache_server}.")
                scraped_urls = scraper(tbd_url, resp, wordCounts, uniqueURLs)
                for scraped_url in scraped_urls:
                    self.frontier.add_url(scraped_url)
            except:
                print("Timeout error (5 seconds)")
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)

    def reportAnswers(self):
        #uniqueURLs = shelve.open("uniqueURLs.shelve")
        reportFile = open("report.txt", "w")
        print("Page with most words ("+ str(wordCounts["@mostWords"]) + "): " + uniqueURLs["@longestURL"], file = reportFile)
        print("Number of unique pages:",len(uniqueURLs)-1, file = reportFile)
        print("Fifty most common words:", file = reportFile)
        stopWords = ["a","about","above","after","again","against","all","am","an","and","any","are","aren't",
            "as","at","be","because","been","before","being","below","between","both","but","by","can't","cannot",
            "could","couldn't","did","didn't","do","does","doesn't","doing","don't","down","during","each",
            "few","for","from","further","had","hadn't","has","hasn't","have","haven't","having","he","he'd",
            "he'll","he's","her","here","here's","hers","herself","him","himself","his","how","how's","i","i'd",
            "i'll","i'm","i've","if","in","info","is","isn't","it","it's","its","itself","let's","me","more",
            "most","mustn't","my","myself","no","nor","not","of","off","on","once","only","or","other","ought",
            "our","ours","ourselves","out","over","own","same","shan't","she","she'd","she'll","she's","should",
            "shouldn't","so","some","such","than","that","that's","the","their","theirs","them","themselves",
            "then","there","there's","these","they","they'd","they'll","they've","this","those","through","to",
            "too","under","until","up","very","was","wasn't","we","we'd","we'll","we're","we've","were","weren't",
            "what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's",
            "with","won't","would","wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself",
            "yourselves","@mostWords"]
        words = 0
        sortedWords = sorted(wordCounts.items(),key=(lambda x: -x[1])) 
        index = 0
        while words != 50:
            if (not sortedWords[index][0] in stopWords):
                if (words < 49):
                    print(sortedWords[index][0],end = ", ", file = reportFile)
                else:
                    print(sortedWords[index][0], file = reportFile)
                words += 1
            index += 1
        #getting the subdomains of ics.uci.edu
        urlSubDict = dict()
        for url in uniqueURLs.keys():
            if url != "@longestURL":
                parse = urlparse(url)
                netloc = parse.netloc.lower()
                if netloc[:4] == "www.":
                    netloc = netloc[4:]
                if re.match(r"(.*\.|)ics\.uci\.edu", netloc) != None:
                    if urlSubDict.get(netloc) == None:
                        urlSubDict[netloc] = 1
                    else:
                        urlSubDict[netloc] += 1
        print("Number of unique URLs in the ics.uci.edu subdomain: " + str(len(urlSubDict)), file = reportFile)
        for key, value in sorted(urlSubDict.items()):
            print("https://" + key + ", " + str(value), file = reportFile)
        wordCounts.close()
        uniqueURLs.close()



