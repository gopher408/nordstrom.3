# -*- coding: utf-8 -*-
"""
Created on Wed Aug 03 11:01:25 2016

@author: raysun
"""

import banter_nltk as banter

import numbers, os, re, sys

file_folder = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(file_folder, '..'))
sys.path.insert(0, file_folder)

import math, nltk, os, random

from nltk.tokenize import MWETokenizer

from config.banter_config import BanterConfig
from communication.echo import Echo
from datastore.dummy_datastore import DummyDataStore
import json

shortwords = {'lol': 'laugh out loud', 'btw': 'between', 'cuz': 'cause', 'ttyl': 'talk to you later',
              'brb': 'be right back', 'l8r': 'later', 'ur': 'your', 'omg': 'oh, my god', 'kinda': 'kind of',
              'plz': 'please', 'da': 'the', 'idk': "I don't know", 'Np': 'No problem'}

emoticons = {':-)': 'happy', ':-(': 'sad', ';-)': 'wink', '\o/': 'Yay, yay', ':-o': 'surprise', ':-w': 'waiting',
             ':-D': 'big grin'}

basic_colors = [
            "black",
            "blue",
            "brown",
            "cyan",
            "gray",
            "green",
            "indigo",
            "magenta",
            "orange",
            "pink",
            "purple",
            "red",
            "violet",
            "white",
            "yellow",
        ]

global_dict = ["ralph lauren", "polo shirt", "6 inch", "old fashion", "old fashioned", "in stock", "zip code", "palo alto", "walnut creek",
        "san bruno", "san mateo", "santa clara", "san jose","san francisco","hewlett packard","microsoft surtfaces","microsoft surface",
        "home theaters", "home theater","remote controllers","remote controller","digital cameras","digital camera", "broadway plaza",
        "hard drives", "hard drive", "blue rays", "blue ray", "flat panel", "high definition", 'trouble shoot', 'stoneridge mall',
        "microsoft offices", "microsoft office", "windows 10", "win 10", "windows 7", "win 7", "smart tvs", "smart tv",
        "personal computers","personal coumpter", "sky blue", "pacific blue", "suger plum",
        "t shirt", "t shirts","new year","martin luther king", "martin luther king jr.", "presidents day",
        "st. patrick","saint patrick","memorial day","independence day", "july 4th","july forth","jul 4th","labor day",
        "colmbus day","thanksgiving day","christmas eve", "no one", "best buy",
        "expect to", "like to", "need to", "want to", "this morning", "this afternoon", "this evening", "flower girls", "flower girl",
        "expects to", "likes to", "needs to", "want to", "young adults", "young adult", "close to", "right now",
        "expected to", "liked to", "needed to", "wanted to", "what time", "how much", "how late", "how early", "how soon","how long",
        "lunch time", "lunch break", "lunch hour", "lunch hours", "short sleeve", "long sleeve", "how expensive", "how costly", "how cheap"]

abbr = {"I'm": "I am", "I'd": "I would", "You're": "You are", "We're": "We are", "<":"below", "<=":"below",">":"above",">=":"above","=":"equal","~":"about"}

neglist = {"ai'nt": "are not", "are'nt": "are not", "isn't": "is not", "wasn't": "was not", "weren't": "were not",
           "haven't": "have not", "hasn't": "has not", "hadn't": "had not", "sha'nt": "shall not", "shouldn't": "should not",
           "won't": "will not", "wouldn't":"would not","don't": "do not", "doesn't": "does not", "didn't": "did not" }

exts = [',', '.', '!', '?']

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

