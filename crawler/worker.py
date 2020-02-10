from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import scraper
import time
import shelve
import re
from urllib.parse import urlparse

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.wordCounts = 0
        self.uniqueURLs = 0
        self.workers = 0    #All the workers
        self.myBackupList= list()      #List of urls belonging to this worker
        self.worker_id = worker_id
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            if len(myBackupList) == 0:
                #No more worker urls, search frontier
                tbd_url = self.frontier.get_tbd_url()
                wID = urlID(tbd_url)
                if wID != self.worker_id:
                    #Not my url, give to someone else
                    self.workers[wID].addToMine(tbd_url)
                else:
                    myBackupList.append(tbd_url)
            else:
                tbd_url = myBackupList.pop(len(myBackupList)-1) #Take url belonging to this worker
                try:
                    resp = download(tbd_url, self.config, self.logger)
                    self.logger.info(
                        f"Downloaded {tbd_url}, status <{resp.status}>, "
                        f"using cache {self.config.cache_server}.")
                    scraped_urls = scraper(tbd_url, resp, self.wordCounts, self.uniqueURLs)
                    for scraped_url in scraped_urls:
                        self.frontier.add_url(scraped_url)
                except:
                    print("Timeout error (5 seconds):",tbd_url)
                self.frontier.mark_url_complete(tbd_url)
                time.sleep(self.config.time_delay)

    def addInfo(self,wordCounts,uniqueURLs,workers):
        self.wordCounts = wordCounts
        self.uniqueURLs = uniqueURLs
        self.workers = workers

    def urlID(self,url):
        parse = urlparse(url)
        netloc = parse.netloc.lower()
        if netloc[:4] == "www.":
            netloc = netloc[4:]
        wID = (chr(netloc[0]) - 97) % len(self.workers)
        return wID

    def addToMine(self,url):
        self.myBackupList.append(url)



