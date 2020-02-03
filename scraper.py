import re
from urllib.parse import urlparse
from urllib.request import urlopen
from lxml import html

def scraper(url, resp):
    links = extract_next_links(url, resp)
    #print(url)
    #print(is_valid(url))
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation requred.
    #get the actual document html text
    rawHtml = urlopen(url).read()
    stringDoc = html.fromstring(rawHtml)
    linksList = list(stringDoc.iterlinks())
    return [link[2] for link in linksList]

def is_valid(url):
    try:   
        #^(.*\.|)ics\.uci\.edu(|(\/|#|\?).*)$
        #^(.*\.|)cs\.uci\.edu(|(\/|#|\?).*)$
        #^(.*\.|)informatics\.uci\.edu(|(\/|#|\?).*)$
        #^(.*\.|)stat\.uci\.edu(|(\/|#|\?).*)$
        #^(www\.|)today\.uci\.edu\/department\/information_computer_sciences(|(\/|#|\?).*)$
        parsed = urlparse(url)
        #print(parsed.netloc.lower())
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
        r = not not re.match(
            r"((.*\.|)ics\.uci\.edu)|"
            + r"((.*\.|)cs\.uci\.edu)|"
            + r"((.*\.|)informatics\.uci\.edu)|"
            + r"((.*\.|)stat\.uci\.edu)|"
            + r"((www\.|)today\.uci\.edu\/department\/information_computer_sciences)",parsed.netloc.lower())
        #print(p, r)
        return p and r
    except TypeError:
        print ("TypeError for ", parsed)
        raise
