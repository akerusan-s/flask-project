from flask_restful import reqparse, abort, Resource
from data import db_session
from .__all_models import Good
from flask import jsonify


parser = reqparse.RequestParser()
parser.add_argument("surname")
parser.add_argument("name")
parser.add_argument("email")
parser.add_argument("password")


def abort_if_good_not_found(good_id):
    session = db_session.create_session()
    good = session.query(Good).get(good_id)
    if not good or not good.active:
        abort(404, message=f"Good {good_id} not found")


class GoodsResource(Resource):
    def get(self, good_id):
        abort_if_good_not_found(good_id)
        session = db_session.create_session()
        good = session.query(Good).get(good_id)
        result = {'good': good.to_dict(only=("id", "description", "name",
                                             "group", "likes", "price", "shop_id", "count_goods"))}
        return jsonify(result)


class GoodsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        goods = session.query(Good).all()
        return jsonify({'goods': [item.to_dict(only=("id", "description", "name",
                                               "group", "likes", "price", "shop_id", "count_goods")) for item in goods]})
