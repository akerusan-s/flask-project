from flask_restful import reqparse, abort, Resource
from data import db_session
from .__all_models import User, Shop, Good
from flask import jsonify


parser = reqparse.RequestParser()
parser.add_argument("surname")
parser.add_argument("name")
parser.add_argument("email")
parser.add_argument("password")


def abort_if_shop_not_found(shop_id):
    session = db_session.create_session()
    shop = session.query(Shop).get(shop_id)
    if not shop:
        abort(404, message=f"Shop {shop_id} not found")


class ShopsResource(Resource):
    def get(self, shop_id):
        abort_if_shop_not_found(shop_id)
        session = db_session.create_session()
        shop = session.query(Shop).get(shop_id)
        result = {'shop': shop.to_dict(only=("id", "description", "name",
                                             "city", "likes", "goods_id", "creator_id"))}
        if shop.show_phone:
            result["shop"]["phone"] = shop.phone
        if shop.show_email:
            result["shop"]["email"] = shop.email
        return jsonify(result)


class ShopsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        shops = session.query(Shop).all()
        return jsonify({'shops': [item.to_dict(only=("id", "description", "name", "email", "phone",
                                               "city", "likes", "goods_id", "creator_id")) for item in shops]})
