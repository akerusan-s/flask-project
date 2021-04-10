import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField, IntegerField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin


class SearchForm(FlaskForm):
    response = StringField('Найти товар...')
    submit = SubmitField('Найти!')


class RegisterForm(FlaskForm):
    name = StringField('Введите своё имя', validators=[DataRequired()])
    surname = StringField('Введите свою фамилию', validators=[DataRequired()])
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit2 = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Адресс электронной почты', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    liked_goods = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    liked_shops = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    shops_created = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)

    def __repr__(self):
        return f'<User> {self.id} {self.surname} {self.name}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Shop(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'shops'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    phone = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)

    city = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    goods_id = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    creator_id = sqlalchemy.Column(sqlalchemy.Integer)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    show_email = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=True)
    show_phone = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=True)

    def __repr__(self):
        return f'<Shop> {self.id} {self.name} {self.email}'


class Good(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'goods'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    group = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    price = sqlalchemy.Column(sqlalchemy.Integer)
    shop_id = sqlalchemy.Column(sqlalchemy.Integer)
    likes = sqlalchemy.Column(sqlalchemy.Integer)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    active = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=True)

    def __repr__(self):
        return f'<Shop> {self.id} {self.name} {self.email}'