class BanterThinker:
    def __init__(self, banter_config, communication, datastore):
        self.communication = communication
        self.datastore = datastore
        self.query = None 
        self.banter_config = banter_config
        self.trees = None
        self.datastore_request = []
        self.answer = None 
        self.missed = []
        self.dict = None 

    def load_dict(self,dict):
        dict.sort(key=lambda item:(-len(item),item))
        self.dict = dict

    def get_dict(self):
        return self.dict

    def set_query(self, query):
        self.query = query

    def get_query(self):
        return self.query

    def reset_query(self):
        self.query = ''

    def set_datastore_request(self, datastore_request):
        self.datastore_request = datastore_request

    def get_datastore_request(self):
        return self.datastore_request

    def reset_datastore_request(self):
        self.datastore_request = None

    def set_answerData(self, answerData):
        self.answerData = answerData

    def get_answerData(self):
        return self.answerData

    def reset_answerData(self):
        self.answerData = None

    def set_missed(self, words):
	self.reset_missed()
        for word in words.split():
            self.missed.append(word)

    def get_missed(self):
        if len(self.missed) > 0:
           return self.missed
        else:
           return []

    def reset_missed(self):
        self.missed = []

    def lookup(self, query, dict):
        self.load_dict(dict)
        text = query.lower()
	ques =  text.split()
        for terms in self.get_dict():
	    terms = terms.lower()
	    items = terms.split()
            temp = []  
            if terms in text:
               words = list(set(items).intersection(ques))
# RHS: to fix the bug of "close to" matched to "close tonight"
	       if len(words) == len(items): 
                  buf = '_'.join(items)
                  text = text.replace(terms, buf)
        self.set_query(text)
        #        print self.get_query()
        return self.get_query()

    def evaluate(self, text):
        tokenizer = MWETokenizer()
        res = tokenizer.tokenize(text.split())
        return res

    def normalize_message(self, message):
        message = message.strip().replace(u'\u2019s', "")
        message = message.strip().replace(u'\u2019', "")
# RHS: abbreviation will be converted to the original form by calling convert_abbr
#        message = message.strip().replace("'", "")
        message = message.strip().replace("\"", "")
        return message

    def convert_abbr(self,words):
        buf = []
        for word in words:
            lword = word
            if lword in abbr:
               #        print lword, abbr[lword]
               for term in abbr[lword].split():
                   buf.append(term.lower())
            else:
               buf.append(word.lower())
        return buf

    def convert_neglist(self,words):
        buf = []
        for word in words:
            lword = word.lower()
            if lword in neglist:
                #       print lword, neglist[lword]
               for term in neglist[lword].split():
                   buf.append(term.lower())
            else:
               buf.append(word.lower())
        return buf

    def check_endword(self, words):
        if len(words) > 0:
           buf = []
           for word in words:
               if word[-1] in exts:
                  word = word[:-1]
               buf.append(word)
           words = buf
        return words


    def performNLP(self, dict, message,test=False):
        query = message
        if test == True:
           # tokenization of message
           message = self.normalize_message(message)
#           print message
           words = self.evaluate(message)
#           print words
           words = self.convert_abbr(words)
#           print words
           words = self.convert_neglist(words)
#           print words
           words = self.check_endword(words)
#	   print words
           query = ' '.join(words)
           self.set_query(query)


    def parse_query(self, dict, query, test=False, limits=None):
        query0 = query
        self.reset_datastore_request()
        print 'INPUT:' + query
# RHS: turn this on for standalone grammar test
        self.performNLP(dict,query,test) 
        query = self.get_query()
#        print query
#        #	 nltk.data.show_cfg(self.banter_config.get_grammer_file())
#        words = str(query).split()
#        if words[-1][-1] in exts:
#            words[-1] = words[-1][:-1]
#        buf = []
#        for word in words:
#	    if word[-1] in exts:
#               word = word[:-1]
#            buf.append(word)
#        words = buf
#        print words
#        query = ' '.join(words)
#        print query
#        self.set_query(query)
#        #	 print 'NLP: ' + query
#        #        print 'NLP: '
#        #        print query.split()
        cp = nltk.load_parser(self.banter_config.get_grammer_file())
        try:
            if len(query.split()) == 0:
               self.trees = list(cp.parse(list(query)))
            else: 
               self.trees = list(cp.parse(query.split()))
        except ValueError:
            print "ERROR_CODE': 'DID_NOT_UNDERSTAND 1'"
            self.set_datastore_request('')
            return {'ERROR_CODE': 'DID_NOT_UNDERSTAND'}
        if self.trees == []:
            print "ERROR_CODE': 'DID_NOT_UNDERSTAND 2'"
            self.set_datastore_request('')
            return {'ERROR_CODE': 'DID_NOT_UNDERSTAND'}
        try:
            print "Grammar not matched!"
            warning = ''.join(self.trees)
