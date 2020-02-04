from html.parser import HTMLParser

class GoodTextParser(HTMLParser):
	keptText = ""	#Parsed for relevant text

    def handle_starttag(self, tag, attrs):
        tempStr = ""
        isDesc = False
        for atter in attrs:
            if (atter[0] == "name" and atter[1] == "description"):
                isDesc = True
            if atter[0] == "content":
                tempStr += atter[1]
        if (isDesc):
            keptText += " " + tempStr

    def handle_data(self, data):
        keptText += " " + data