# -*- coding: utf-8 -*-D

"""
Created on Wed Jul 13 10:52:35 2016

@title: banter_app.py

@version: 1.3

@author: raysun
"""

import banter_nltk as banter
import math, random, time, os, re, sys

file_folder = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(file_folder, '..'))
sys.path.insert(0, file_folder)

from nltk.tokenize import MWETokenizer

from config.banter_config import BanterConfig
from communication.echo import Echo
from datastore.dummy_datastore import DummyDataStore
import json, datetime, calendar
import json
import urllib
import urllib2
import requests
from datastore.aws_datastore import AWSDataStore

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

states = ['closing', 'opening', 'question', 'answer', 'thanks']

thanks = [#"Thank you for contacting us",
          "I’m happy that I was able to assist you today",
#          "It’s been a pleasure...",
          #         "You’ve been a pleasure to talk with. Have a wonderful day",
          #         "Thank you for being a great customer. We value your relationship",
          #         "Your satisfaction is a great compliment to us",
#          "Is there anything else I can help you with?",
          #         "Certainly, I’d be happy to assist you with that today",
#          "I would be more than happy to assist you today",
#          "Please let me know if I can provide any other additional support"]
	 ]

exts = ['.', '!', '?']

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

global_dict = ["ralph lauren", "polo shirt", "6 inch", "old fashion", "old fashioned", "in stock", "zip code",
               "palo alto", "walnut creek",
               "san mateo", "santa clara", "san jose", "san francisco", "hewlett packard", "microsoft surtfaces",
               "microsoft surface", "broadway plaza",
               "home theaters", "home theater", "remote controllers", "remote controller", "digital cameras",
               "digital camera", "stoneridge mall",
               "hard drives", "hard drive", "blue rays", "blue ray", "flat panel", "high definition", "trouble shoot",
               "microsoft offices", "microsoft office", "windows 10", "win 10", "windows 7", "win 7", "smart tvs",
               "smart tv",
               "personal computers", "personal coumpter", "sky blue", "pacific blue", "suger plum", "the stanford",
               "t shirt", "t shirts", "new year", "martin luther king", "martin luther king jr.", "presidents day",
               "st. patrick", "saint patrick", "memorial day", "independence day", "july 4th", "july forth", "jul 4th",
               "labor day",
               "colmbus day", "thanksgiving day", "christmas eve", "no one", "best buy",
               "expect to", "like to", "need to", "want to", "this morning", "this afternoon", "this evening",
               "flower girls", "flower girl",
               "expects to", "likes to", "needs to", "want to", "young adults", "young adult", "close to", "right now",
               "expected to", "liked to", "needed to", "wanted to", "what time", "how much", "how late", "how early",
               "how soon", "how long",
               "lunch time", "lunch break", "lunch hour", "lunch hours", "short sleeve", "long sleeve", "how expensive",
               "how costly", "how cheap"]

wh_tones = ["what", "when", "where", "which", "how", "why", "what_time", "how_much", "how_late"]

yesno_tones = ["Do", "Does", "Did", "Am", "Are", "Is", "Was", "Were", "Will", "Would", "Shall", "Should",
               "Don't", "Doesn't", "Didn't", "Ain't", "Aren't", "Wasn't", "Weren't", "Won't", "Wouldn't", "Shan't",
               "Shouldn't"]
request_tones = ["looking", "look", "need", "want", "find", "buy", "have", "sell", "like", "carry", "see"]

thanks_tones = ["Thank", "Thanks", "Appreciate", "pleasure"]

closing_tones = ["Goodbye", "Good-bye", "Bye", "bye", "Ciao", "ciao", "Adios", "adios"]


def get_timestamp():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return st


