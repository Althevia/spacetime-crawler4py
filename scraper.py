import re
from urllib.parse import urlparse
from urllib.request import urlopen
from lxml import html

def scraper(url, resp):
    if 399 < resp.status < 607:
        return list()
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation requred.
    rawHtml = urlopen(url).read() #Gets the string of the entire html document
    stringDoc = html.fromstring(rawHtml)
    linksList = list(stringDoc.iterlinks()) #List of tuples of link kind of objects
    return [link[2] for link in linksList] #Creates a list of links from all the tuples in linksList

def is_valid(url):
    try:   
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        p = not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()) 
        #Checks for the right domains
        r = not not re.match(
            r"((.*\.|)ics\.uci\.edu)|"
            + r"((.*\.|)cs\.uci\.edu)|"
            + r"((.*\.|)informatics\.uci\.edu)|"
            + r"((.*\.|)stat\.uci\.edu)|"
            + r"((www\.|)today\.uci\.edu\/department\/information_computer_sciences)",parsed.netloc.lower())
        return p and r
    except TypeError:
        print ("TypeError for ", parsed)
        raise