#            print warning
            if "Error" in warning:
                words = warning.split('words:')[1:]
#                print words
                if words[-1][-1] in exts:
                    words[-1] = words[-1][:-1]
#		print words
                missing = ''.join(words)
                missing = missing.replace('u\"','')
                missing = missing.replace('u\'', '')
                missing = missing.replace(',',  '')
#                missing = missing.replace('".', '')
                missing = missing.replace('"', '')
                missing = missing.replace('\'', '')
                missing = missing[1:]
		print "Missing words = \"" + missing + "\"" 
   	        self.set_missed(missing)
#                print self.get_missed()
		if query != query0:
                   self.parse_query(dict, query, test, limits)
                else:
                   self.datastore_request['lost'] = lost 
                   self.set_datastore_request(self.datastore_request)
#                   self.reset_missed()
                   return self.get_datastore_request()
        except:
#            print self.trees[0]
            print "Grammar matched!"
            temp = None
            try:
                temp = self.trees[0].label()['SEM']
            except:
                pass
            if not isinstance(temp, (list, tuple)):  # hack so this is always a list
                temp = [temp]
            temp = [s for s in temp if s]

            datastore_request = {}
            for field in temp:
                parts = field.split('=')
# RHS: to avoid duplicate
                if parts[0] in datastore_request:
		    item = parts[1].replace('"','') 
		    if item not in datastore_request[parts[0]].split(','):
                       datastore_request[parts[0]] += ',' + item
                else:
                    datastore_request[parts[0]] = parts[1].replace('"', '')
# RHS: to generate action of 'ask time'. This is not accurate yet. Need to specify more conditions
            if 'descriptor' in datastore_request and 'datetime' in datastore_request: 
	       items = datastore_request['descriptor'].split(',')
	       buf = []
               for item in items:
                   if item in ['this','next']:
                      datastore_request['datetime'] = item + ',' + datastore_request['datetime']
                   else:
                      buf.append(item)
               datastore_request['descriptor'] = ','.join(buf) 
            elif 'descriptor' in datastore_request:
	       items = datastore_request['descriptor'].split(',')
               for item in items:
                  if item in ['open','close','until']:
                     if 'action' not in datastore_request: 
                        datastore_request['action'] = 'ask time'
            elif 'datetime' in datastore_request:
               if len(datastore_request['datetime']) > 0:
                  if 'action' not in datastore_request: 
                     datastore_request['action'] = 'ask time'
# RHS: to generate action of 'find store'
	    elif 'datetime' not in datastore_request: 
               if 'store' and 'location' in datastore_request:
                  if 'action' not in datastore_request and 'datetime' not in datastore_request:
                     datastore_request['action'] = 'find store'
            if limits != None:
                if isinstance(limits, int):
                    datastore_request['LIMIT'] = limits
                    #           print 'INTENT: ' + datastore_request
            self.set_datastore_request(datastore_request)
#            print 'INTENT: ' + str(self.get_datastore_request())
            return self.get_datastore_request()

        return self.get_datastore_request()


    # This code has to be modified to current settings
    def submit_query(self):
