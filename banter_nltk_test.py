# -*- coding: utf-8 -*-
"""
Created on Wed Aug 03 11:01:25 2016

@author: raysun
"""

import banter_nltk as banter

import os, re, sys

file_folder = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(file_folder, '..'))
sys.path.insert(0, file_folder)

import math, nltk, os, random

from nltk.tokenize import MWETokenizer

from config.banter_config import BanterConfig
from communication.echo import Echo
from datastore.dummy_datastore import DummyDataStore
import json

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

#abbr = {"I'm": "I am", "I'd": "I would", "You're": "You are", "We're": "We are"}
abbr = {"I'm": "I am", "I'd": "I would", "You're": "You are", "We're": "We are", "<":"below", "<=":"below",">":"above",">=":"above","=":"equal","~":"about"}

neglist = {"ai'nt": "are not", "are'nt": "are not", "isn't": "is not", "wasn't": "was not", "weren't": "were not",
           "haven't": "have not", "hasn't": "has not", "hadn't": "had not", "sha'nt": "shall not", "shouldn't": "should not",
           "won't": "will not", "wouldn't":"would not","don't": "do not", "doesn't": "does not", "didn't": "did not" }

exts = [',', '.', '!', '?']


if __name__ == "__main__":
    # configure banter thinker
    grammarConfig = BanterConfig('Nordstrom', 'case12.fcfg')
    nlu = banter.BanterThinker(grammarConfig, Echo(), DummyDataStore())
    dict = global_dict
    test = True
    limits = None

    fd = open('testcases.csv','rb')
    i = 0
    for line in fd:
        if line[0] == '#':
           pass
        else:
           query = '\"' + line.split('\n')[0] + '\"'
           print "***** Test Case: " + str(i) + " *****\n" 
           datastore_request = nlu.parse_query(dict, query, test, limits)
           nlu.submit_query() 
           print "\n"
           i += 1 
