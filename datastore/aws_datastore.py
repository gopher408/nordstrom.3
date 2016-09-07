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


class AWSDataStore(DataStore):
    def __init__(self, partner, profileName):
        self.partner = partner
        self.profileName = profileName

        boto3.setup_default_session()
        self.searchHost = 'search-banter-q77sbxf2fph3xsdrnyszxwc7me.us-west-2.es.amazonaws.com'
        self.awsauth = AWS4Auth('AKIAJSGJI6BZPZ4YZDIA',
                                'TlbyJg8i9tuIoL9FaPytmoRXSFAkimOY3ed6gTol',
                                'us-west-2',
                                'es')
        self.googleKey = 'AIzaSyBTq1V4Bj6mSeeJ4u7bDKTPvdlNr-ry8XM'

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

            'High Low',
            'Flat Heel',
            'Low Heel',
            'Medium Heel',
            'High Heel',
            'Ultra High Heel']

        self.hackedproducts = [
            'Athletic',
            'Shoes',
            'Boat',
            'Shoes',
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
            'Wedges']

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

        self.globalBlackList = ['and', 'shop', 'the', 'con', 'com', 'largeselected']

    def search(self, queryData):
        return self.locationSearch(queryData)
        pass

    def locationSearch(self, queryData):
        logging.warning('productSearch')
        logging.warning(queryData)

        if not 'location' in queryData:
            print "AWSDataStore.locationSearch - NO_LOCATION:" + json.dumps(queryData)
            queryData['ERROR_CODE'] = 'NO_LOCATION'
            return queryData

        # given location lookup lat and long
        geoPoint = None

        google_places = GooglePlaces(self.googleKey)
        try:
            geoPoint = googleplaces.geocode_location(queryData['location'])
        except GooglePlacesError:
            print "AWSDataStore.locationSearch - LOCATION_LOOKUP_FAILED:" + queryData['location']
            queryData['ERROR_CODE'] = 'LOCATION_LOOKUP_FAILED'
            return queryData

        if not geoPoint:
            print "AWSDataStore.locationSearch - LOCATION_LOOKUP_FAILED:" + queryData['location']
            queryData['ERROR_CODE'] = 'LOCATION_LOOKUP_FAILED'
            return queryData

        print "AWSDataStore.locationSearch - using location" + str(geoPoint)

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
                "bool": {
                    "must": {
                        "match": {
                            "businessID": self.partner
                        },
                    },
                    "filter": {
                        "geo_distance": {
                            "distance": "60km",
                            "location": {
                                "lat": geoPoint['lat'],
                                "lon": geoPoint['lng']
                            }
                        }
                    }
                }
            }
        }

        #print {"query": queryFields}
        res = es.search(index='locations', body=queryFields)
        # default_operator, min_score

        queryData["locations"] = []

        print("%d documents found" % res['hits']['total'])
        for doc in res['hits']['hits']:
            queryData["locations"].append({
                'sort': doc['sort'],
                'docID': doc['_id'],
                'id': doc['_source']['id'],
                'city': doc['_source']['city'],
                'name': doc['_source']['name'],
                'address': doc['_source']['address']
            })

        logging.warning(queryData)
        return queryData

    def productSearch(self, queryData):
        logging.warning('productSearch')
        logging.warning(queryData)

        text = "INTENT: " + self.sqlset + ". To add search result here ..."

        es = Elasticsearch(
            hosts=[{'host': self.searchHost, 'port': 443}],
            http_auth=self.awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

        queryFields = {
            "bool": {
                "should": [],
                "filter": [{
                  "match": {
                    "businessID": self.partner
                  }
                }]
            }
        }

        for attr in queryData:
            fields = attr.split("=", 2)
            print fields

            if 'color' in fields[0]:
                color = fields[1].replace('"', '')
                queryFields['bool']['should'].append({"match": {"colors": {"query": [color], "boost": 2}}})

            if 'brand' in fields[0]:
                brand = fields[1].replace('"', '')
                queryFields['bool']['should'].append({"match": {"brand": {"query": brand, "boost": 2}}})

            if 'good' in fields[0]:
                good = fields[1].replace('"', '')
                queryFields['bool']['should'].append({"match": {"title": {"query": good, "boost": 1}}})
                queryFields['bool']['should'].append({"match": {"description": {"query": good}}})
                queryFields['bool']['should'].append({"match": {"categories": {"query": [good], "boost": 1}}})



        print {"query": queryFields}
        res = es.search(index='products', body={"query": queryFields})
        # default_operator, min_score

        products = []

        print("%d documents found" % res['hits']['total'])
        for doc in res['hits']['hits']:
            print("%s) %s" % (doc['_id'], doc['_score']), doc['_source']['id'], doc['_source']['title'], (doc['_source']['colors'] if 'colors' in doc['_source'] else doc['_source']['color']), doc['_source']['categories'], doc['_source']['description'])
            if (doc['_score'] > 0.05):
                products.append({
                    'score': doc['_score'],
                    'docID': doc['_id'],
                    'id': doc['_source']['id']
                })

        logging.warning(products)
        return products

    def cleanData(self, str, blacklist):

        cleaned = set([])

        str = str.replace(' amp ', ' and ')

        str = re.sub('[^0-9a-zA-Z]+', ' ', str).strip().lower()
        if str:
            if str and len(str) >= 3 and not str in self.globalBlackList and not str in blacklist:
                cleaned.add(str)
            fields = re.split("(\s+)", str)
            for field in fields:
                field = re.sub('[^0-9a-zA-Z]+', ' ', field).strip().lower()
                if field and len(field) >= 3 and not field in self.globalBlackList and not str in blacklist:
                    cleaned.add(field)

        return cleaned

    def getMulti(self, ids):
        logging.warning('getMulti')
        logging.warning(ids)

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

        deser = TypeDeserializer()

        products = []

        for itemDB in response[u'Responses'][u'products']:
            products.append({
                'id': deser.deserialize(itemDB['id']),
                'title': deser.deserialize(itemDB['title']),
                'description': deser.deserialize(itemDB['description']),
                'brand': deser.deserialize(itemDB['brand']),
                'businessID': deser.deserialize(itemDB['businessID']),
                'businessProductID': deser.deserialize(itemDB['businessProductID']),
                'categories': deser.deserialize(itemDB['categories']),
                'color': deser.deserialize(itemDB['color']),
                'colors': deser.deserialize(itemDB['colors']),
                'img': deser.deserialize(itemDB['img']),
                'itemID': deser.deserialize(itemDB['itemID']),
                'link': deser.deserialize(itemDB['link']),
                'orginalPrice': deser.deserialize(itemDB['orginalPrice']),
                'salePrice': deser.deserialize(itemDB['salePrice']),
                'size_desc': deser.deserialize(itemDB['size_desc']),
                'sizes': deser.deserialize(itemDB['sizes']),
                'thumbnails': deser.deserialize(itemDB['thumbnails'])
            })

        return products

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

    def getAllProductAttibutes(self):
        dynamodb = boto3.client('dynamodb', region_name='us-west-2')

        tds = TypeDeserializer()

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
                    data['colors'].update(self.cleanData(field, []))

            for field in self.hackedcolors:
                data['products'].update(self.cleanData(field, []))

            if 'brand' in itemDB:
                field = tds.deserialize(itemDB['brand'])
                data['brands'].update(self.cleanData(field, []))

            for field in self.hackedbrands:
                data['brands'].update(self.cleanData(field, []))

            if 'categories' in itemDB:
                fields = tds.deserialize(itemDB['categories'])
                for field in fields:
                    data['products'].update(self.cleanData(field, []))

            for field in self.hackedproducts:
                data['products'].update(self.cleanData(field, []))

            if 'styles' in itemDB:
                fields = tds.deserialize(itemDB['styles'])
                for field in fields:
                    data['styles'].update(self.cleanData(field, []))

            for field in self.hackedstyles:
                data['styles'].update(self.cleanData(field, []))

            if 'sizes' in itemDB:
                fields = tds.deserialize(itemDB['sizes'])
                for field in fields:
                    data['sizes'].update(self.cleanData(field , []))

            for field in self.hackedsizes:
                data['sizes'].update(self.cleanData(field, []))

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
                        data['colors'].update(self.cleanData(field, []))

                for field in self.hackedcolors:
                    data['products'].update(self.cleanData(field, []))

                if 'brand' in itemDB:
                    field = tds.deserialize(itemDB['brand'])
                    data['brands'].update(self.cleanData(field, []))

                for field in self.hackedbrands:
                    data['brands'].update(self.cleanData(field, []))

                if 'categories' in itemDB:
                    fields = tds.deserialize(itemDB['categories'])
                    for field in fields:
                        data['products'].update(self.cleanData(field, []))

                for field in self.hackedproducts:
                    data['products'].update(self.cleanData(field, []))

                if 'styles' in itemDB:
                    fields = tds.deserialize(itemDB['styles'])
                    for field in fields:
                        data['styles'].update(self.cleanData(field, []))

                for field in self.hackedstyles:
                    data['styles'].update(self.cleanData(field, []))

                if 'sizes' in itemDB:
                    fields = tds.deserialize(itemDB['sizes'])
                    for field in fields:
                        data['sizes'].update(self.cleanData(field, []))

                for field in self.hackedsizes:
                    data['sizes'].update(self.cleanData(field, []))

        return data

    def getAllLocationAttibutes(self):
        dynamodb = boto3.client('dynamodb', region_name='us-west-2')

        tds = TypeDeserializer()

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
                data['names'].update(self.cleanData(field, []))

            if 'zipCode' in itemDB:
                field = tds.deserialize(itemDB['zipCode'])
                data['zipcodes'].update(self.cleanData(field, []))

            if 'city' in itemDB:
                field = tds.deserialize(itemDB['city'])
                data['locations'].update(self.cleanData(field, []))



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