#        assert self.get_datastore_request(),  'we should have datastore_request data'
        if self.datastore_request == None or len(self.get_datastore_request()) == 0:
           print "Datastore_request: " + str(self.get_datastore_request())
           return {'ERROR_CODE': 'DID_NOT_UNDERSTAND'}

        lost = self.get_missed()
        if len(lost) > 0:
           price = []
           for word in lost:
	       word = word.replace(',','')
               if word[0] in ['>','<']:
                  nword = word[1:len(word)]
                  if re.search("^\${0,1}\d+(\.\d*){0,1}",nword) != None:
                     if is_number(nword):
                        nword = '$' + nword
                     nword = word[0] + nword
                     price.append(nword) 
	       else:
                  if re.search("^\${0,1}\d+(\.\d*){0,1}",word) != None:
		     if is_number(word):
                     	price.append('$'+word) 
                     else:
			price.append(word) 

           if len(price) > 0:
              self.datastore_request['price'] = price
	      lost1 = []
              for item in lost:
                  item1 = item.replace(',','')
                  item1 = item1.replace('$','')
	          lost1.append(item1)
	      price1 = []
              for item in price:
                  item1 = item.replace(',','')
                  item1 = item1.replace('$','')
                  price1.append(item1)                 
              lost = list(set(lost1)-set(price1))
              self.set_missed(' '.join(lost))
              lost = self.get_missed()

        self.datastore_request['lost'] = lost

        '''  RAY is this right, do we want to check if this was an answer or a question
             the test case for this is 'is there a store near me?  answer: alaska
        if len(lost) > 0:
            self.reset_missed()
            return {'ERROR_CODE': 'UNKNOWN_WORDS', 'lost': lost}
        '''

        answerData = self.datastore.search(self.datastore_request)
        if 'ERROR_CODE' in answerData:
            return answerData
            # FVZ is this right? search may not find anything or have an error, do we reset the query

# RHS: clean up missing words here -- don't want to carry over to next query
        self.reset_missed()

        self.reset_query()
        self.reset_answerData()

        # print 'OUTPUT (NLG): ' + self.get_answer()
        self.set_answerData(answerData)
        return self.get_answerData()



if __name__ == "__main__":
    # configure banter thinker
    grammarConfig = BanterConfig('Nordstrom', 'case12.fcfg')
    nlu = banter.BanterThinker(grammarConfig, Echo(), DummyDataStore())
    dict = global_dict
    query = ""
    test = True
    limits = None

# RHS20160827
    query = "Is there a store near me?"
    query = "Is there a store nearby"
    query = "Is there a Nordstrom in San Francisco?"
    query = "Where is the nearst Nordstrom in San Francisco?"
    query = "Is there any Nordstrom close to San Francisco?"
    query = "Find a Nordstrom store nearby"
    query = "Help to find the closest Nordstrom"
    query = "Help find the closest Nordstrom"
    query = "Can you help me find a Nordstrom in San Francisco"
    query = "Can you help me find a the nearest Nordstrom in San Francisco"  # test bogus word
    query = "Can I get the direction to a Nordstrom in San Francisco"
    query = "Is there any Nordstrom store close to San Francisco?"
    query = "How can I get to a Nordstrom in San Francisco"
    query = "How can I find a Nordstrom in San Francisco"
    query = "What is the closest Nordstrom in San Francisco"
    query = "What is the nearest Nordstrom store in Palo Alto?"
    query = "Are you in Palo Alto?"
    query = "Does Palo Alto have a Nordstrom?" 
    query = "Is there a store near me?"
    query = "Can you direct me to a Nordstrom in San Francisco"
    query = "Palo Alto Nordstrom?" 
    query = "Palo Alto store?" 
    query = "Juno, Alaska"
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query() 

    query = "What time is Richfield open until?"
    query = "What time is Alska open until?"
    query = "When is Alska open until?"
    query = "what are Richfield's hours today"
    query = "When will Stanford store be close tonight?"
    query = "How late will the store be open today"
    query = "How late will Richfield store be open today"
    query = "How late will the Richfield store be open today"
    query = "How late does the Richfield store open today"
    query = "How late does Richfield store open today"
    query = "How late does the store open today"
    query = "What time does it open tomorrow?"
    query = "Reset"
    query = "55 Vizio"
    query = "Mac"
    query = "Red"
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query()

