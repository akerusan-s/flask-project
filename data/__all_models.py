import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField, IntegerField, FileField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin


class DeleteLikedEntity(FlaskForm):
    """ Форма для удаления сущности из избранного """
    submit = SubmitField("Удалить из избранного")


class AddLikedEntity(FlaskForm):
    """ Форма для добавления сущности в избранное """
    submit = SubmitField("Добавить в избранное")


class AddPicture(FlaskForm):
    """ Форма для добавления фото к товару """
    photo = FileField("Загрузить фото", validators=[DataRequired()])
    submit = SubmitField("Принять")


class DeleteEntity(FlaskForm):
    """ Форма для удаления сущности """
    submit = SubmitField("Удалить")


class AddGood(FlaskForm):
    """ Форма для добавления товара """
    description = TextAreaField("Описание", validators=[DataRequired()])
    name = StringField("Название", validators=[DataRequired()])
    price = IntegerField("Цена")
    group = StringField("Категория", default="Другое")
    photo = FileField("Загрузить фото", validators=[DataRequired()])
    active = BooleanField("Активно ли")
    count_goods = IntegerField("Количество")
    submit = SubmitField("Принять")


class CreateShop(FlaskForm):
    """ Форма для добавления магазина """
    description = TextAreaField("Описание", validators=[DataRequired()])
    name = StringField("Название", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    phone = StringField("Телефон")
    city = StringField("Город", validators=[DataRequired()])
    photo = FileField("Загрузить")
    show_email = BooleanField("Показывать ли Email")
    show_phone = BooleanField("Показывать ли Телефон")
    submit = SubmitField("Принять")


# Заготовочка на будущее
# class SearchForm(FlaskForm):
#     response = StringField('Найти товар...')
#     submit = SubmitField('Найти!')


class ChangeName(FlaskForm):
    """ Форма для изменения имени пользователя """
    new_name = StringField('Введите своё имя', validators=[DataRequired()])
    new_surname = StringField('Введите свою фамилию', validators=[DataRequired()])
    submit = SubmitField('Изменить')


class ChangeEmail(FlaskForm):
    """ Форма для изменения эл.почты пользователя """
    new_email = email = EmailField('Новая почта', validators=[DataRequired()])
    submit = SubmitField('Изменить')


class ChangePassword(FlaskForm):
    """ Форма для изменения пароля пользователя """
    new_password = email = EmailField('Новый пароль', validators=[DataRequired()])
    submit = SubmitField('Изменить')


class RegisterForm(FlaskForm):
    """ Форма для регистрации нового пользователя """
    name = StringField('Введите своё имя', validators=[DataRequired()])
    surname = StringField('Введите свою фамилию', validators=[DataRequired()])
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit2 = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    """ Форма для авторизации пользователя """
    email = EmailField('Адресс электронной почты', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    """ Форма-модель пользователя """
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    liked_goods = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True, default=",")
    liked_shops = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True, default=",")
    shops_created = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True, default=",")

    def __repr__(self):
        return f'<User> {self.id} {self.surname} {self.name}'

    def set_password(self, password):
        # хешируем введённый пароль пользователя, не явно хранится
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        # для проверки введенного и фактического паролей
        return check_password_hash(self.hashed_password, password)


class Shop(SqlAlchemyBase, UserMixin, SerializerMixin):
    """ Форма-модель магазина """
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

    likes = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    def __repr__(self):
        return f'<Shop> {self.id} {self.name} {self.email}'


class Good(SqlAlchemyBase, UserMixin, SerializerMixin):
    """ Форма-модель товара """
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
    count_pictures = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    count_goods = sqlalchemy.Column(sqlalchemy.Integer, default=1)

    def __repr__(self):
        return f'<Shop> {self.id} {self.name} {self.email}'
