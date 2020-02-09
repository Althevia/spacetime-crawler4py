import re
from urllib.parse import urlparse
from urllib.request import urlopen
from lxml import html
from htmlParser import GoodTextParser
import shelve
import hashlib
import urllib.robotparser

# Load existing save file, or create one if it does not exist.
#wordCounts = shelve.open("wordCounts.shelve")
#uniqueURLs = shelve.open("uniqueURLs.shelve")

#Pages to avoid, due to traps or other reasons
blacklist = []
#Robots.txt disallows
#disA = ["https://www.ics.uci.edu/~mpufal/","https://www.ics.uci.edu/bin/"]
robotTxts = ["https://www.ics.uci.edu/robots.txt","https://today.uci.edu/robots.txt","https://www.cs.uci.edu/robots.txt",
    "https://www.informatics.uci.edu/robots.txt","https://www.stat.uci.edu/robots.txt"]
#Issues
badPhrases = ["/pdf/",".pdf","/?ical=1","/calendar/","format=xml","replytocom","wp-json","?share=google-plus","?share=facebook","?share=twitter"]

rpList = [] #List to hold robot parsers
rp = urllib.robotparser.RobotFileParser()
for r in robotTxts:
    rp.set_url(r)
    rp.read()
    rpList.append(rp)

def scraper(url, resp, wordCounts, uniqueURLs):
    if 399 < resp.status < 609:
        return list()
    tokenize(url, wordCounts, uniqueURLs)
    links = extract_next_links(url, resp, uniqueURLs)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp, uniqueURLs):
    # Implementation requred.
    rawHtml = resp.raw_response.content #Gets the string of the entire html document
    stringDoc = html.fromstring(rawHtml)
    linksList = list(stringDoc.iterlinks()) #List of tuples of link kind of objects
    listOfLinks = []
    for link in linksList:
        parsed = urlparse(link[2])
        fragLen = len(parsed.fragment)  #Remove the fragments
        defraggedLink = link[2][0:len(link[2])-fragLen]
        if uniqueURLs.get(defraggedLink) == None:
            #Need to check for duplicates
            uniqueURLs[defraggedLink] = 1
            listOfLinks.append(defraggedLink) #Add to list of links
    return listOfLinks

def tokenize(url, wordCounts, uniqueURLs):
    try:
        rawHtml =urlopen(url).read().decode("utf-8")
        parser = GoodTextParser()
        parser.feed(rawHtml)
    except:
        print("Exception caught in tokenize. Bad html content")
        return
    #print(parser.keptText)
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
            if wordCounts.get(token) != None:
                wordCounts[token] += 1
            else:
                wordCounts[token] = 1
            token = ""
    if token != "":
        totalWords += 1
        if wordCounts.get(token) != None:
            wordCounts[token] += 1
        else:
            wordCounts[token] = 1

    if wordCounts.get("@mostWords") == None:
        wordCounts["@mostWords"] = totalWords
        uniqueURLs["@longestURL"] = url
    elif wordCounts["@mostWords"] < totalWords:
        wordCounts["@mostWords"] = totalWords
        uniqueURLs["@longestURL"] = url
        print("NEW BIG PAGE")

def fingerprint(strText):
    pass



def is_valid(url):
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
        for rp in rpList:
            if rp.can_fetch("*",url) == False:
                return False

        return True
    except TypeError:
        print ("TypeError for ", parsed)
        raise