class BanterClient:
    def __init__(self, name, banter_config, communication, datastore):
        self.banter_config = banter_config;
        self.communication = communication
        self.datastore = datastore
        self.reset(name)

        self.localdict = global_dict
        with open(banter_config.get_words_file()) as f:
            lines = f.readlines()
            for line in lines:
                self.localdict.append(line.strip())

        # configure banter thinker
        self.nlu = banter.BanterThinker(banter_config, communication, datastore)

    def reset(self, name):
        global global_mesg_id
        self.name = name
        self.query = []
        self.data = []
        self.tones = [states[0]]
        self.states = [states[0]]
        self.in_text = []
        self.MesgId = 0
        self.topics = ["closing"]

    def evaluate(self, text):
        tokenizer = MWETokenizer()
        res = tokenizer.tokenize(text.split())
        return res

    def normalize_message(self, message):
        message = message.strip().replace(u'\u2019s', "")
        message = message.strip().replace(u'\u2019', "")
        message = message.strip().replace("\"", "")
        return message

    def preprocess(self, message):
        # tokenization of message
        self.nlu.performNLP(self.localdict, message, test=True)
        query = self.nlu.get_query()
        self.in_text.append(query)
        words = message.split()
        self.update_tone(words)

    def update_tone(self, words):
        prev_tone = self.get_tone()
        prev_state = self.get_state()
     	print "\n***** PRIOR STATUS *****\n"
        tmp = "Prior tone: " + str(prev_tone)
        print tmp
        top = "Prior state: " + str(prev_state)
        print top
        if len(words) > 0:
            if words[-1][-1] == '?':
                curr_tone = states[2]
            elif words[0].lower() in [item.lower() for item in wh_tones]:
                curr_tone = states[2]
            elif words[0].lower() in [item.lower() for item in yesno_tones]:
                curr_tone = states[2]
            else:
                curr_tone = states[3]
                for word in words:
                    for term in thanks_tones:
                        if word.lower() == term.lower():
                            curr_tone = states[4]
                    for term in closing_tones:
                        if word.lower() == term.lower():
                            curr_tone = states[0]
                    for term in request_tones:
                        if word.lower() == term.lower():
                            curr_tone = states[2]
        elif prev_tone == states[0]:
            curr_tone = states[1]
        elif prev_tone == states[2]:
            if prev_state == states[2]:
                curr_tone = states[3]
        elif prev_tone == states[3]:
            if prev_state == states[2]:
                curr_tone = states[2]  # can also be 3?
        elif prev_tone == states[4]:
            if prev_state == states[4]:
                curr_tone = states[0]
        self.set_tone(curr_tone)


    def verify_dialog(self, limits=None):
        curr_tone = self.get_tone()
        hist_tones = self.get_tones()
        num_tones = len(hist_tones)
        in_text = self.in_text[-1]
        resultData = self.nlu.parse_query(self.localdict, in_text, False, limits)

        if 'action' in resultData and 'reset' == resultData['action']:
            self.reset(self.name)
            return resultData
        if 'action' in resultData and 'unstop' == resultData['action']:
            self.reset(self.name)
            return resultData
        if 'action' in resultData and 'start' == resultData['action']:
            self.reset(self.name)
            return resultData

        prev_topic = self.get_topic()
        print "Prior topic: " + prev_topic
        topic = ''
        # this handles switching between goods or retrieving previous goods
        if 'action' in resultData:
            if resultData['action'] == 'find store':
                topic = 'location'
                if topic != prev_topic:
                    print "Change topic: Resetting to " + topic.upper()
                    if 'lost' in resultData:
                        del resultData['lost']
                    self.set_topic(topic)
            elif resultData['action'] == 'ask time':
                topic = 'datetime'
                if topic != prev_topic:
                    print "Change topic: Resetting to " + topic.upper()
                    if 'lost' in resultData:
                        del resultData['lost']
                    self.set_topic(topic)
            elif resultData['action'] in ['ask price', 'ask size', 'ask color', 'ask product']:
		if 'goods' in resultData:
                    goods = resultData['goods'].split(':')
                    if len(goods) > 0:
                        topic = goods[0]
                        if topic != prev_topic:
                            print "Change topic: Resetting to " + topic.upper()
                elif 'more' in resultData['action'].split(','):
                    resultData['action'] = 'more'
                    topic = prev_topic
                    print "Inherit topic: " + topic.upper()
		else:
		   topic = prev_topic
                   print "Inherit topic: " + topic.upper()
                if 'lost' in resultData:
                    del resultData['lost']
                    self.set_topic(topic)
            else:
                if 'goods' in resultData:
                    goods = resultData['goods'].split(':')
                    if len(goods) > 0:
                        topic = goods[0]
                        if topic != prev_topic:
                            print "Change topic: Resetting to " + topic.upper()
                            if 'lost' in resultData:
                                del resultData['lost']
                            self.set_topic(topic)
                elif 'more' in resultData['action'].split(','):
                    resultData['action'] = 'more'
                    topic = prev_topic
                    print "Inherit topic: " + topic.upper()
                    if 'lost' in resultData:
                        del resultData['lost']
                    self.set_topic(topic)

        elif 'datetime' in resultData or ('descriptor' in resultData and resultData['descriptor'] in ['open', 'close']):
            topic = 'datetime'
            if topic != prev_topic:
                print "Change topic: Resetting to " + topic.upper()
                if 'lost' in resultData:
                    del resultData['lost']
                self.set_topic(topic)
            if 'action' not in resultData:
                resultData['action'] = 'ask time'

        elif 'location' in resultData:
            topic = 'location'
            if topic != prev_topic:
                print "Change topic: Resetting to " + topic.upper()
                if 'lost' in resultData:
                    del resultData['lost']
                self.set_topic(topic)
            if 'action' not in resultData:
                resultData['action'] = 'find store'

        elif 'goods' in resultData:
            goods = resultData['goods'].split(':')
            if len(goods) > 0:
                topic = goods[0]
                print "GOODS: " + topic
                if topic != prev_topic:
                    print "Change topic: Resetting to " + topic.upper()
                    if 'lost' in resultData:
                        del resultData['lost']
                    self.set_topic(topic)

        elif 'occasion' in resultData:
            topic = prev_topic
            print "Inherit topic: " + topic.upper()
            if 'lost' in resultData:
                del resultData['lost']
            self.set_topic(topic)

        elif 'color' in resultData:
            topic = prev_topic
            print "Inherit topic: " + topic.upper()
            if 'lost' in resultData:
                del resultData['lost']
            self.set_topic(topic)

        elif 'size' in resultData:
            if prev_topic in ['location', 'datetime']:
                resultData['rownum'] = resultData['size']
                del resultData['size']
            topic = prev_topic
            print "Inherit topic: " + topic.upper()
            if 'lost' in resultData:
                del resultData['lost']
            self.set_topic(topic)

        elif 'brand' in resultData:
            topic = prev_topic
            print "Inherit topic: " + topic.upper()
            if 'lost' in resultData:
                del resultData['lost']
            self.set_topic(topic)

        elif 'price' in resultData:
            topic = prev_topic
            print "Inherit topic: " + topic.upper()
            if 'lost' in resultData:
                del resultData['lost']
            self.set_topic(topic)

        elif 'descriptor' in resultData:
            topic = prev_topic
            print "Inherit topic: " + topic.upper()
            if 'lost' in resultData:
                del resultData['lost']
            self.set_topic(topic)

        elif len(prev_topic) > 0:
            if 'lost' in resultData:
                del resultData['lost']
            topic = prev_topic
            self.set_topic(topic)

        else:
            if 'lost' in resultData:
                del resultData['lost']
            topic = "others"
            self.set_topic(topic)

        prev_tone = hist_tones[num_tones-2]
        if (topic == prev_topic) or 'prior_subject' in resultData and resultData['prior_subject'] == '1':
            prev_data = self.get_query()

            if prev_data and 'action' in prev_data:
                del prev_data['action']

            if prev_data and 'text' in prev_data:
                del prev_data['text']

            if prev_data and  'ERROR_CODE' in prev_data:
                del prev_data['ERROR_CODE']

            if 'ERROR_CODE' in resultData:
                del resultData['ERROR_CODE']

            if 'state' not in resultData:
                resultData['state'] = str(self.get_state())

            if in_text in basic_colors:
                resultData['color'] = in_text

            if 'prior_subject' not in resultData:
                resultData['prior_subject'] = '1'

            newdata = {}
            if prev_data:
                newdata.update(prev_data)
            newdata.update(resultData)
            resultData = newdata

        else:
            if 'ERROR_CODE' in resultData:
                del resultData['ERROR_CODE']

            if 'state' not in resultData:
                resultData['state'] = str(self.get_state())

            if in_text in basic_colors:
                resultData['color'] = in_text

            if prev_tone == states[2] and curr_tone == states[2]:
                if 'action' in resultData:
                    if 'find store' in resultData['action'] and not 'location' in resultData:
                        resultData['location'] = in_text
                else:
                    resultData['action'] = states[2]  # 'question'

            elif prev_tone == states[2] and curr_tone == states[3]:
                if 'action' in resultData:
                    if 'find store' in resultData['action'] and not 'location' in resultData:
                        resultData['location'] = in_text
                else:
                    resultData['action'] = states[3]  # 'answer'

        if 'action' not in resultData or resultData['state'] in (states[2], states[3]):
            if 'datetime' in resultData and resultData['datetime'] != None:
                resultData['action'] = 'ask time'
            elif 'location' in resultData and resultData['location'] != None:
                resultData['action'] = 'find store'
            elif 'goods' in resultData and resultData['goods'] != None:
                resultData['action'] = 'find'
            elif 'occasion' in resultData and resultData['occasion'] != None:
                resultData['action'] = 'find'
            elif 'color' in resultData and resultData['color'] != None:
                resultData['action'] = 'find'
            elif 'size' in resultData and resultData['size'] != None:
                resultData['action'] = 'find'
            elif 'brand' in resultData and resultData['brand'] != None:
                resultData['action'] = 'find'
            elif 'price' in resultData and resultData['price'] != None:
                resultData['action'] = 'find'
            elif 'descriptor' in resultData and resultData['descriptor'] != None:
                resultData['action'] = 'find'

        self.nlu.set_datastore_request(resultData)
        resultData = self.nlu.submit_query()

        print "\n***** RESULT *****\n"
        self.set_query(resultData)
        print self.get_query()
        return self.get_query()


    def converse(self, message, limits=None):
        self.preprocess(message)

        prev_state = self.get_state()
        curr_tone = self.get_tone()
        if curr_tone == states[0]:
            self.close()
        elif curr_tone == states[1]:
            self.start()
        elif curr_tone == states[4]:
            if prev_state == states[4]:
                self.close()
            else:
                self.thank_you()
        else:
            if prev_state == None or prev_state == states[0]:
                self.start()
                prev_state = self.get_state()
            resultData = self.verify_dialog(limits)
            print "\n***** RESPONSE *****\n"
            if 'ERROR_CODE' in resultData:
                self.respondWithQuestion(resultData)
            else:
                self.respondWithAnswer(resultData)

        print "\n***** CURRENT STATUS *****\n"
        tmp = "Current state: " + str(self.get_state())
        print tmp
        top = "Current topic: " + str(self.get_topic())
        print top
        print '\n***********************************\n'

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return (self.name)

    def set_communication(self, communication):
        self.communication = communication

    def get_communication(self):
        return self.communication

    def set_state(self, status):
        self.states.append(status)

    def get_state(self):
        if len(self.states) == 0:
            return None
        else:
            return (self.states[-1])

    def get_states(self):
        return (self.states)

    def set_tone(self, tone):
        self.tones.append(tone)

    def get_tone(self):
        if len(self.tones) == 0:
            return None
        else:
            return (self.tones[-1])

    def get_tones(self):
        return (self.tones)

    def set_topic(self, topic):
        self.topics.append(topic)

    def get_topic(self):
        if len(self.topics) == 0:
            return None
        else:
            return (self.topics[-1])

    def get_topics(self):
        return (self.topics)

    def set_data(self, data, state):
        record = {}
        record['speaker'] = self.name
        record['mesg_id'] = self.MesgId
        data['text'] = data['text'].decode('utf-8').replace(u"\u2019", "'") if 'text' in data and data['text'] != None else None
        record['message'] = data['text']
        record['link'] = data['link'] if 'link' in data else None
        record['data'] = data
        record['datetime'] = get_timestamp()
        self.set_state(state)
        record['state'] = state
        record['topic'] = self.get_topic()
        self.data.append(record)
        return record

    def get_data(self):
        if len(self.data) == 0:
            return None
        else:
            return (self.data[-1])

    def print_data(self):
        for rec in self.data:
            print rec
        return len(self.data)

    def set_query(self, query):
        self.query.append(query)

    def get_query(self):
        if len(self.query) > 0:
            return self.query[-1]
        else:
            return None

    def set_MesgId(self):
        self.MesgId = self.MesgId + 1

    def get_MesgId(self):
        return self.MesgId

    def sendResponse(self, record):
        record['sms_msgsid'] = self.communication.send(record)
        self.set_MesgId()

    def set_response_text(self, data, text, link=None):
        data['text'] = text
        data['link'] = link
        return data

    def start(self, text=None):
        record = self.set_data({'text': text}, states[1])
        self.set_topic("opening")
        record['topic'] = "opening"
        if (text):
            self.sendResponse(record)

    def respondWithQuestion(self, intent=None):
        print '-> respondWithQuestion:' + json.dumps(intent) + '\n'
        record = None
        if 'ERROR_CODE' in intent:
            if intent['ERROR_CODE'] == 'NO_LOCATION':
                self.set_response_text(intent,
                                       "Thank you for contacting " + self.banter_config.get_partner().title() + ". Where are you located?")
                record = self.set_data(intent, states[2])
            elif intent['ERROR_CODE'] == 'LOCATION_LOOKUP_FAILED':
                self.set_response_text(intent, "We could not find a store in '" + intent[
                    'location'] + "'. Can you please try again?")
                record = self.set_data(intent, states[2])
            elif intent['ERROR_CODE'] == 'DID_NOT_UNDERSTAND':
                self.set_response_text(intent,
                                       "Sorry, I don't understand your question. Can you please try to rephrase it?")
                record = self.set_data(intent, states[2])
            elif intent['ERROR_CODE'] == 'UNKNOWN_WORDS':
                self.set_response_text(intent, "However, I don't understand your question regarding \"" + ','.join(
                    intent['lost']) + "\". Can you check it again?")
                record = self.set_data(intent, states[2])
            elif intent['ERROR_CODE'] == 'TOO_MANY':
                if 'goods' in intent and 'dress' in intent['goods']:
                    tmp = []
                    filtermore = []
                    pricedesc = ''
                    if 'style' in intent:
                        tmp += intent['style'].split(',')
                    else:
                        filtermore.append('style')
                    if 'color' in intent:
                        tmp += intent['color'].split(',')
                    else:
                        filtermore.append('color')
                    if 'occasion' in intent:
                        tmp += intent['occasion'].split(',')
                    else:
                        filtermore.append('occasion')
                    if 'size' in intent:
                        tmp.append('size '+intent['size'])
                    else:
                        filtermore.append('size')
                    if 'price' in intent:
                        (str(intent['price']) if 'price' in intent else '')
                        if 'lost' in intent and 'under' in intent['lost']:
                            pricedesc = 'under ' + intent['price'][len(intent['price'])-1]

                        elif 'lost' in intent and 'over' in intent['lost']:
                            pricedesc = 'over ' + intent['price'][len(intent['price']) - 1]

                        else:
                            pricedesc = 'under ' + intent['price'][len(intent['price']) - 1]
                    else:
                        filtermore.append('price')
                    if 'brand' in intent:
                        tmp += intent['brand'].split(',')
                    else:
                        filtermore.append('brand')

                    if len(filtermore) <= 0:
                        filtermore.append('style')

                    expandedFilterMore = ''
                    for x in filtermore:
                        if len(expandedFilterMore):
                            if x == filtermore[len(filtermore)-1]:
                                expandedFilterMore += ' or ' + x
                            else:
                                expandedFilterMore += ', ' + x
                        else:
                            expandedFilterMore +=  x


                    tmp = 'I can help you with that. We\'ve got a wide selection of ' + ', '.join(
                        tmp) + ' dresses'+pricedesc+'. Can you help me narrow it down a bit more by specifying a '+expandedFilterMore+'?'
                    self.set_response_text(intent, tmp.replace('  ', ' ').strip())
                    record = self.set_data(intent, states[2])

                elif 'goods' in intent and 'polo' in intent['goods']:
                    tmp = []
                    filtermore = []
                    pricedesc = ''
                    if 'style' in intent:
                        tmp += intent['style'].split(',')
                    else:
                        filtermore.append('style')
                    if 'color' in intent:
                        tmp += intent['color'].split(',')
                    else:
                        filtermore.append('color')
                    if 'occasion' in intent:
                        tmp += intent['occasion'].split(',')
                    else:
                        pass; #filtermore.append('occasion')
                    if 'size' in intent:
                        tmp.append('size ' + intent['size'])
                    else:
                        filtermore.append('size')
                    if 'price' in intent:
                        (str(intent['price']) if 'price' in intent else '')
                        if 'lost' in intent and 'under' in intent['lost']:
                            pricedesc = ' under ' + intent['price'][len(intent['price']) - 1]

                        elif 'lost' in intent and 'over' in intent['lost']:
                            pricedesc = ' over ' + intent['price'][len(intent['price']) - 1]

                        else:
                            pricedesc = ' under ' + intent['price'][len(intent['price']) - 1]
                    else:
                        filtermore.append('price')
                    if 'brand' in intent:
                        tmp += intent['brand'].split(',')
                    else:
                        filtermore.append('brand')

                    if len(filtermore) <= 0:
                        filtermore.append('style')

                    expandedFilterMore = ''
                    for x in filtermore:
                        if len(expandedFilterMore):
                            if x == filtermore[len(filtermore) - 1]:
                                expandedFilterMore += ' or ' + x
                            else:
                                expandedFilterMore += ', ' + x
                        else:
                            expandedFilterMore += x

                    tmp = 'I can help you with that. We\'ve got a wide selection of ' + ', '.join(
                        tmp) + ' polos'+pricedesc+'. Can you help me narrow it down a bit more by specifying a '+expandedFilterMore+'?'
                    self.set_response_text(intent, tmp.replace('  ', ' ').strip())
                    record = self.set_data(intent, states[2])


                elif 'goods' in intent and (
                                    'shoe' in intent['goods'] or 'flats' in intent['goods'] or 'heels' in intent[
                            'goods'] or 'boots' in intent['goods'] or 'sneaker' in intent['goods']):
                    tmp = []
                    filtermore = []
                    pricedesc = ''
                    if 'style' in intent:
                        tmp += intent['style'].split(',')
                    else:
                        filtermore.append('style')
                    if 'color' in intent:
                        tmp += intent['color'].split(',')
                    else:
                        filtermore.append('color')
                    if 'occasion' in intent:
                        tmp += intent['occasion'].split(',')
                    else:
                        filtermore.append('occasion')
                    if 'size' in intent:
                        tmp.append('size ' + intent['size'])
                    else:
                        filtermore.append('size')
                    if 'price' in intent:
                        (str(intent['price']) if 'price' in intent else '')
                        if 'lost' in intent and 'under' in intent['lost']:
                            pricedesc = ' under ' + intent['price'][len(intent['price']) - 1]

                        elif 'lost' in intent and 'over' in intent['lost']:
                            pricedesc = ' over ' + intent['price'][len(intent['price']) - 1]

                        else:
                            pricedesc = ' under ' + intent['price'][len(intent['price']) - 1]
                    else:
                        filtermore.append('price')
                    if 'brand' in intent:
                        tmp += intent['brand'].split(',')
                    else:
                        filtermore.append('brand')

                    if len(filtermore) <= 0:
                        filtermore.append('style')

                    expandedFilterMore = ''
                    for x in filtermore:
                        if len(expandedFilterMore):
                            if x == filtermore[len(filtermore) - 1]:
                                expandedFilterMore += ' or ' + x
                            else:
                                expandedFilterMore += ', ' + x
                        else:
                            expandedFilterMore += x

                    type = 'shoes'
                    if 'flats' in intent['goods']:
                        type = 'flats'
                    elif 'heels' in intent['goods']:
                        type = 'flats'
                    elif 'boots' in intent['goods']:
                        type = 'boots'
                    elif 'sneaker' in intent['goods']:
                        type = 'sneakers'


                    tmp = 'I can help you with that. We\'ve got a wide variety of ' + ', '.join(
                        tmp) + ' ' + type +pricedesc+'. Can you help me narrow it down a bit by specifying a '+expandedFilterMore+'?'
                    self.set_response_text(intent, tmp.replace('  ', ' ').strip())
                    record = self.set_data(intent, states[2])

                elif 'goods' in intent and 'shirt' in intent['goods']:
                    tmp = []
                    filtermore = []
                    pricedesc = ''
                    if 'style' in intent:
                        tmp += intent['style'].split(',')
                    else:
                        filtermore.append('style')
                    if 'color' in intent:
                        tmp += intent['color'].split(',')
                    else:
                        filtermore.append('color')
                    if 'occasion' in intent:
                        tmp += intent['occasion'].split(',')
                    else:
                        pass #filtermore.append('occasion')
                    if 'size' in intent:
                        tmp.append('size ' + intent['size'])
                    else:
                        filtermore.append('size')
                    if 'price' in intent:
                        (str(intent['price']) if 'price' in intent else '')
                        if 'lost' in intent and 'under' in intent['lost']:
                            pricedesc = ' under ' + intent['price'][len(intent['price']) - 1]

                        elif 'lost' in intent and 'over' in intent['lost']:
                            pricedesc = ' over ' + intent['price'][len(intent['price']) - 1]

                        else:
                            pricedesc = ' under ' + intent['price'][len(intent['price']) - 1]
                    else:
                        filtermore.append('price')
                    if 'brand' in intent:
                        tmp += intent['brand'].split(',')
                    else:
                        filtermore.append('brand')

                    if len(filtermore) <= 0:
                        filtermore.append('style')

                    expandedFilterMore = ''
                    for x in filtermore:
                        if len(expandedFilterMore):
                            if x == filtermore[len(filtermore) - 1]:
                                expandedFilterMore += ' or ' + x
                            else:
                                expandedFilterMore += ', ' + x
                        else:
                            expandedFilterMore += x

                    tmp = 'I can help you with that. We\'ve got a wide variety of ' + ', '.join(
                        tmp) + ' shirts'+pricedesc+'. Is there a particular '+expandedFilterMore+'?'
                    self.set_response_text(intent, tmp.replace('  ', ' ').strip())
                    record = self.set_data(intent, states[2])

                elif 'goods' in intent and 'tv' in intent['goods']:

                    self.set_response_text(intent,
                                           'I can help you with that. Is there a particular type (LED/OLED), size, brand or price range?')
                    record = self.set_data(intent, states[2])

                elif 'goods' in intent and 'computer' in intent['goods']:
                    self.set_response_text(intent,
                                           'I can help you with that. Is there a particular Operating system (Mac/Windows/Chrome), size, brand or price range?')
                    record = self.set_data(intent, states[2])

                else:
                    self.set_response_text(intent,
                                           "I can help you with that.  Is there a particular type, size, brand or price range?")
                    record = self.set_data(intent, states[2])

            elif intent['ERROR_CODE'] == 'NOT_FOUND':
                if 'action' in intent:
                    if 'ask time' in intent['action']:
                        self.set_response_text(intent,
                                               "Could you please be more specific on which one?")
                        record = self.set_data(intent, states[2])
                    elif 'find store' in intent['action']:
                        self.set_response_text(intent,
                                               "Sorry, where are you located?")
                        record = self.set_data(intent, states[2])
                    elif 'need' in intent['action'] or \
                                    'look' in intent['action'] or \
                                    'need' in intent['action'] or \
                                    'find' in intent['action'] or \
                                    'buy' in intent['action'] or \
                                    'like' in intent['action'] or \
                                    'want' in intent['action']:

                        tmp = []
                        if 'lost' in intent:
                            tmp += intent['lost']
                        if 'style' in intent:
                            tmp += intent['style'].split(',')

                        if len(tmp) > 0:
                            self.set_response_text(intent,
                                                   "Sorry, I don't understand your question regarding \"" + ','.join(
                                                       tmp) + "\". Can you check it again?")
                        else:
                            self.set_response_text(intent,
                                                   "Sorry, I don't have the item you like. Can you check it again?")

                        record = self.set_data(intent, states[2])

                    elif 'ask price' in intent['action'] or \
                         'ask color' in intent['action'] or \
                         'ask size' in intent['action'] or \
                         'ask product' in intent['action']:

                        self.set_response_text(intent,
                                               "Sorry, I could not find that. Can you please try again?")
                        record = self.set_data(intent, states[2])
                    else:
                        self.set_response_text(intent,
                                               "Sorry, I don't understand your question. Can you please try to rephrase it?")
                        record = self.set_data(intent, states[2])
                else:
                    self.set_response_text(intent,
                                           "Sorry, I don't understand your question. Can you please try to rephrase it?")
                    record = self.set_data(intent, states[2])

            else:
                self.set_response_text(intent,
                                       "Sorry, I don't understand your question. Can you please try to rephrase it?")
                record = self.set_data(intent, states[2])
        elif "text" in intent:
            record = self.set_data(intent, states[2])
            intent['link'] = None
        else:
            self.set_response_text(intent,
                                   "Sorry, I don't understand your question. Can you please try to rephrase it?")
            record = self.set_data(intent, states[2])  # fvz

        self.sendResponse(record)

    def question(self, text=None):
        record = self.set_data({'text': text}, states[2])
        self.set_topic("question")
        record['topic'] = "question"
        self.sendResponse(record)

    def respondWithAnswer(self, data=None):
        print '-> respondWithAnswer DATA:' + json.dumps(data) + '\n'

        record = None

        if 'datastore_action' in data:
            if data['datastore_action'] == 'product_search':
                if len(data['datastore_products']) == 0:
                    self.set_response_text(data,
                                           'We could not find any products that match that.')

                else:
                    link = 'http://' + self.banter_config.get_partner() + '.banter.ai/products?partner=' + self.banter_config.get_partner()

                    if 'style' in data:
                        link += '&style=' + data['style']
                    if 'color' in data:
                        link += '&color=' + data['color']
                    if 'brand' in data:
                        link += '&brand=' + data['brand']

                    for product in data['datastore_products']:
                        link += '&pid=' + product['id']

                    self.set_response_text(data,
                                           'Here are the best options for you:', link)

                record = self.set_data(data, states[3])

            elif data['datastore_action'] == 'location_search':
                if len(data['datastore_locations']) == 0:
                    self.set_response_text(data,
                                           'We could not find a store near you.')
                elif len(data['datastore_locations']) == 1:
                    txt = 'Yes, there is a store nearby:\n'
                    txt += data['datastore_locations'][0]['name'] + ' - ' + data['datastore_locations'][0][
                        'address'] + ', ' + data['datastore_locations'][0]['city']
                    self.set_response_text(data, txt.strip())

                elif 'rownum' in data:
                    num = int(data['rownum']) - 1
                    txt = data['datastore_locations'][0]['name'] + ' - ' + data['datastore_locations'][num][
                        'address'] + ', ' + data['datastore_locations'][num]['city']
                    self.set_response_text(data, txt.strip())

                else:
                    txt = 'Yes, there are several stores nearby:\n'
                    for i in range(min(3, len(data['datastore_locations']))):
                        txt += str(i + 1) + ') ' + data['datastore_locations'][i]['name'] + '\n'

                    self.set_response_text(data, txt.strip())

                record = self.set_data(data, states[3])

            elif data['datastore_action'] == 'location_question':
                datetimefield = data['datetime'] if 'datetime' in data else 'today'

                datetimefield = datetimefield.split(',')
                if 'evening' in datetimefield or 'afternoon' in datetimefield or 'night' in datetimefield:
                    data['descriptor'] = 'close'
                elif 'morning' in datetimefield:
                    data['descriptor'] = 'close'

                if datetimefield[0] == 'time' or datetimefield[0] == 'datetime' or datetimefield[0] == 'date':
                    datetimefield = datetimefield[1] if len(datetimefield) > 1 else 'today'
                else:
                    datetimefield = datetimefield[0]
                    # datetimefield = datetimefield[len(datetimefield) - 1]

                # hack for time passed ini
                if datetimefield == 'time':
                    datetimefield = 'today'
                elif datetimefield == 'now':
                    datetimefield = 'today'
                    data['descriptor'] = 'hours'
                elif datetimefield == 'night':
                    datetimefield = 'tonight'
                elif datetimefield == 'afternoon':
                    datetimefield = 'tonight'
                elif datetimefield == 'evening':
                    datetimefield = 'tonight'
                elif datetimefield == 'morning':
                    datetimefield = 'today'
                elif 'week' in datetimefield:
                    del data['descriptor']
                    datetimefield = 'week'

                daytolookup = datetime.date.today().weekday()
                dayword = calendar.day_name[daytolookup]
                if datetimefield == 'today':
                    dayword = calendar.day_name[daytolookup]
                elif datetimefield == 'tomorrow':
                    daytolookup = daytolookup % 7
                    dayword = calendar.day_name[daytolookup]
                else:
                    # should be weekday
                    dayword = datetimefield

                dayhours = None
                dayword = dayword.lower().strip()
                text = ' - '
                if dayword == 'monday':
                    dayhours = data['datastore_location']['hours']['mon']
                    if datetimefield != 'today' and datetimefield != 'tomorrow':
                        data['datetime'] = dayword.title()
                elif dayword == 'tuesday':
                    dayhours = data['datastore_location']['hours']['tue']
                    if datetimefield != 'today' and datetimefield != 'tomorrow':
                        data['datetime'] = dayword.title()
                elif dayword == 'wednesday':
                    dayhours = data['datastore_location']['hours']['wed']
                    if datetimefield != 'today' and datetimefield != 'tomorrow':
                        data['datetime'] = dayword.title()
                elif dayword == 'thursday':
                    dayhours = data['datastore_location']['hours']['thr']
                    if datetimefield != 'today' and datetimefield != 'tomorrow':
                        data['datetime'] = dayword.title()
                elif dayword == 'friday':
                    dayhours = data['datastore_location']['hours']['fri']
                    if datetimefield != 'today' and datetimefield != 'tomorrow':
                        data['datetime'] = dayword.title()
                elif dayword == 'saturday':
                    dayhours = data['datastore_location']['hours']['sat']
                    if datetimefield != 'today' and datetimefield != 'tomorrow':
                        data['datetime'] = dayword.title()
                elif dayword == 'sunday':
                    dayhours = data['datastore_location']['hours']['sun']
                    if datetimefield != 'today' and datetimefield != 'tomorrow':
                        data['datetime'] = dayword.title()
                else:
                    if 'thr' in data['datastore_location']['hours']:
                        data['datastore_location']['hours']['thu'] = data['datastore_location']['hours']['thr']
                        del data['datastore_location']['hours']['thr']
                    for weekday in weekdays:
                        day = weekday.lower()[0:3]
                        if day in data['datastore_location']['hours']:
                            text += weekday + ': ' + data['datastore_location']['hours'][day]
                        if day == 'sun':
                            text += '. '
                        else:
                            if day == 'sat':
                                text += ', and '
                            else:
                                text += ', '
                # "descriptor":"close"
                if ('action' in data and 'how late' in data['action']) or ('descriptor' in data and 'open' in data['descriptor'] and  'until' in data['descriptor']):
                    parts = dayhours.split('-')
                    self.set_response_text(data, data['datastore_location']['name'] + ' ' + data['datastore_location'][
                        'city'] + ' is open until ' + parts[1] + ' ' + (
                        datetimefield if datetimefield else 'tonight') + '.')

                elif 'descriptor' in data and 'close' in data['descriptor']:
                    # Nordstrom Stanford Shopping Center closes at 9:00 PM tonight.
                    parts = dayhours.split('-')
                    self.set_response_text(data, data['datastore_location']['name'] + ' ' + data['datastore_location'][
                        'city'] + ' closes at ' + parts[1] + ' ' + (
                        datetimefield if datetimefield else 'tonight') + '.')
                elif 'descriptor' in data and 'open' in data['descriptor']:
                    # Nordstrom Stanford Shopping Center opens at 9:00 AM tomorrow.
                    parts = dayhours.split('-')
                    self.set_response_text(data, data['datastore_location']['name'] + ' ' + data['datastore_location'][
                        'city'] + ' opens at ' + parts[0] + ' ' + (
                        datetimefield if datetimefield else 'today') + '.')
                elif dayword in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                    parts = dayhours.split('-')
                    self.set_response_text(data, data['datastore_location']['name'] + ' ' + data['datastore_location'][
                        'city'] + ' is open from ' + parts[0] + ' until ' + parts[1] + ' ' + (
                        datetimefield if datetimefield else 'today') + '.')
                else:
                    self.set_response_text(data, data['datastore_location']['name'] + ' ' + data['datastore_location'][
                        'city'] + ' store hours of this week ' + text)

                record = self.set_data(data, states[3])

            elif data['datastore_action'] == 'product_question':
                if 'confirmation' in data:
                    if data['confirmation'] == '1':
                        self.set_response_text(data, "Great! Click here to go to complete the purchase:",
                                               data['datastore_product']['link'])
                        self.reset(self.name)
                        record = self.set_data(data, states[3])

                    else:
                        self.set_response_text(data, "Is there something else I can find for you?")
                        self.reset(self.name)
                        record = self.set_data(data, states[2])

                else:
                    tmp = []
                    if 'brand' in data['datastore_product']:
                        tmp.append(data['datastore_product']['brand'])
                    if 'title' in data['datastore_product']:
                        tmp.append(data['datastore_product']['title'])
                    if 'price' in data['datastore_product'] and data['datastore_product']['price']:
                        tmp.append('$' + data['datastore_product']['price'])
                    elif 'salePrice' in data['datastore_product'] and data['datastore_product']['salePrice']:
                        tmp.append('$' + data['datastore_product']['salePrice'])
                    elif 'originalPrice' in data['datastore_product'] and data['datastore_product']['originalPrice']:
                        tmp.append('$' + data['datastore_product']['originalPrice'])
                    elif 'regularPrice' in data['datastore_product'] and data['datastore_product']['regularPrice']:
                        tmp.append('$' + data['datastore_product']['regularPrice'])

                    self.set_response_text(data, 'Your selection is ' + ', '.join(tmp) + '. Would you like to buy it?')

                    record = self.set_data(data, states[2])

            else:
                self.set_response_text(data,
                                       "Sorry, I don't understand your question. Can you please try to rephrase it?")
                record = self.set_data(data, states[2])

        elif 'action' in data and 'reset' == data['action']:
            self.set_response_text(data, 'reset')
            record = self.set_data(data, states[1])

        elif 'action' in data and 'unstop' == data['action']:
            self.set_response_text(data, 'unstop')
            record = self.set_data(data, states[1])

        elif 'action' in data and 'start' == data['action']:
            self.set_response_text(data, 'start')
            record = self.set_data(data, states[1])

        else:
            self.set_response_text(data, "Sorry, I don't understand your question. Can you please try to rephrase it?")
            record = self.set_data(data, states[2])

        self.sendResponse(record)

    def answer(self, text=None):
        record = self.set_data({'text': text}, states[3])
        self.set_topic("answer")
        record['topic'] = "answer"
        self.sendResponse(record)

    def thank_you(self, text=None):
        if text == None:
            num = int(math.ceil(random.randint(1, 100) % len(thanks)))
            text = thanks[num]
            num1 = int(math.ceil(random.randint(1, 100) % 2))
            if text[-1] != '!' and text[-1] != '.' and text[-1] != '?':
                ext = exts[num1]
            else:
                ext = ''
            tet = text + ext
        record = self.set_data({'text': text}, states[4])
        self.set_topic("thanks")
        record['topic'] = "thanks"
        self.sendResponse(record)

    def close(self, comm_dump=None, text=None):
        if text == None:
            num = int(math.ceil(random.randint(1, 100) % 2))
            if num == 0:
                text = "Bye"
            elif num == 1:
                text = "Goodbye"

        record = self.set_data({'text': text}, states[0])
        self.set_topic("closing")
        record['topic'] = "closing"
        self.sendResponse(record)
        self.reset(self.name)


