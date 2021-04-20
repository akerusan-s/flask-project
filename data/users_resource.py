from flask_restful import reqparse, abort, Resource
from data import db_session
from .__all_models import User
from flask import jsonify


# инициализация парсера
parser = reqparse.RequestParser()
parser.add_argument("surname")
parser.add_argument("name")
parser.add_argument("email")
parser.add_argument("password")


def abort_if_user_not_found(user_id):
    """Обработка ошибки ненахождения пользователя"""
    session = db_session.create_session()
    user = session.query(User).get(user_id)  # пользователь
    if not user:
        abort(404, message=f"User {user_id} not found")


def abort_if_user_no_permission(user_id, password):
    """Проверка прав пользоваетля через пароль"""
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    # собственно проверка (как при авторизации)
    if not user.check_password(password):
        abort(403, message=f"No permission for user: {user_id} - wrong password")


class UsersResource(Resource):
    """ API для 1 пользователя """
    def get(self, user_id, password):
        """GET-запросы"""
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        # больше данных при правильно введенном пароле
        if user.check_password(password):
            return jsonify({'user': user.to_dict(only=("id", "surname", "name", "email", "shops_created",
                                                       "liked_goods", "liked_shops", "modified_date"))})
        return jsonify({'user': user.to_dict(only=("id", "surname", "name", "email", "shops_created"))})

    def delete(self, user_id, password):
        """DELETE-запросы"""
        abort_if_user_not_found(user_id)
        abort_if_user_no_permission(user_id, password)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        session.delete(user) # удаляем нужного нам пользователя
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, user_id, password):
        """PUT-запросы"""
        abort_if_user_not_found(user_id)
        abort_if_user_no_permission(user_id, password)
        args = parser.parse_args()
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        # изменяем то, что есть в запросе
        if args["surname"]:
            user.surname = args["surname"]
        if args["name"]:
            user.name = args["name"]
        if args["email"]:
            user.email = args["email"]
        if args["password"]:
            user.set_password(args["password"])
        session.commit()
        return jsonify({'success': 'OK'})


class UsersListResource(Resource):
    """API для списка пользователей"""
    def get(self):
        """GET-запросы"""
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify({'users': [item.to_dict(only=("id", "surname", "name", "email", "shops_created")) for item in users]})

    def post(self):
        """POST-запросы"""
        args = parser.parse_args()
        session = db_session.create_session()
        # создание пользователя, остальные данные по умолчанию
        user = User(
                surname=args["surname"],
                name=args["name"],
                email=args["email"],
        )
        user.set_password(args["password"])
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})