# RHS20160828
    query = "What time does it open tomorrow?"
    query = "What time do you open?"
    query = "What time do you close tonight?" # to solve "close to" and "close tonight"
    query = "What time does Palo Alto store open tomorrow?"
    query = "Do you open Monday night?"
    query = "Is Nordstrom Palo Alto open now?"
    query = "How late do you open Tuesday night?"
    query = "Do you open right now?"
    query = "Does Palo Alto store open now?"
    query = "Is there a store open now?"
    query = "Hours?"
    query = "What time is Palo Alto Nordstrom open until?"
    query = "Opening time?"
    query = "Open time?"
    query = "Open?"
    query = "Closing time?"
    query = "close time?"
    query = "Close?"
    query = "Can I go there now?" # this sentence does not ask time!
    query = "Can I shop there now?" # this sentence does not ask time!
    query = "When are you open next Tuesday?"
    query = "When are you open this week?"
    query = "When are you open until?"
    query = "How early are you open tomorrow"
    query = "How late are you close tonight"
    query = "How soon will you have it in stock?"
    query = "How long before you close"
    query = "How long before you open tomorrow"
    query = "Hi"
    query = "Hello"
    query = "Help!"
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query()

    query = "What time does it open tomorrow?"
    query = "I’d like to buy a new dress"
    query = "I am looking for red boots"
    query = "I am looking for a"
    query = "I'm looking for some red boots."
    query = "I'm looking for some redd botts." # to test missing words
    query = "I'm looking in for some red boots." # to test bogus words
    query = "I am looking for red boots with a" # to test incomplete sentence
    query = "How much I'm looking for some red boots." # to test variation
    query = "I shot an elephant in my pajama."
    query = "I shot elephants in my pajamas."
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query()

    query = "I need a new dress for a wedding"
    query = "I need a new dress for old fashioned day"
    query = "I'm looking for some old fashioned dresses"
    query = "Do you have any pink dress with buckle"
    query = "I need some blue comfort shoes"
    query = "I need some old fashioned purple comfort shoes with buckle"
    query = "I am looking for boots"
    query = "I need some black boots"
    query = "I need black boots"
    query = "Do you have any black boots?"
    query = "Do you have black boots?"
    query = "I want a t-shirt"
    query = "I want a red dress"
    query = "I would like to buy a new dress"
    query = "I like to buy a white shirt"
    query = "I'm looking for some blue skirts"
    query = "I like to see some red boots"
    query = "I am interested to buy some red shoes"
    query = "I am looking for a short polo"
    query = "I am looking for a polo shirt"
    query = "I am looking for a sport shirt"
    query = "I am looking for an oxford short sleeve polo"
    query = "I am looking for tall dress boots like the first one."
    query = "I am looking for more tall dress boots like the third one."
    query = "I need new white shoes"
    query = "Size 12 in black"
    query = "What is the price?" 
    query = "How expensive is that boot?" 
    query = "Between $70 and $100"
    limits = 3
    datastore_request = nlu.parse_query(dict, query, test, limits)
    nlu.submit_query()

# RHS20160827
    query = "I need a dress"
    query = "I want some shoes"
    query = "Black dresses"
    query = "I am shopping for new boots"
    query = "I'm looking for some red boots."
    query = "Find me some purple cocktail dresses."
    query = "Do you have toddler flower girl dresses?"
    query = "I like to buy gucci handbags"
    query = "I like to see some gucci handbags"
    query = "Help me find some brown shoes"
    query = "Show me some purple shoes"
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query()

    query = "Can I see more like the first one"
    query = "Do you have more like the first one?"
    query = "I'm looking for tall dress boots like the first one"
    query = "I am looking for tall dress boots like the first one"
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query()

    query = "More like the first one"
    query = "More like the gucci"
    query = "More like the gucci one"
    query = "More like the blue one"
    query = "I like the first one"
    query = "I like the gucci"
    query = "I like the gucci one"
    query = "I like the blue one"
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query()

    query = "How much for the first one"
    query = "How much for the gucci"
    query = "Do you have the second one in a large"
    query = "Do you have the gucci in size 4"
    query = "Do you have that in stock"
    query = "Do you have it in black"
    query = "Do you have that in a large"
    query = "Do you have that in red"
    query = "Do you have that in size 4"
    query = "Can I see more?"
    query = "Can I see the gucci?"
    query = "Can I see that in black"
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query()

    query = "I am looking for the ralph lauren white polo shirt"
    query = "I am looking for a gucci handbag"
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query()

    # This is for V2
    query = "Do you have something like the gucci in black"
    query = "What about something in a 6 inch heel"
#    limits = 3
#    datastore_request = nlu.parse_query(dict, query, test, limits)
#    nlu.submit_query()