if __name__ == '__main__':
    comm_dump = None

    use_datastore = True
    partner = 'nordstrom'

    grammarConfig = BanterConfig(partner, 'case12.fcfg')
    dummyDataStore = DummyDataStore()
    realDataStore = AWSDataStore(partner, None)

    ##### configure banter client for an agent
    name_1 = "Banter"
    agent = BanterClient(name_1, grammarConfig, Echo(), realDataStore if use_datastore else dummyDataStore)

    ##### configure banter client for a customer
    name_2 = "Joe"
    customer = BanterClient(name_2, grammarConfig, Echo(), None)

    ##### case 1: store locations
    print "\n***** CASE 1.a *****\n"
    text = "Is there a store near me?"
#    text = "Is there a store nearby"
#    text = "Is there a BestBuy nearby"

    customer.question(text)

    # when message is received by agent
    #    dummyDataStore.setReturnError("NO_LOCATION")
    agent.converse(text)

    # agent starts the greeting message
#    text = "Thank you for contacting Nordstrom."
#    agent.start(text)

    # agent verifies the question
    # agent will respond given dummyDataStore.setReturnError above # text = "Where are you located?"
    # agent will respond given dummyDataStore.setReturnError above text = "What is your zip code?"
    # agent will respond given dummyDataStore.setReturnError above agent.respondWithQuestion({'text': text})

    print "\n***** CASE 1.b *****\n"
    # customer replies the location
    text = "Palo Alto"
