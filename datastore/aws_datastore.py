from datastore import DataStore
import boto3
import logging
from boto3.dynamodb.conditions import Key, Attr
import re
from boto3.dynamodb.types import TypeDeserializer
from datetime import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from googleplaces import GooglePlaces, types, lang, GooglePlacesError
import googleplaces
import json
import re
from decimal import *

B = False

tds = TypeDeserializer()

class AWSDataStore(DataStore):
    def __init__(self, partner, profileName=None):
        self.partner = partner
        self.profileName = profileName

        boto3.setup_default_session()
        self.searchHost = 'search-banter-q77sbxf2fph3xsdrnyszxwc7me.us-west-2.es.amazonaws.com'
        self.awsauth = AWS4Auth('AKIAJSGJI6BZPZ4YZDIA',
                                'TlbyJg8i9tuIoL9FaPytmoRXSFAkimOY3ed6gTol',
                                'us-west-2',
                                'es')
        self.googleKey = 'AIzaSyBTq1V4Bj6mSeeJ4u7bDKTPvdlNr-ry8XM'

        ''' purge database
        dynamodb = boto3.client('dynamodb', region_name='us-west-2')
        response = dynamodb.scan(TableName='products')
        for itemDB in response[u'Items']:
            print(itemDB)
            dynamodb.delete_item(TableName='products',
                                 Key={'id': itemDB['id']})
        response = dynamodb.scan(TableName='product_color')
        for itemDB in response[u'Items']:
            print(itemDB)
            dynamodb.delete_item(TableName='product_color',
                                 Key={'productID': itemDB['productID'],
                                    'color': itemDB['color']})
        '''

        self.hackedstyles = [
            '3/4 and Long Sleeve',
            'A-Line',
            'Ballgown',
            'Body-Con',
            'Cold Shoulder',
            'Convertible',
            'Drop Waist',
            'Empire Waist',
            'Fit & Flare',
            'Halter',
            'Jumpsuits & Rompers',
            'Maxi',
            'Mermaid',
            'Off-the-Shoulder',
            'One Shoulder',
            'Peplum',
            'Popover',
            'Sheath',
            'Shift',
            'Shirtdress',
            'Slipdress',
            'Short Sleeve',
            'Skater',
            'Sleeveless',
            'Strapless',
            'Tank',
            'Trapeze',
            'Two-Piece',
            'Wrap',
            'little',
            'dinner',

            'Extra Trim Fit',
            'Trim Fit',
            'Regular Fit',
            'Classic Fit',

            'Check & Plaid',
            'Geometric',
            'Novelty',
            'Polka Dot',
            'Solid',
            'Striped',

            'Sleeveless',
            'Short Sleeve',
            'Long Sleeve',

            'Contemporary',
            'Designer',
            'Modern',
            'Trend',

            'Short',
            'Knee-Length',
            'Mid-Length',
            'Long',

            'Summer',
            'Off - the - Shoulder',
            'Jumpsuits & Rompers',
            'Dress Separates',

            'Maxi',
            'Midi',
            'Fit & Flare',
            'Lace',
            'Shift',
            'Sweater & Knit',

            'Athletic',
            'Boat',
            'Booties',
            'Boots',
            'shirt',
            'Clogs',
            'Flats',
            'Insoles',
            'Loafers',
            'Moccasins',
            'Mules',
            'Oxfords',
            'Pumps',
            'Sandals',
            'Shoe Care',
            'Slip-Ons',
            'Slippers',
            'Sneakers',
            'Wedges',
            'flowers',

            'High Low',
            'Flat Heel',
            'Low Heel',
            'Medium Heel',
            'High Heel',
            'Ultra High Heel', 'LED', 'OLED', 'Curved', 'plasma', 'Mac', 'Windows', 'chrome']

        self.hackedoccasion = [
            'Wedding Guest',
            'Cocktail & Party',
            'Mother of the Bride',
            'Formal',
            'Work',
            'Casual',
            'Homecoming',
            'Night Out',
            'Bridesmaid',
        ]

        self.hackedproducts = []

        self.hackedbrands = [
        ]

        self.hackedcolors = [

        ]

        self.hackedsizes = [
            'Small'
            'Petite Small',
            'Small P',
            'Small Petite',
            'petite',
            'medium',
            'large',
            'x-large'
            'xx-large'
        ]

        self.colors = [
            "pink",
            "black",
            "blue",
            "brown",
            "green",
            "orange",
            "pink",
            "purple",
            "red",
            "white",
            "yellow",
            "pink"
        ]

        self.globalBlackList = ['dresses', 'shoes', 'shirt', 't-shirt', 't-shirts', 'laptops',
                                'polo shirt', 'polo shirts', 'booties', 'flats', 'loafers', 'loafer', 'oxford',
                                'pump', 'pumps', 'sandal', 'sandals', 'slipper', 'slippers', 'selected',
                                'sneaker', 'sneakers', 'wedge', 'wedges', 'boots', 'boot',
                                'heel', 'heels', 'handbag', 'handbags', 'outfits', 'pant', 'pants',
                                'skirts', 'skirt', 'tshirts', 'tshirt', 't shirts', 't shirt'
                                'new', 'dress', 'shoe', 'shirt', 'boot', 'laptop', 'and', 'shop',
                                'the', 'con', 'com', 'largeselected', 'near', 'what', 'need', 'looking', 'want',
                                "pink", 'little black', 'little white',
                                "black", 'little', 'big', 'at',
                                "blue", "in", "south", 'shops',
                                "brown", 'out', 'night', 'day', 'evening', 'late'
                                "green", 'sunglasses',
                                "orange",
                                "pink",
                                "purple",
                                "red",
                                "white",
                                "yellow",
                                "pink"
                                ]

    def search(self, queryData):
        print 'AWSDataStore.search:' + json.dumps(queryData)

        if 'ERROR_CODE' in queryData:
            del queryData['ERROR_CODE']

        if 'action' in queryData:
            if 'ask time' in queryData['action']:
                return self.locationQuestion(queryData)
            elif 'find store' in queryData['action']:
                 return self.locationSearch(queryData)
            elif 'find' in queryData['action'] and 'store' in queryData:
                 return self.locationSearch(queryData)
            elif 'need' in queryData['action'] or \
                 'look' in queryData['action'] or \
                 'need' in queryData['action'] or \
                 'find' in queryData['action'] or \
                 'buy'  in queryData['action'] or \
                 'like' in queryData['action'] or \
                 'want' in queryData['action']:
                 if 'rownum' in queryData and 'datastore_products' in queryData:
                     return self.productQuestion(queryData)
                 else:
                     return self.productSearch(queryData)
            elif 'ask price' in queryData['action'] or \
                 'ask color' in queryData['action'] or \
                 'ask size'  in queryData['action'] or \
                 'ask product' in queryData['action']:
                 return self.productQuestion(queryData);

            elif 'see descriptor' in queryData['action'] and 'descriptor' in queryData and 'business hours' in queryData['descriptor']:
                return self.locationQuestion(queryData)

            elif 'see descriptor' in queryData['action'] and not 'descriptor' in queryData:

                if 'datastore_action' in queryData and 'product_search' in queryData['datastore_action']:
                    return self.productSearch(queryData)

                elif 'datastore_action' in queryData and 'location_search' in queryData['datastore_action']:
                    return self.locationSearch(queryData)

                print 'AWSDataStore.search -> returning DID_NOT_UNDERSTAND'
                queryData['ERROR_CODE'] = 'DID_NOT_UNDERSTAND'

        elif 'datetime' in queryData and queryData['datetime'] == 'time':
            return self.locationQuestion(queryData)

        elif 'descriptor' in queryData:
            if 'business hours' in queryData['descriptor']:
                return self.locationQuestion(queryData)
            else:
                print 'AWSDataStore.search -> returning DID_NOT_UNDERSTAND'
                queryData['ERROR_CODE'] = 'DID_NOT_UNDERSTAND'
                #if 'zipcode' in queryData or 'location' in queryData:
                #return self.locationSearch(queryData)
        else:
            print 'AWSDataStore.search -> returning DID_NOT_UNDERSTAND'
            queryData['ERROR_CODE'] = 'DID_NOT_UNDERSTAND'

        return queryData


    def locationQuestion(self, queryData):
        print 'AWSDataStore.locationQuestion:' + str(queryData)

        queryData['datastore_action'] = 'location_question'

        # lookup by location
        locations = self.findLocation(queryData)
        if not locations or not len(locations):
            print "AWSDataStore.locationQuestion - NOT_FOUND:" + json.dumps(queryData)
            queryData['ERROR_CODE'] = 'NOT_FOUND'
            return queryData

        store = locations[0]

        dynamodb = boto3.client('dynamodb', region_name='us-west-2')

        response = dynamodb.get_item(
            TableName='locations',
            Key={'id': {'S': store['id']}}
        )

        queryData['datastore_location'] = {
            'id': tds.deserialize(response['Item']['id']),
            'address': tds.deserialize(response['Item']['address']),
            'city': tds.deserialize(response['Item']['city']),
            'hours': tds.deserialize(response['Item']['hours']),
            'location': tds.deserialize(response['Item']['location']),
            'name': tds.deserialize(response['Item']['name']),
            'number': str(tds.deserialize(response['Item']['number'])) if 'number' in response['Item'] else None,
            'phoneNumber': tds.deserialize(response['Item']['phoneNumber']) if 'phoneNumber' in response['Item'] else None,
            'services': tds.deserialize(response['Item']['services']) if 'services' in response['Item'] else None,
            'state': tds.deserialize(response['Item']['state']),
            'type': tds.deserialize(response['Item']['type']) if 'type' in response['Item'] else None,
            'zipCode': tds.deserialize(response['Item']['zipCode'])
        }

        return queryData


    def locationSearch(self, queryData):
        print 'AWSDataStore.locationSearch:' + str(queryData)

        queryData['datastore_action'] = 'location_search'

        # use zipcode or location
        location = None
        guess = False

        if not location and 'location' in queryData and queryData['location']:
            location = queryData['location']
        if not location and 'zipcode' in queryData and queryData['zipcode']:
            location = queryData['zipcode']
        if not location and 'lost' in queryData and queryData['lost']:
            guess = True
            location = ' '.join(queryData['lost'])

        if not location:
            print "AWSDataStore.locationSearch - NO_LOCATION:" + json.dumps(queryData)
            queryData['ERROR_CODE'] = 'NO_LOCATION'
            return queryData

        # given location lookup lat and long
        geoPoint = None

        google_places = GooglePlaces(self.googleKey)
        try:
            geoPoint = googleplaces.geocode_location(location)
        except GooglePlacesError:
            if guess:
                print "AWSDataStore.locationSearch - NO_LOCATION:" + json.dumps(queryData)
                queryData['ERROR_CODE'] = 'NO_LOCATION'
            else:
                print "AWSDataStore.locationSearch - LOCATION_LOOKUP_FAILED:" + location
                queryData['ERROR_CODE'] = 'LOCATION_LOOKUP_FAILED'
            return queryData

        if not geoPoint:
            if guess:
                print "AWSDataStore.locationSearch - NO_LOCATION:" + json.dumps(queryData)
                queryData['ERROR_CODE'] = 'NO_LOCATION'
            else:
                print "AWSDataStore.locationSearch - LOCATION_LOOKUP_FAILED:" + location
                queryData['ERROR_CODE'] = 'LOCATION_LOOKUP_FAILED'
            return queryData

        print "AWSDataStore.locationSearch - using location" + str(geoPoint)

        if guess:
            queryData['location'] = location

        es = Elasticsearch(
            hosts=[{'host': self.searchHost, 'port': 443}],
            http_auth=self.awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

        queryFields = {
            "sort": [
                {
                    "_geo_distance": {
                        "location": {
                            "lat": geoPoint['lat'],
                            "lon": geoPoint['lng']
                        },
                        "order": "asc",
                        "unit": "km"
                    }
                }
            ],
            "query": {
                    "filtered": {
                        "filter": {
                            "bool": {
                                "must": [
                                    {
                                        "geo_distance": {
                                            "distance": "60km",
                                            "distance_type": "sloppy_arc",
                                            "location": {
                                                "lat": geoPoint['lat'],
                                                "lon": geoPoint['lng']
                                            }
                                        },
                                    },
                                    {
                                        "term": {
                                            "businessID": self.partner
                                        }
                                    }
                                ]
                            }
                        }
                }
            }
        }

        print 'AWSDataStore search query:' +  str(queryFields)
        try:
            res = es.search(index='locations', body=queryFields)
        except Exception as e:
            print(e)
            res = {
                "hits": {
                    "total": 0,
                    "hits": [],
                }
            }
        # default_operator, min_score

        queryData["datastore_locations"] = []

        print("AWSDataStore %d documents found" % res['hits']['total'])
        for doc in res['hits']['hits']:
            queryData["datastore_locations"].append({
                'sort': doc['sort'],
                'docID': doc['_id'],
                'id': doc['_source']['id'],
                'city': doc['_source']['city'],
                'name': doc['_source']['name'],
                'address': doc['_source']['address']
            })

        print 'AWSDataStore.locationSearch -> response' + str(queryData)

        return queryData


    def findProduct(self, queryData):
        print 'AWSDataStore.findProduct' + str(queryData)

        if 'rownum' in queryData and 'datastore_products' in queryData:
            if int(queryData['rownum']) <= len(queryData['datastore_products']):
                return queryData['datastore_products'][int(queryData['rownum'])-1]

        return None


    def findLocation(self, queryData):
        print 'AWSDataStore.findProduct' + str(queryData)

        location = None

        if 'location' in queryData:
            location = queryData['location']
        if 'zipcode' in queryData:
            location = queryData['zipcode']

        if not location:
            if 'lost' in queryData and queryData['lost']:
                location = queryData['lost'][0]
            else:
                return None

        es = Elasticsearch(
            hosts=[{'host': self.searchHost, 'port': 443}],
            http_auth=self.awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

        queryFields = {
            "query": {
                "bool": {
                    "should": [{"match": {"city": {"query": location, "boost": 10}}},
                               {"match": {"name": {"query": location, "boost": 5}}}],
                    "filter": [{
                      "match": {
                        "businessID": self.partner
                      }
                    }]
                }
            },
            "size": 10
        }

        print 'AWSDataStore seach query' + str(queryFields)
        res = es.search(index='locations', body=queryFields)
        # default_operator, min_score

        locations = []

        print("AWSDataStore %d documents found" % res['hits']['total'])
        for doc in res['hits']['hits']:
            if (doc['_score'] > 0.25):
                locations.append({
                    'score': doc['_score'],
                    'docID': doc['_id'],
                    'id': doc['_source']['id'],
                    'city': doc['_source']['city'],
                    'name': doc['_source']['name'],
                    'address': doc['_source']['address']
                })

        print 'AWSDataStore.locations' + str(locations)

        return locations


    def productQuestion(self, queryData):
        print 'AWSDataStore.productQuestion' + str(queryData)

        queryData['datastore_action'] = 'product_question'

        # lookup by location
        product = self.findProduct(queryData)
        if not product:
            print "AWSDataStore.locationQuestion - NOT_FOUND:" + json.dumps(queryData)
            queryData['ERROR_CODE'] = 'NOT_FOUND'
            return queryData

        dynamodb = boto3.client('dynamodb', region_name='us-west-2')

        response = dynamodb.get_item(
            TableName='products',
            Key={'id': {'S': product['id']}}
        )

        queryData['datastore_product'] = {
            'id': tds.deserialize(response['Item']['id']),
            'title': tds.deserialize(response['Item']['title']),
            'description': tds.deserialize(response['Item']['description']),
            'brand': tds.deserialize(response['Item']['brand']),
            'businessID': tds.deserialize(response['Item']['businessID']),
            'businessProductID': str(tds.deserialize(response['Item']['businessProductID'])),
            'categories': tds.deserialize(response['Item']['categories']),
            'color': tds.deserialize(response['Item']['color']),
            'colors': tds.deserialize(response['Item']['colors']) if 'colors' in response['Item'] else None,
            'img': tds.deserialize(response['Item']['img']),
            'itemID': str(tds.deserialize(response['Item']['itemID'])),
            'link': tds.deserialize(response['Item']['link']),
            'orginalPrice': str(tds.deserialize(response['Item']['orginalPrice'])) if 'orginalPrice' in response['Item'] else None,
            'salePrice': str(tds.deserialize(response['Item']['salePrice'])) if 'salePrice' in response['Item'] else None,
            'regularPrice': str(tds.deserialize(response['Item']['regularPrice'])) if 'regularPrice' in response['Item'] else None,
            'size_desc': str(tds.deserialize(response['Item']['size_desc'])) if 'size_desc' in response['Item'] else None,
            'sizes': tds.deserialize(response['Item']['sizes']) if 'sizes' in response['Item'] else None,
            'thumbnails': tds.deserialize(response['Item']['thumbnails']) if 'thumbnails' in response['Item'] else None
        }

        return queryData


    def productSearch(self, queryData):
        print 'AWSDataStore.productSearch' + str(queryData)

        queryData['datastore_action'] = 'product_search'

        if not 'goods' in queryData:
            print "AWSDataStore.locationQuestion - NOT_FOUND:" + json.dumps(queryData)
            queryData['ERROR_CODE'] = 'NOT_FOUND'
            return queryData

        es = Elasticsearch(
            hosts=[{'host': self.searchHost, 'port': 443}],
            http_auth=self.awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

        queryFields = {
            "bool": {
                "must": [],
                "should": [],
                "filter": [
                            {
                                "term": {
                                    "businessID": self.partner
                                }
                            }
                        ]
              }
        }

        if 'color' in queryData:
            fields = queryData['color'].split(',')
            for field in fields:
                queryFields['bool']['must'].append({"match": {"colors": {"query": field}}})

        if 'brand' in queryData:
            fields = queryData['brand'].split(',')
            for field in fields:
                queryFields['bool']['must'].append({"match": {"brand": {"query": field}}})

        if 'goods' in queryData:
            should = {
                'bool': {
                    'should': []
                }
            }

            goods = queryData['goods'].split(',')
            for good in goods:
                good = good.split(':')
                if len(good) >= 2:
                    if 'dress' in good[0]:
                        should2 = {
                            'bool': {
                                'should': []
                            }
                        }
                        should2['bool']['should'].append({"match": {"categories": {"query": "dress"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "dresses"}}})

                        queryFields['bool']['must'].append(should2)

                    elif 'heels' in good[0]:
                        should2 = {
                            'bool': {
                                'should': []
                            }
                        }
                        should2['bool']['should'].append({"match": {"categories": {"query": "heels"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "heel"}}})

                        queryFields['bool']['must'].append(should2)

                    elif 'boots' in good[0]:
                        should2 = {
                            'bool': {
                                'should': []
                            }
                        }
                        should2['bool']['should'].append({"match": {"categories": {"query": "boot"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "boots"}}})

                        queryFields['bool']['must'].append(should2)

                    elif 'sneaker' in good[0]:
                        should2 = {
                            'bool': {
                                'should': []
                            }
                        }
                        should2['bool']['should'].append({"match": {"categories": {"query": "sneaker"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "sneakers"}}})

                        queryFields['bool']['must'].append(should2)

                    elif 'flats' in good[0]:
                        should2 = {
                            'bool': {
                                'should': []
                            }
                        }
                        should2['bool']['should'].append({"match": {"categories": {"query": "flats"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "flat"}}})

                        queryFields['bool']['must'].append(should2)

                    elif 'shoe' in good[0]:
                        should2 = {
                            'bool': {
                                'should': []
                            }
                        }
                        should2['bool']['should'].append({"match": {"categories": {"query": "shoe"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "shoes"}}})

                        queryFields['bool']['must'].append(should2)

                    elif 'polo shirt' in good[0]:
                        should2 = {
                            'bool': {
                                'should': []
                            }
                        }
                        should2['bool']['should'].append({"match": {"categories": {"query": "polo"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "polos"}}})

                        queryFields['bool']['must'].append(should2)

                    elif 'shirt' in good[0]:
                        should2 = {
                            'bool': {
                                'should': []
                            }
                        }
                        should2['bool']['should'].append({"match": {"categories": {"query": "shirt"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "shirts"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "t-shirt"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "t-shirts"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "polo"}}})
                        should2['bool']['should'].append({"match": {"categories": {"query": "polos"}}})

                        queryFields['bool']['must'].append(should2)

                    should['bool']['should'].append({"match": {"title": {"query": good[1]}}})
                    should['bool']['should'].append({"match": {"description": {"query": good[1]}}})
                    should['bool']['should'].append({"match": {"categories": {"query": good[1]}}})
                    should['bool']['should'].append({"match": {"details": {"query": good[1]}}})
                    should['bool']['should'].append({"match": {"features": {"query": good[1]}}})
                else:
                    should['bool']['should'].append({"match": {"title": {"query": good}}})
                    should['bool']['should'].append({"match": {"description": {"query": good}}})
                    should['bool']['should'].append({"match": {"categories": {"query": good}}})
                    should['bool']['should'].append({"match": {"details": {"query": good}}})
                    should['bool']['should'].append({"match": {"features": {"query": good}}})

            queryFields['bool']['must'].append(should)

        if 'style' in queryData:
            should = {
                'bool': {
                    'should': []
                }
            }

            fields = queryData['style'].split(',')
            for field in fields:

                if field in self.colors:
                    should['bool']['should'].append({"match": {"color": {"query": field}}})
                    should['bool']['should'].append({"match": {"colors": {"query": field}}})
                else:
                    should['bool']['should'].append({"match": {"title": {"query": field}}})
                    should['bool']['should'].append({"match": {"description": {"query": field}}})
                    should['bool']['should'].append({"match": {"categories": {"query": field}}})
                    should['bool']['should'].append({"match": {"details": {"query": field}}})
                    should['bool']['should'].append({"match": {"features": {"query": field}}})
                    should['bool']['should'].append({"match": {"sizes": {"query": field}}})
                    should['bool']['should'].append({"match": {"color": {"query": field}}})
                    should['bool']['should'].append({"match": {"colors": {"query": field}}})

            queryFields['bool']['must'].append(should)

        if 'occasion' in queryData:
            should = {
                'bool': {
                    'should': []
                }
            }

            fields = queryData['occasion'].split(',')
            for field in fields:

                should['bool']['should'].append({"match": {"title": {"query": field}}})
                should['bool']['should'].append({"match": {"description": {"query": field}}})
                should['bool']['should'].append({"match": {"categories": {"query": field}}})
                should['bool']['should'].append({"match": {"details": {"query": field}}})
                should['bool']['should'].append({"match": {"features": {"query": field}}})
                should['bool']['should'].append({"match": {"sizes": {"query": field}}})
                should['bool']['should'].append({"match": {"color": {"query": field}}})
                should['bool']['should'].append({"match": {"colors": {"query": field}}})

            queryFields['bool']['must'].append(should)

        if 'price' in queryData:
            # price is [$555], [$100,$222], look at lost for under or over
            should = {
                'bool': {
                    'should': []
                }
            }

            if len(queryData['price']) == 2:
                locost = re.findall(r'\d+', queryData['price'][0])
                hicost = re.findall(r'\d+', queryData['price'][1])

                should['bool']['should'].append({"range": {"orginalPrice": {"gte": Decimal(locost[0])}}})
                should['bool']['should'].append({"range": {"salePrice": {"gte": Decimal(locost[0])}}})
                should['bool']['should'].append({"range": {"regularPrice": {"gte": Decimal(locost[0])}}})

                should['bool']['should'].append({"range": {"orginalPrice": {"lte": Decimal(hicost[0])}}})
                should['bool']['should'].append({"range": {"salePrice": {"lte": Decimal(hicost[0])}}})
                should['bool']['should'].append({"range": {"regularPrice": {"lte": Decimal(hicost[0])}}})

            else:
                lost = queryData['lost'] if 'lost' in queryData else []

                cost = re.findall(r'\d+', queryData['price'][0])
                if 'under' in lost:
                    should['bool']['should'].append({"range": {"orginalPrice": {"lte": Decimal(cost[0])}}})
                    should['bool']['should'].append({"range": {"salePrice": {"lte": Decimal(cost[0])}}})
                    should['bool']['should'].append({"range": {"regularPrice": {"lte": Decimal(cost[0])}}})

                elif 'over' in lost:

                    should['bool']['should'].append({"range": {"orginalPrice": {"gte": Decimal(cost[0])}}})
                    should['bool']['should'].append({"range": {"salePrice": {"gte": Decimal(cost[0])}}})
                    should['bool']['should'].append({"range": {"regularPrice": {"gte": Decimal(cost[0])}}})

                else:
                    should['bool']['should'].append({"range": {"orginalPrice": {"lte": Decimal(cost[0])}}})
                    should['bool']['should'].append({"range": {"salePrice": {"lte": Decimal(cost[0])}}})
                    should['bool']['should'].append({"range": {"regularPrice": {"lte": Decimal(cost[0])}}})

            queryFields['bool']['must'].append(should)

        if 'lost' in queryData:
            for field in queryData['lost']:
                should = {
                    'bool': {
                        'should': []
                    }
                }

                if field in self.colors:
                    should['bool']['should'].append({"match": {"color": {"query": field}}})
                    should['bool']['should'].append({"match": {"colors": {"query": field}}})

                    queryFields['bool']['must'].append(should)

                elif field not in ['under', 'over', 'between']:
                    should['bool']['should'].append({"match": {"title": {"query": field}}})
                    should['bool']['should'].append({"match": {"description": {"query": field}}})
                    should['bool']['should'].append({"match": {"categories": {"query": field}}})
                    should['bool']['should'].append({"match": {"details": {"query": field}}})
                    should['bool']['should'].append({"match": {"features": {"query": field}}})
                    should['bool']['should'].append({"match": {"sizes": {"query": field}}})
                    should['bool']['should'].append({"match": {"color": {"query": field}}})
                    should['bool']['should'].append({"match": {"colors": {"query": field}}})

                    queryFields['bool']['should'].append(should)

        if 'descriptor' in queryData:
            fields = queryData['descriptor'].split(',')
            for field in fields:
                should = {
                    'bool': {
                        'should': []
                    }
                }

                if field in self.colors:
                    should['bool']['should'].append({"match": {"color": {"query": field}}})
                    should['bool']['should'].append({"match": {"colors": {"query": field}}})

                    queryFields['bool']['must'].append(should)

#                elif field not in ['under', 'over', 'between']:
                elif field not in ['under', 'over']:
                    should['bool']['should'].append({"match": {"title": {"query": field}}})
                    should['bool']['should'].append({"match": {"description": {"query": field}}})
                    should['bool']['should'].append({"match": {"categories": {"query": field}}})
                    should['bool']['should'].append({"match": {"details": {"query": field}}})
                    should['bool']['should'].append({"match": {"features": {"query": field}}})
                    should['bool']['should'].append({"match": {"sizes": {"query": field}}})
                    should['bool']['should'].append({"match": {"color": {"query": field}}})
                    should['bool']['should'].append({"match": {"colors": {"query": field}}})

                    queryFields['bool']['should'].append(should)

        if 'size' in queryData:
            should = {
                'bool': {
                    'should': []
                }
            }

            fields = queryData['size'].split(',')
            for field in fields:
                should['bool']['should'].append({"match": {"sizes": {"query": 'size'+str(field)+'size'}}})
                should['bool']['should'].append({"match": {"size_desc": {"query": str(field)}}})
                if 'goods' in queryData and 'dress' in queryData['goods']:
                    if field == '2' or field == '3' or field == '4':
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str('small') + 'size'}}})
                    elif field == '6' or field == '7' or field == '8':
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str('medium') + 'size'}}})
                    elif field == '10' or field == '11' or field == '12':
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str('large') + 'size'}}})
                    elif field == '14' or field == '15' or field == '16':
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str('x-large') + 'size'}}})
                    elif field == 'small':
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(2) + 'size'}}})
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(3) + 'size'}}})
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(4) + 'size'}}})
                    elif field == 'medium':
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(6) + 'size'}}})
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(7) + 'size'}}})
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(8) + 'size'}}})
                    elif field == 'large':
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(10) + 'size'}}})
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(11) + 'size'}}})
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(12) + 'size'}}})
                    elif field == 'x-large':
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(13) + 'size'}}})
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(14) + 'size'}}})
                        should['bool']['should'].append({"match": {"sizes": {"query": 'size' + str(15) + 'size'}}})

            queryFields['bool']['must'].append(should)

        # fvz other fields, in db and passed

        print 'AWSDataStore search query:' + str({"query": queryFields})
        res = es.search(index='products', body={"query": queryFields, "size": 12})
        # default_operator, min_score

        queryData["datastore_products"] = []

        print("AWSDataStore - %d documents found" % res['hits']['total'])
        queryData["datastore_product_count"] = res['hits']['total'];

        for doc in res['hits']['hits']:
            print("AWSDataStore found doc: %s) %s" % (doc['_id'], doc['_score']), doc['_source']['id'], doc['_source']['title'])
            queryData["datastore_products"].append({
                'score': doc['_score'],
                'docID': doc['_id'],
                'id': doc['_source']['id']
            })
            if len(queryData["datastore_products"]) > 12:
                break

        if res['hits']['total'] > 20 and not 'answer' in queryData['action']:
            queryData['ERROR_CODE'] = 'TOO_MANY'
            print "AWSDataStore.productSearch - TOO_MANY:" + json.dumps(queryData)
            return queryData

        print 'AWSDataStore.productSearch -> response' + str(queryData)

        return queryData


    def cleanData(self, str, blacklist, parseString=True):

        cleaned = set([])

        str = str.replace(' amp ', ' and ')
        str = str.replace(' & ', ' and ')

        str = re.sub('[^0-9a-zA-Z]+', ' ', str).strip().lower()
        if str:
            if str and len(str) >= 3 and not str in self.globalBlackList and not str in blacklist:
                cleaned.add(str)
            if parseString:
                fields = re.split("(\s+)", str)
                for field in fields:
                    field = re.sub('[^0-9a-zA-Z]+', ' ', field).strip().lower()
                    if field and len(field) >= 3 and not field in self.globalBlackList and not str in blacklist:
                        cleaned.add(field)

        return cleaned


    def getMulti(self, ids):
        print 'AWSDataStore getMulti'

        dynamodb = boto3.client('dynamodb', region_name='us-west-2')

        dbIds = []
        for id in ids:
            dbIds.append({
                'id': {'S': id}
            })

        response = dynamodb.batch_get_item(
            RequestItems={
                'products': {
                    'Keys': dbIds
                }
            }
        )

        tmpProducts = {}
        for itemDB in response[u'Responses'][u'products']:
            tmpProducts[tds.deserialize(itemDB['id'])] = {
                'id': tds.deserialize(itemDB['id']),
                'title': tds.deserialize(itemDB['title']),
                'description': tds.deserialize(itemDB['description']) if 'description' in itemDB else None,
                'brand': tds.deserialize(itemDB['brand']) if 'brand' in itemDB else None,
                'businessID': tds.deserialize(itemDB['businessID']),
                'businessProductID': str(tds.deserialize(itemDB['businessProductID'])),
                'categories': tds.deserialize(itemDB['categories']) if 'categories' in itemDB else None,
                'color': tds.deserialize(itemDB['color']) if 'color' in itemDB else None,
                'colors': tds.deserialize(itemDB['colors']) if 'colors' in itemDB else None,
                'img': tds.deserialize(itemDB['img'])  if 'img' in itemDB else None,
                'itemID': str(tds.deserialize(itemDB['itemID'])) if 'itemID' in itemDB else None,
                'link': tds.deserialize(itemDB['link']),
                'orginalPrice': str(tds.deserialize(itemDB['orginalPrice'])) if 'orginalPrice' in itemDB else None,
                'salePrice': str(tds.deserialize(itemDB['salePrice'])) if 'salePrice' in itemDB else None,
                'regularPrice': str(tds.deserialize(itemDB['regularPrice'])) if 'regularPrice' in itemDB else None,
                'size_desc': tds.deserialize(itemDB['size_desc']) if 'size_desc' in itemDB else None,
                'sizes': tds.deserialize(itemDB['sizes']) if 'sizes' in itemDB else None,
                'thumbnails': tds.deserialize(itemDB['thumbnails']) if 'thumbnails' in itemDB else None
            }

        products = []
        for id in ids:
            if id in tmpProducts:
                products.append(tmpProducts[id])

        return products


    def getColors(self, productID):
        print 'AWSDataStore getColors' + str(productID)

        dynamodb = boto3.client('dynamodb', region_name='us-west-2')

        expressionattributenames = {}
        expressionattributevalues = {}
        filterexpression = []

        expressionattributenames['#productID'] = 'productID'
        expressionattributevalues[':productID'] = {'S': productID}
        filterexpression = '#productID = :productID'

        response = dynamodb.query(
            TableName='product_color',
            ExpressionAttributeNames=expressionattributenames,
            ExpressionAttributeValues=expressionattributevalues,
            KeyConditionExpression=filterexpression
        )

        print 'AWSDataStore response' + json.dumps(response)

        tmpProducts = []
        for itemDB in response[u'Items']:
            tmpProducts.append({
                'id': tds.deserialize(itemDB['productID']),
                'img': tds.deserialize(itemDB['img']),
                'color': tds.deserialize(itemDB['color']),
            })

        return tmpProducts


    def addLocation(self, partner, data):
        logging.warning('addLocation')
        logging.warning(partner)
        logging.warning(data)

        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('locations')

        data['businessID'] = partner
        data['id'] = str(data['number']) + '_' + partner

        response = table.put_item(
            Item=data
        )


    def addProduct(self, partner, data):
        logging.warning('addProduct')
        logging.warning(partner)
        logging.warning(data)

        assert 'businessID' in data
        assert 'title' in data
        assert 'link' in data
        assert 'img' in data

        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('products')

        data['businessID'] = partner
        data['id'] = str(data['businessProductID']) + '_' + partner

        response = table.put_item(
            Item=data
        )


    def getAllProductAttibutes(self):
        dynamodb = boto3.client('dynamodb', region_name='us-west-2')

        expressionattributenames = {}
        expressionattributevalues = {}
        filterexpression = []

        expressionattributenames['#businessID'] = 'businessID'
        expressionattributevalues[':businessID'] = {'S': self.partner}
        filterexpression.append('(#businessID = :businessID)')

        data = {}
        data['colors'] = set([])
        data['brands'] = set([])
        data['styles'] = set([])
        data['products'] = set([])
        data['sizes'] = set([])
        data['description'] = set([])
        data['occasion'] = set([])

        response = dynamodb.scan(
            TableName='products',
            ExpressionAttributeNames=expressionattributenames,
            ExpressionAttributeValues=expressionattributevalues,
            FilterExpression=' AND '.join(filterexpression)
        )

        for itemDB in response[u'Items']:
            if 'colors' in itemDB:
                fields = tds.deserialize(itemDB['colors'])
                for field in fields:
                    data['colors'].update(self.cleanData(field, [], False))

            for field in self.hackedcolors:
                data['products'].update(self.cleanData(field, [], False))

            if 'brand' in itemDB:
                field = tds.deserialize(itemDB['brand'])
                data['brands'].update(self.cleanData(field, [], False))

            for field in self.hackedbrands:
                data['brands'].update(self.cleanData(field, [], False))

            if 'categories' in itemDB:
                fields = tds.deserialize(itemDB['categories'])
                for field in fields:
                    if 'brand' in itemDB:
                        if itemDB['brand']['S'].lower() in field.lower() or field.lower() in itemDB['brand']['S'].lower():
                            continue

                    data['styles'].update(self.cleanData(field, ['nike'], False))

            for field in self.hackedproducts:
                data['products'].update(self.cleanData(field, ['best buy', 'best_buy', 'bestbuy'], False))

            data['products'].update(['tv:tv'])

            if 'styles' in itemDB:
                fields = tds.deserialize(itemDB['styles'])
                for field in fields:
                    data['styles'].update(self.cleanData(field, []))

            for field in self.hackedstyles:
                data['styles'].update(self.cleanData(field, []))

            for field in self.hackedoccasion:
                data['occasion'].update(self.cleanData(field, []))

            if 'sizes' in itemDB:
                fields = tds.deserialize(itemDB['sizes'])
                for field in fields:
                    data['sizes'].update(self.cleanData(field , [], False))

            for field in self.hackedsizes:
                data['sizes'].update(self.cleanData(field, [], False))

        while 'LastEvaluatedKey' in response:

            response = dynamodb.scan(
                TableName='products',
                ExpressionAttributeNames=expressionattributenames,
                ExpressionAttributeValues=expressionattributevalues,
                FilterExpression=' AND '.join(filterexpression),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )

            for itemDB in response[u'Items']:
                if 'colors' in itemDB:
                    fields = tds.deserialize(itemDB['colors'])
                    for field in fields:
                        data['colors'].update(self.cleanData(field, [], False))

                for field in self.hackedcolors:
                    data['products'].update(self.cleanData(field, [], False))

                if 'brand' in itemDB:
                    field = tds.deserialize(itemDB['brand'])
                    data['brands'].update(self.cleanData(field, [], False))

                for field in self.hackedbrands:
                    data['brands'].update(self.cleanData(field, [], False))

                if 'categories' in itemDB:
                    fields = tds.deserialize(itemDB['categories'])

                    for field in fields:
                        for field in fields:
                            if 'brand' in itemDB:
                                if itemDB['brand']['S'].lower() in field.lower() or field.lower() in itemDB['brand'][
                                    'S'].lower():
                                    continue

                        data['styles'].update(self.cleanData(field, ['nike'], False))

                for field in self.hackedproducts:
                    data['products'].update(self.cleanData(field, ['best buy', 'best_buy', 'bestbuy'], False))

                if 'styles' in itemDB:
                    fields = tds.deserialize(itemDB['styles'])
                    for field in fields:
                        data['styles'].update(self.cleanData(field, []))

                for field in self.hackedstyles:
                    data['styles'].update(self.cleanData(field, []))

                for field in self.hackedoccasion:
                    data['occasion'].update(self.cleanData(field, []))

                if 'sizes' in itemDB:
                    fields = tds.deserialize(itemDB['sizes'])
                    for field in fields:
                        data['sizes'].update(self.cleanData(field, [], False))

                for field in self.hackedsizes:
                    data['sizes'].update(self.cleanData(field, [], False))

        return data


    def getAllLocationAttibutes(self):
        dynamodb = boto3.client('dynamodb', region_name='us-west-2')

        expressionattributenames = {}
        expressionattributevalues = {}
        filterexpression = []

        expressionattributenames['#businessID'] = 'businessID'
        expressionattributevalues[':businessID'] = {'S': self.partner}
        filterexpression.append('(#businessID = :businessID)')

        data = {}
        data['locations'] = set([])
        data['names'] = set([])
        data['zipcodes'] = set([])

        response = dynamodb.scan(
            TableName='locations',
            ExpressionAttributeNames=expressionattributenames,
            ExpressionAttributeValues=expressionattributevalues,
            FilterExpression=' AND '.join(filterexpression)
        )

        for itemDB in response[u'Items']:
            if 'name' in itemDB:
                field = tds.deserialize(itemDB['name'])
                data['names'].update(self.cleanData(field, [], False))

            if 'zipCode' in itemDB:
                field = tds.deserialize(itemDB['zipCode'])
                data['zipcodes'].update(self.cleanData(field, [], False))

            if 'city' in itemDB:
                field = tds.deserialize(itemDB['city'])
                data['locations'].update(self.cleanData(field, [], False))

        while 'LastEvaluatedKey' in response:
            response = dynamodb.scan(
                TableName='products',
                ExpressionAttributeNames=expressionattributenames,
                ExpressionAttributeValues=expressionattributevalues,
                FilterExpression=' AND '.join(filterexpression),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )

            for itemDB in response[u'Items']:
                if 'name' in itemDB:
                    field = tds.deserialize(itemDB['name'])
                    data['names'].update(self.cleanData(field, []))

            if 'zipCode' in itemDB:
                field = tds.deserialize(itemDB['zipCode'])
                data['zipcodes'].update(self.cleanData(field, []))

            if 'locations' in itemDB:
                field = tds.deserialize(itemDB['city'])
                data['brands'].update(self.cleanData(field, []))

        return data


    def normalizeName(self, name, city):
        items = []
        items.append(name);

        # best name, strip co and city

        tmp = name.replace(self.partner, '').strip()
        tmp = name.replace('in ' + city, '').strip()

        return name;


