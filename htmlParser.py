from html.parser import HTMLParser

class GoodTextParser(HTMLParser):
    #keptText = ""	#Parsed for relevant text

    def __init__(self):
        super().__init__()
        self.keptText = ""
        self.currentTag = ""

    #What to do when tag is found <.*>
    def handle_starttag(self, tag, attrs):
        tempStr = ""
        isDesc = False
        self.currentTag = tag
        #adding metadata information to the text we parse
        for atter in attrs:
            if (atter[0] == "name" and atter[1] == "description"):
                isDesc = True
            if atter[0] == "content":
                tempStr += atter[1]
        if (isDesc):
            self.keptText += " " + tempStr

    #What to do with info between tags <>.*<>
    def handle_data(self, data):
        #don't want to add information that is under html style or script information
        if self.currentTag != "script" and self.currentTag != "style":
            self.keptText += " " + data
