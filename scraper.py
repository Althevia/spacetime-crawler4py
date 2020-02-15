import re
from urllib.parse import urlparse
from urllib.request import urlopen
from lxml import html
from htmlParser import GoodTextParser
import shelve
from hashlib import sha384
import urllib.robotparser
import requests
import cbor
import time
from utils.response import Response

#Pages to avoid, due to traps or other reasons
blacklist = ["https://wics.ics.uci.edu/events/","https://www.ics.uci.edu/~eppstein/pix"]
#Issues
badPhrases = ["/pdf/",".pdf",".zip",".ppt","/?ical=1","/calendar/","format=xml","replytocom",
    "wp-json","?share=google-plus","?share=facebook","?share=twitter","action=login"]
#Dictionary to hold all robot parsers
rpDict = dict()
#threshold for how similar we will allow documents (for simhash)
threshold = .95 #0.96875

def scraper(url, resp, wordCounts, uniqueURLs, uniqueFP):
    #check if the resp is a valid one
    if 399 < resp.status < 609:
        return list()
    tokenize(url, wordCounts, uniqueURLs, uniqueFP)
    links = extract_next_links(url, resp, uniqueURLs)
    return [link for link in links if is_valid(link,uniqueURLs)]

def extract_next_links(url, resp, uniqueURLs):
    rawHtml = resp.raw_response.content #Gets the string of the entire html document
    stringDoc = html.fromstring(rawHtml)
    linksList = list(stringDoc.iterlinks()) #List of tuples of link kind of objects
    listOfLinks = []
    for link in linksList:
        parsed = urlparse(link[2])
        fragLen = len(parsed.fragment)  #Remove the fragments
        defraggedLink = link[2][0:len(link[2])-fragLen]
        defraggedLink.rstrip("/")
        if uniqueURLs.get(defraggedLink) == None:
            #Need to check for duplicates
            uniqueURLs[defraggedLink] = 1
            listOfLinks.append(defraggedLink) #Add to list of links
    return listOfLinks

def tokenize(url, wordCounts, uniqueURLs, uniqueFP):
    try:
        rawHtml =urlopen(url).read().decode("utf-8")
        parser = GoodTextParser()
        parser.feed(rawHtml)
    except:
        #print("Exception caught in tokenize. Bad html content")
        return
    wordDict = dict()   #Local var to keep count of words
    totalWords = 0

    #Stolen from Annie's assignment 1 (but modified)
    token = ""
    for c in parser.keptText:
        numCode = ord(c)
        if 91 > numCode > 64:    #Checks upper case letters
            token += (c.lower())    #Converts upper to lower
        elif 123 > numCode > 96 or 47 < numCode < 58 or numCode == 39:   #Checks lower case letters or numbers or '
            token += c
        elif token != "":
            totalWords += 1
            if wordDict.get(token) != None:
                wordDict[token] += 1
            else:
                wordDict[token] = 1
            token = ""
    if token != "":
        totalWords += 1
        if wordDict.get(token) != None:
            wordDict[token] += 1
        else:
            wordDict[token] = 1

    fingerprint = simhash(wordDict)
    isGoodFP= True
    for oldfp in uniqueFP.keys():
        if similarity(fingerprint, oldfp) > threshold:
            isGoodFP = False
            #Is a duplicate
            break
    if isGoodFP:
        uniqueFP[fingerprint] = "1"
        for key, value in wordDict.items():
            #add to the wordCounts shelf
            if wordCounts.get(key) == None:
                wordCounts[key] = value
            else:
                wordCounts[key] += value
        if wordCounts.get("@mostWords") == None:
            wordCounts["@mostWords"] = totalWords
            uniqueURLs["@longestURL"] = url
        elif wordCounts["@mostWords"] < totalWords:
            wordCounts["@mostWords"] = totalWords
            uniqueURLs["@longestURL"] = url
            #New big page found

def simhash(wordDict):
    fp = [0]*384
    #Hash every word
    #For bit in word, add/sub to vector times the weight
    for word,count in wordDict.items():
        wordHash = sha384(word.encode("utf-8")).hexdigest() #Hash a hex representation
        wordHash = "{0:0384b}".format(int(wordHash,16)) #Convert hex string to binary string
        while wordHash != "":
            #add the value of the count to the correct bit position in the fp array if the bit is positive
            if wordHash[len(wordHash)-1] == "1":
                fp[len(wordHash)-1] += count
                wordHash = wordHash[:-1]
            else: #else, subtract the count
                fp[len(wordHash)-1] -= count
                wordHash = wordHash[:-1]
    #Turn all to 0 if neg, 1 if pos
    fpStr = ""
    for num in fp:
        if num < 0:
            #If neg, set bit to 0
            fpStr = fpStr + "0"
        else:
            #Else set to 1
            fpStr = fpStr + "1"
    return fpStr

#Returns percent of similarity between two strings
def similarity(str1,str2):
    i = 0
    for s in range(0,384):
        if str1[s] == str2[s]:
            i += 1
    return i/384


def is_valid(url, uniqueURLs):
    try:   
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        #Checks for right file types
        p = not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        if not p:
            return False

        #Checks for the right domains
        r = not not re.match(
            r"((.*\.|)ics\.uci\.edu)|"
            + r"((.*\.|)cs\.uci\.edu)|"
            + r"((.*\.|)informatics\.uci\.edu)|"
            + r"((.*\.|)stat\.uci\.edu)|"
            + r"((www\.|)today\.uci\.edu\/department\/information_computer_sciences)",parsed.netloc.lower())
        if not r:
            return False

        #Checks pages to avoid
        for phrase in badPhrases:
            if phrase in url:
                return False
        for l in blacklist:
            if l in url:
                return False
        try:
            #Reads robots.txt to check for disallows
            robotPage = parsed.scheme + "://" + parsed.netloc.lower() + "/robots.txt"
            config = uniqueURLs["@config"]
            if rpDict.get(robotPage) == None:
                #taken from the download method given to us but modified so we don't bypass the cache
                #a time delay added so we keep with politeness
                time.sleep(config.time_delay)
                host, port = config.cache_server
                resp = requests.get(
                    f"http://{host}:{port}/",
                    params=[("q", f"{robotPage}"), ("u", f"{config.user_agent}")],timeout=5)
                if resp:
                    rResp = Response(cbor.loads(resp.content))
                else:
                    rResp = Response({
                        "error": f"Spacetime Response error {resp} with url {robotPage}.",
                        "status": resp.status_code,
                        "url": robotPage})
                if not (399 < rResp.status < 609):
                    #make sure the page was able to be opened
                    rString = rResp.raw_response.content.decode("utf-8")
                    linesList = rString.split("\n")
                    rp = urllib.robotparser.RobotFileParser()
                    rp.parse(linesList)
                    rpDict[robotPage] = rp
            else:
                rp = rpDict.get(robotPage)
            if rp != None:
                #make sure this page is allowed to be visited from this robots.txt page
                if rp.can_fetch("*",url) == False:
                    return False
        except:
            #print("Timeout error (5 seconds):",robotPage)
            pass

        if url[-5:] == "/feed":
            return False

        return True
    except TypeError:
        print ("TypeError for ", parsed)
        raise