#    text = "94301"
#    text = "SF"
#    text = "San Francisco Central"
#    text = "San Francisco CBD East"
    customer.answer(text)

    # agent should links this information with previous query to search for the result
    # Sample answer is something like:
    # Yes, there are several stores nearby: [display top 3 results closest to location
    # in a format similar to the example shown here, ordered by distance away]
    # 1) Nordstrom Stanford Shopping Center - Palo Alto, CA
    # 2) Nordstrom Hillsdale Shopping Center - San Mateo, CA
    # 3) Nordstrom Valley Fair - San Jose, CA
    agent.converse(text)

    print "\n***** CASE 1.c *****\n"
    # customer replies the location
    text = "1"
    customer.answer(text)

    agent.converse(text)

    ##### case 2: store hours
    print "\n***** CASE 2.a *****\n"
    text = "What are Stanford's hours?"
#    text = "What are Stanford's hours this week?"
#    text = "What time does the stanford store close?"
#    text = "What time does the Stanford store close?"
#    text = "What time is Richfield open until?"
    customer.question(text)

    # agent should reply something like:
    # "Nordstrom Stanford Shopping Center closes at 9:00 PM tonight." [notice this is different than previous demo]
    agent.converse(text)

    print "\n***** CASE 2.b *****\n"
    # customer asks when the store will open tomorrow
    text = "What time does it open tomorrow?"
