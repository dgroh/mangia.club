from datetime import datetime
from flask import Flask, make_response
from flask_restful import Resource, reqparse
from bson import ObjectId
import bcrypt

from . import HttpStatusCode
from db import mongo

base_parser = reqparse.RequestParser()
base_parser.add_argument('email', required=True, location='json')
base_parser.add_argument('first_name', required=True, location='json')
base_parser.add_argument('last_name', required=True, location='json')
base_parser.add_argument('password', required=True, location='json')
base_parser.add_argument('phone', required=True, location='json')

class User(Resource):
    def __init__(self):
        self.parser = base_parser.copy()

        for arg in self.parser.args:
            arg.required=False

        self.parser.add_argument('is_host', type=bool, location='json')
        self.parser.add_argument('rating', location='json')

    def get(self, id):
        object_id = ObjectId(id)

        user = mongo.db.users.find_one_or_404({ '_id': object_id })

        user['_id'] = str(user['_id'])
        user['hashed_password'] = user['hashed_password'].decode('utf-8')
        user['password_salt'] = user['password_salt'].decode('utf-8')

        return make_response({'data': user}, HttpStatusCode.HTTP_200_OK)

    def put(self, id):
        args = self.parser.parse_args()

        object_id = ObjectId(id)

        users = mongo.db.users

        users.find_one_or_404({ '_id': object_id })

        fields = { key: value for key,value in args.items() if value is not None }

        users.update_one({ '_id': object_id },
        {
            '$push': {
                'changes': {
                    'fields': fields,
                    'updated_by_user': '',
                    'updated_date_time': datetime.utcnow()
                }
            }
        })

        return '[HTTP_204_NO_CONTENT]', HttpStatusCode.HTTP_204_NO_CONTENT


class UserList(Resource):
    def __init__(self):
        self.parser = base_parser.copy()

    def get(self):
        response = []
        users = mongo.db.users.find()

        for user in users:
            user['_id'] = str(user['_id'])
            user['hashed_password'] = user['hashed_password'].decode('utf-8')
            user['password_salt'] = user['password_salt'].decode('utf-8')
            
            response.append(user)

        return make_response({'data': response}, HttpStatusCode.HTTP_200_OK)

    def post(self):
        args = self.parser.parse_args()

        existing_user = mongo.db.users.find_one({ 'email': args['email'] })

        if existing_user is None:
            password_salt = bcrypt.gensalt()

            hashed_password = bcrypt.hashpw(args['password'].encode('utf-8'), password_salt)

            mongo.db.users.insert_one({
                'email': args['email'],
                'first_name': args['first_name'],
                'last_name': args['last_name'],
                'hashed_password': hashed_password,
                'password_salt': password_salt,
                'phone': args['phone'],
                'published:': True,
                'created_by_user': args['email'],
                'created_date_time': datetime.utcnow()
            })

            return '[HTTP_201_CREATED]', HttpStatusCode.HTTP_201_CREATED

        return '[HTTP_409_CONFLICT]', HttpStatusCode.HTTP_409_CONFLICT
