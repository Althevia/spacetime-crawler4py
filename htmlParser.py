from html.parser import HTMLParser

class GoodTextParser(HTMLParser):
    #keptText = ""	#Parsed for relevant text

    def __init__(self):
        super().__init__()
        self.keptText = ""
        self.currentTag = ""

    def handle_starttag(self, tag, attrs):
        tempStr = ""
        isDesc = False
        self.currentTag = tag
        for atter in attrs:
            if (atter[0] == "name" and atter[1] == "description"):
                isDesc = True
            if atter[0] == "content":
                tempStr += atter[1]
        if (isDesc):
            self.keptText += " " + tempStr

    def handle_data(self, data):
        if self.currentTag != "script":
            self.keptText += " " + data