#    text = "what time does the Stanford store open tomorrow"
#    text = "what are Richfield's hours today"
#    text = "what are Richfield's hours tomorrow"
#    text = "How late will Richfield store be open today"
#    text = "How late does Richfield store open today"
#    text = "How late will the store be open today"
#    text = "How late will Richfield store be open today"
#    text = "How late will the Richfield store be open today"
#    text = "How late does the Richfield store open today"
#    text = "How late does Richfield store open today"
#    text = "How late does the store open today"

    customer.question(text)

    # agent should reply something like:
    # "Nordstrom Stanford Shopping Center opens at 10:00 AM tomorrow."
    agent.converse(text)

#    exit()

    ##### case 3: customer requests for service - women's shoes
    print "\n***** CASE 3 *****\n"
#    text = "I'm looking for a new TV"
#    text = "I'm looking for a new 24\" TV"
#    text = "I need someone to trouble shoot my new 24\" TV"
#    text = "I need someone to troubleshoot my new 24\" TV"
#    text = "I'm looking for a 55\" Vizio HDTV"
#    text = "I'm looking for a 55\" TV"
#    text = "55\" Vizio"
#    text = "Macbook"
#    text = "Mac"
#    text = "I like the HP 13\""
#    text = "I'm looking for a new laptop"
#    text = "I'm looking for some red boots."
#    text = "I am looking for boots"
#    text = "I need some black boots"
#    text = "I need black boots"
#    text = "Do you have any black boots?"
#    text = "Do you have black boots?"
#    text = "I'm looking for tall dress boots"
#    text = "I'd like to buy a new dress"
    text = "I need new red boots with size 6"
    customer.question(text)

    # agent sends the product information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#    exit()

    ##### case 4: to test bad sentences
    print "\n***** CASE 4 *****\n"
