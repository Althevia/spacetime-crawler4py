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
        #creating variables so we can store the shelf files and pass them into scraper 
        self.wordCounts = 0
        self.uniqueURLs = 0
        self.uniqueFP = 0
        self.workers = 0    #All the workers
        self.myBackupList= list()      #List of urls belonging to this worker
        self.worker_id = worker_id
        super().__init__(daemon=True)
        
    def run(self):
        while True:            
            if len(self.myBackupList) == 0:
                #No more worker urls, search frontier
                tbd_url = self.frontier.get_tbd_url()
                if not tbd_url:
                    #if no workers are running, we want to have everyone stop running
                    checkAll = False
                    for worker in self.workers:
                        if len(worker.myBackupList) != 0:
                            #Some worker is still running
                            checkAll = True
                        if checkAll == False:
                            time.sleep(2)
                    if checkAll == False:
                        for worker in self.workers:
                            if len(worker.myBackupList) != 0:
                                #Some worker is still running! :O
                                checkAll = True
                            if checkAll != True:
                                time.sleep(2)
                    if checkAll == False:
                        break
                else:
                    wID = self.urlID(tbd_url)
                    if wID != self.worker_id:
                        #Not my url, give to someone else
                        self.workers[wID].addToMine(tbd_url)
                    else:
                        self.myBackupList.append(tbd_url)
            else:
                tbd_url = self.myBackupList.pop(len(self.myBackupList)-1) #Take url belonging to this worker
                try:
                    resp = download(tbd_url, self.config, self.logger)
                    self.logger.info(
                        f"Downloaded {tbd_url}, status <{resp.status}>, "
                        f"using cache {self.config.cache_server}.")
                    scraped_urls = scraper(tbd_url, resp, self.wordCounts, self.uniqueURLs, self.uniqueFP)
                    for scraped_url in scraped_urls:
                        self.frontier.add_url(scraped_url)
                except:
                    #print("Timeout error (5 seconds):",tbd_url)
                    pass
                self.frontier.mark_url_complete(tbd_url)
                time.sleep(self.config.time_delay)

    def addInfo(self,wordCounts,uniqueURLs,uniqueFP,workers):
        #get the shelf files stored in the __init__.py file
        self.wordCounts = wordCounts
        self.uniqueURLs = uniqueURLs
        self.uniqueFP = uniqueFP
        self.workers = workers

    def urlID(self,url):
        #used for multithreading so each thread only gets one (or 2) domains so we can remain polite
        parsed = urlparse(url)

        r = re.match(r"((.*\.|)ics\.uci\.edu)",parsed.netloc.lower())
        if r == None:
            r = re.match(r"((.*\.|)cs\.uci\.edu)",parsed.netloc.lower())
            if r == None:
                r = re.match(r"((.*\.|)informatics\.uci\.edu)",parsed.netloc.lower())
                if r == None:
                    wID = 3
                else:
                    wID = 2
            else:
                wID = 1
        else:
            wID = 0
        return wID

    def addToMine(self,url):
        self.myBackupList.append(url)



