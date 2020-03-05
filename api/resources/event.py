from flask import make_response, current_app as app
from flask_restful import Resource, reqparse
from datetime import datetime
from bson import ObjectId

from api.resources.constants import HttpStatusCode
from api.resources.auth import token_required

base_parser = reqparse.RequestParser()
base_parser.add_argument('name', required=True, location='json')
base_parser.add_argument('start_datetime', required=True, location='json')
base_parser.add_argument('end_datetime', required=True, location='json')
base_parser.add_argument('max_guests_allowed', required=True, type=int, location='json')
base_parser.add_argument('cuisine', required=True, action='append', location='json')
base_parser.add_argument('price_per_person', required=True, type=float, location='json')
base_parser.add_argument('description', required=True, location='json')


class Event(Resource):

    def __init__(self):
        self.parser = base_parser.copy()

        for arg in self.parser.args:
            arg.required = False

        self.parser.add_argument('guests', action='append', location='json')
        self.parser.add_argument('rating', location='json')

    def get(self, id):
        if not ObjectId.is_valid(id):
            return make_response('[HTTP_400_BAD_REQUEST]', HttpStatusCode.HTTP_400_BAD_REQUEST)

        object_id = ObjectId(id)

        event = app.mongo.db.events.find_one({'_id': object_id})

        if not event:
            return make_response('[HTTP_404_NOT_FOUND]', HttpStatusCode.HTTP_404_NOT_FOUND)

        event['_id'] = str(event['_id'])

        return make_response({'data': event}, HttpStatusCode.HTTP_200_OK)

    @token_required
    def put(self, user_id, id):
        if not ObjectId.is_valid(id):
            return make_response('[HTTP_400_BAD_REQUEST]', HttpStatusCode.HTTP_400_BAD_REQUEST)

        args = self.parser.parse_args()

        object_id = ObjectId(id)

        events = app.mongo.db.events

        event = app.mongo.db.events.find_one({'_id': object_id})

        if not event:
            return make_response('[HTTP_404_NOT_FOUND]', HttpStatusCode.HTTP_404_NOT_FOUND)

        fields = {key: value for key,
                  value in args.items() if value is not None}

        events.update_one({'_id': object_id},
                          {
            '$push': {
                'changes': {
                    'fields': fields,
                    'updated_by_user': user_id,
                    'updated_datetime': datetime.utcnow()
                }
            }
        })

        return '[HTTP_204_NO_CONTENT]', HttpStatusCode.HTTP_204_NO_CONTENT


class EventList(Resource):

    def __init__(self):
        self.parser = base_parser.copy()

    def get(self):
        response = []
        events = app.mongo.db.events.find()

        for event in events:
            event['_id'] = str(event['_id'])
            response.append(event)

        return make_response({'data': response}, HttpStatusCode.HTTP_200_OK)

    @token_required
    def post(self, user_id):
        args = self.parser.parse_args()

        events = app.mongo.db.events

        events.insert_one({
            'host_id': user_id,
            'name': args['name'],
            'start_datetime': args['start_datetime'],
            'end_datetime': args['end_datetime'],
            'max_guests_allowed': args['max_guests_allowed'],
            'cuisine': args['cuisine'],
            'price_per_person': args['price_per_person'],
            'description': args['description'],
            'published:': True,
            'view_count:': 0,
            'created_by_user': user_id,
            'created_datetime': datetime.utcnow()
        })

        return '[HTTP_201_CREATED]', HttpStatusCode.HTTP_201_CREATED