#    text = "I'm looking for some red boots."
#    text = "I'm looking for some red shoes"
#    text = "I'm looking for some gucci handbags"
    text = "I'm looking for some handbags"
#    text = "I'm looking for some redd botts." # to test missing words
#    text = "I'm looking in for some red boots." # to test bogus words
#    text = "How much I'm looking for some red boots." # to test variation
#    text = "I am looking for red boots with a" # to test incomplete sentence
#    text = "I shot an elephant in my pajamas."
#    text = "I need some pajamas for my elephant."
#    text = " I don't like red boots."
#    text = " I don't like red color boots."
#    text = " I don't like red colored boots."
    customer.question(text)

    # agent sends the information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#   Try not use negative question
#    text = "Don't you need some new red shoes."
#    text = "Do you have OLED one"
#    text = "Reset"
#    text = "Red"
#    text = "White"
#    text = "Reset"
#    text = "1$50"
#    text = "150"
#    text = "$150, size 6"
    text = "150, gold, Gucci"
    customer.question(text)

    # agent sends the information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

    exit()

    ##### case 5: customer requests for service -- women's dresses
    print "\n***** CASE 5 *****\n"
#    text = "I need a blue polo shirt"
    text = "I need a new dress for picnic"
#    text = "I need a new dress for a wedding"
#    text = "I need a new dress for old fashioned day"
#    text = "I'm looking for some old fashioned dresses"
#    text = "Do you have any pink dress with buckle"
#    text = "I need some blue comfort shoes"
#    text = "I need some old fashioned purple comfort shoes with buckle"
    customer.question(text)

    # agent sends the information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#    exit()

    ##### case 6: customer requests for service -- men's shirts/t-shirts
    print "\n***** CASE 6 *****\n"
    text = "Purple under $70"
