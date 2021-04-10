# from flask_restful import reqparse, abort, Resource
# from data import db_session
# from .__all_models import User
# from flask import jsonify
#
#
# parser = reqparse.RequestParser()
# parser.add_argument("id", required=True, type=int)
# parser.add_argument("surname", required=True)
# parser.add_argument("name", required=True)
# parser.add_argument("age", required=True, type=int)
# parser.add_argument("position", required=True)
# parser.add_argument("speciality", required=True)
# parser.add_argument("address", required=True)
# parser.add_argument("email", required=True)
# parser.add_argument("hashed_password", required=True)
# parser.add_argument("modified_date", required=True)
#
#
# def abort_if_user_not_found(user_id):
#     session = db_session.create_session()
#     user = session.query(User).get(user_id)
#     if not user:
#         abort(404, message=f"User {user_id} not found")
#
#
# class UsersResource(Resource):
#     def get(self, user_id):
#         abort_if_user_not_found(user_id)
#         session = db_session.create_session()
#         user = session.query(User).get(user_id)
#         return jsonify({'user': user.to_dict()})
#
#     def delete(self, user_id):
#         abort_if_user_not_found(user_id)
#         session = db_session.create_session()
#         user = session.query(User).get(user_id)
#         session.delete(user)
#         session.commit()
#         return jsonify({'success': 'OK'})
#
#
# class UsersListResource(Resource):
#     def get(self):
#         session = db_session.create_session()
#         users = session.query(User).all()
#         return jsonify({'users': [item.to_dict() for item in users]})
#
#     def post(self):
#         args = parser.parse_args()
#         session = db_session.create_session()
#         user = User(
#             id=args["id"],
#             surname=args["surname"],
#             name=args["name"],
#             age=args["age"],
#             position=args["position"],
#             speciality=args["speciality"],
#             address=args["address"],
#             email=args["email"],
#             hashed_password=args["hashed_password"],
#             modified_date=args["modified_date"]
#         )
#         session.add(user)
#         session.commit()
#         return jsonify({'success': 'OK'})