#    text = "Below $100"
#    text = "Less than $100"
#    text = "Less than 100"
#    text = "Above $100"
#    text = "More than 100"
#    text = "Between $70 and $100"
#    text = "Black dresses between $100 and $200"
#    text = "I want the dress of size 7"
#    text = "I want a t-shirt of size 7"
#    text = "Do you have pink shirts?"
#    text = "I like to buy a white shirt"
#    text = "I'm looking for some blue skirts"
#    text = "I am looking for black dinner dress under $500 with lace"
    customer.question(text)

    # agent sends the information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#    exit()

    ##### case 7: customer specifies questions
    print "\n***** CASE 7 *****\n"
#    text = "Do you have the French Connection in size 4"
#    text = "Do you have the second one in a large"
    text = "Do you have the second one in size XL"
    customer.question(text)

    # agent sends the information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#    exit()

    ##### case 8: agent verifies the question
    print "\n***** CASE 8 *****\n"
    #    text = "We don't have any in stock. Does size 5 work for you?"
    #    agent.respondWithQuestion({'text': text})

    # customer confirms/rejects the refined question
    text = "Yes"
#    text = "No"
    customer.answer(text)

    # agent responds to the order
    agent.converse(text)

#    exit()

    ##### case 9: customer likes to see some more products
    print "\n***** CASE 9 *****\n"

    text = "I am looking for gold sandals size 4"
    customer.question(text)

    # agent sends the information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#    text = "Can I see more like the first one"
#    text = "Do you have more like the first one?"
#    text = "I'm looking for tall dress boots like the first one"
#    text = "I am looking for more tall boots like the third one"
#    text = "I am looking for more like the third one"
#    text = "May I see that?"
#    customer.question(text)

    # agent sends the information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
#    agent.converse(text)

#    exit()

    ##### case 10: customer asks specific question
    print "\n***** CASE 10 *****\n"
#    text = "Do you have that in stock"
#    text = "How much is the first one"
#    text = "How much for the gucci"
#    text = "Do you have the second one in a large"
#    text = "Do you have the gucci in size 4"
#    text = "Do you have it in black"
#    text = "Do you have that in a large"
#    text = "Do you have that in red"
#    text = "Do you have that in scarlet"
#    text = "Do you have that in size 4"
    text = "How much is the first one"
#    text = "How much for the gucci"
#    text = "Do you have the second one in a large"
#    text = "Do you have the gucci in size 4"
#    text = "Do you have that in stock"
#    text = "Do you have it in black"
#    text = "Do you have that in a large"
#    text = "Do you have that in red"
#    text = "Do you have that in scarlet"
#    text = "Do you have that in size 4"
    customer.question(text)

    # agent sends the product information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#    exit()

    ##### case 11: customer has additional questions (more sophisticated)
    print "\n***** CASE 11 *****\n"
#    text = "Do you have the leather one?"
#    text = "Do you have that in red?"
#    text = "Can I see more?"
#    text = "Can I see the gucci?"
#    text = "Can I see the leather boot"
#    text = "I am looking for the ralph lauren white polo shirt"
#    text = "I am also looking for a gucci handbag"
    text = "Do you have that in red?"
#    text = "Can I see more?"
#    text = "Can I see the gucci?"
#    text = "Can I see the leather boot"
#    text = "I am looking for the ralph lauren white polo shirt"
#    text = "I am looking for a gucci handbag"
    customer.question(text)

    # agent sends the product information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#    exit()

    ##### case 12 for V2: more sophisticated questions
    print "\n***** CASE 12 *****\n"
#    text = "Do you have something like the gucci in black"
#    text = "What about something in a 6 inch heel"
#    text = "Like to see some red boots" # to test not understandable sentence (grammar can handle this sentence now)
#    text = "I need some old fashioned purple comfort shoes with with buckle" # to test bogus word
#    text = "I need some old fashioned purple comfort shoes with with long white buckle" # to test bogus word
#    text = "need some old fashioned purple comfort shoes with with long white buckle" # to test bogus word
    text = "where to find some old fashioned purple comfort shoes with with long white buckel"  # to test misspelled word "buckel"
    customer.question(text)

    # agent sends the product information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#    exit()

    ##### case 13: product information
    print "\n***** CASE 13 *****\n"
    text = "Do you have that in size 6?"
#    text = "Yellow polo under $100 size S"
#    text = "Yellow polo from $70 to $100 size L"
#    text = "Blue polo from $20 to $50 size XL"
    customer.question(text)

    # agent sends the product information of customer's products
    # text = 'Below is the information for you.'
    # product info should be attached to the end of text
    agent.converse(text)

#    exit()

    ##### case 14: customer sends a "thank you" message
    print "\n***** CASE 14 *****\n"
    text = "Thank you"
    customer.thank_you(text)

    # agent sends thanks
    agent.converse(text)

#    exit()

    ##### case 15: # automatically close the conversation on both sides
    print "\n***** CASE 15 *****\n"
#    text = "Bye, bye now"
    text = ""
    customer.close(text, comm_dump)

    # agent closes the conversation
    agent.converse(text)
