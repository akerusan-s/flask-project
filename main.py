import os
import PIL
import shutil
from PIL import Image

from flask import Flask, render_template, redirect, url_for, request, send_from_directory, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import reqparse, abort, Api, Resource
from werkzeug.utils import secure_filename

from data import db_session
from data import users_resource, shops_resource, goods_resources
from data.telephone_util import check_number
from data.__all_models import User, LoginForm, RegisterForm, ChangeEmail, ChangePassword, ChangeName, CreateShop
from data.__all_models import Shop, AddGood, Good, AddPicture, AddLikedEntity, DeleteLikedEntity
from data.__all_models import DeleteEntity as DeleteShop

# начальная папка загрузки
UPLOAD_FOLDER = ''
# разрешения, доступные при загрузке фотографий
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

# создание API
api = Api(app)

# рег-ция API для пользователей
api.add_resource(users_resource.UsersResource, '/api/v2/users/<int:user_id>/<password>')
api.add_resource(users_resource.UsersListResource, '/api/v2/users')

# рег-ция API для магазинов
api.add_resource(shops_resource.ShopsResource, '/api/v2/shops/<int:shop_id>')
api.add_resource(shops_resource.ShopsListResource, '/api/v2/shops')

# рег-ция API для товаров
api.add_resource(goods_resources.GoodsResource, '/api/v2/goods/<int:good_id>')
api.add_resource(goods_resources.GoodsListResource, '/api/v2/goods')

# Логин-менеджер для рег-ции и авт-ции пользователей
login_manager = LoginManager()
login_manager.init_app(app)
# конфиг секретного ключа и папки, куда будут скачиваться файлы
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """ Проверка на правильный формат фотографии """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Следуюшие ф-ции нужны для обработки некоторых http-кодов
@app.errorhandler(401)
def problem_401(e):
    return redirect("/")


@app.errorhandler(403)
def problem_403(e):
    return redirect("/")


@app.errorhandler(404)
def problem_404(e):
    return redirect("/")


# возвращение пользователя по id
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/all_shops")
def all_shops():
    """ Функция для показа всех магазинов площадки """
    db_sess = db_session.create_session()
    created_shops = sorted(db_sess.query(Shop).limit(10).all(),
                           key=lambda x: -x.likes)  # сортировка по количеству лайков
    return render_template("shops.html", shops=created_shops, title="Все Магазины")


@app.route("/shop/<shop_id>")
def shop(shop_id):
    """ Функция для показа страницы магазина по id """
    db_sess = db_session.create_session()
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()  # загрузка сущности

    # нахождение принадлежащих магазину товаров
    shop_goods_find = current_shop.goods_id.split(",")
    shop_goods = db_sess.query(Good).filter(Good.id.in_(shop_goods_find))

    # загрузка доступных городов магазинов
    cities = open("db/cities.txt", encoding="UTF-8").read().split("\n")

    # проверка на то, в избранном ли магазин у пользователя
    if current_user.is_authenticated:
        if str(current_shop.id) in current_user.liked_shops.split(","):
            flag = True
        else:
            flag = False
    else:
        flag = False

    return render_template("shop.html", shop=current_shop, goods=shop_goods,
                           title=current_shop.name, form=CreateShop(), cities=cities,
                           delete=DeleteShop(), pic_form=AddPicture(), flag=flag,
                           add_like=AddLikedEntity(), delete_like=DeleteLikedEntity())


@login_required
@app.route("/shop/<shop_id>/add_liked_shop", methods=["POST"])
def add_liked_shop(shop_id):
    """ Фунция для добавления магазина в список избранного (генерация пост-запроса) """
    db_sess = db_session.create_session()

    # нахождение магазина
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    # прибавление магазину лайка
    current_shop.likes += 1
    # прибавление к списку избранного пользователя выбранного магазина
    db_sess.query(User).filter(User.id == current_user.id).first().liked_shops += f"{current_shop.id},"
    db_sess.commit()
    return redirect(f"/shop/{shop_id}")


@login_required
@app.route("/shop/<shop_id>/delete_liked_shop", methods=["POST"])
def delete_liked_shop(shop_id):
    """ Фунция для удаления магазина из избранного """
    db_sess = db_session.create_session()

    # находим магазин, отнимаем луцк
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    current_shop.likes -= 1

    # находим пользователя, удаляем магазин из его списка
    user_now = db_sess.query(User).filter(User.id == current_user.id).first()
    list_of_liked_shops = user_now.liked_shops.split(",")
    index_liked = list_of_liked_shops.index(str(current_shop.id))
    list_of_liked_shops[index_liked] = ""
    user_now.liked_shops = ",".join(list_of_liked_shops)

    db_sess.commit()
    return redirect(f"/shop/{shop_id}")


@login_required
@app.route("/shop/<shop_id>/shop_delete", methods=["POST"])
def shop_delete(shop_id):
    """Фунция для удаления магазина """
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()  # находим магазин
    user = db_sess.query(User).filter(User.id == current_user.id).first()  # находим создателя
    db_sess.delete(current_shop)  # удаляем из бд
    db_sess.commit()

    # удаляем из списка пользователя
    created_shops = user.shops_created.split(",")
    created_shops[created_shops.index(str(shop_id))] = ""
    user.shops_created = ",".join(created_shops)
    db_sess.commit()

    # удаляем все файлы магазина
    shutil.rmtree(f"static/img/shops/{shop_id}")

    return redirect("/my_profile")


@login_required
@app.route("/shop/<shop_id>/change_shop_photo", methods=["POST"])
def change_shop_photo(shop_id):
    """ Фунцкия для изменения обложки(фото) магазина """
    file = request.files['file_photo']  # выделение файла из запроса

    # проверка на допустимость разрешения - формата
    if file and allowed_file(file.filename):
        # защищаем название фотографии
        filename = secure_filename(file.filename)

        # папку загрузки меняем на папку магазина
        app.config['UPLOAD_FOLDER'] = f"static/img/shops/{shop_id}"

        # сохраняем в папке
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # видоизменяем файл, как нам надо (сжатие до размеров 500*500 пикселей)
        img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        maxsize = (500, 500)
        img.thumbnail(maxsize, PIL.Image.ANTIALIAS)

        # сохраняем новый файл
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], "main.png"))

        # удаляем старый файл
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(f"/shop/{shop_id}")

    return redirect(f"/shop/{shop_id}")


@login_required
@app.route("/shop/<shop_id>/change_shop_info", methods=["POST"])
def change_shop_info(shop_id):
    """ Функция для изменения информации о магазине """
    form_creation = CreateShop()  # нужная форма
    cities = open("db/cities.txt", encoding="UTF-8").read().split("\n")  # возможные города магазина
    desc = request.form.get('text')  # выделяем значение поля описания
    phone = form_creation.phone.data  # выделяем значение поля телефона
    city = request.form.get('select_city')  # выделяем значение поля города

    # проверка на присутствие магазина в избранном (для подачи html-страницы)
    if str(shop_id) in current_user.liked_shops.split(","):
        flag = True
    else:
        flag = False

    db_sess = db_session.create_session()
    shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()  # находим нужный магазин

    # находим все товары магазина
    shop_goods_find = shop.goods_id.split(",")
    shop_goods = db_sess.query(Good).filter(Good.id.in_(shop_goods_find))

    # проврка корректности ввода номера телефона
    if ("+" in check_number(phone)) or (phone == ""):
        # принятие параметров (изменениий)
        shop.description = desc
        shop.name = form_creation.name.data
        shop.email = form_creation.email.data
        shop.phone = phone
        shop.city = city
        shop.show_email = form_creation.show_email.data
        shop.show_phone = form_creation.show_phone.data
        db_sess.commit()

        return redirect(f"/shop/{shop.id}")

    return render_template("shop.html", shop=shop, goods=shop_goods, delete=DeleteShop(),
                           title=shop.name, form=CreateShop(), cities=cities,
                           message="Недопустимый формат телефона", pic_form=AddPicture(), flag=flag,
                           add_like=AddLikedEntity(), delete_like=DeleteLikedEntity())


@app.route("/shop/<shop_id>/goods/<good_id>")
def good(shop_id, good_id):
    """ Функция для показа товара по id """
    db_sess = db_session.create_session()

    # находим магазин и принадлежащий ему товар
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    current_good = db_sess.query(Good).filter(Good.id == good_id).first()

    # проверка на создателя, если товар не активен
    if not current_good.active and current_shop.creator_id != current_user.id:
        abort(404)

    # находим картиночки товара, его категорию
    list_of_pictures = filter(lambda x: "." in x, os.listdir(f"static/img/shops/{shop_id}/goods/{good_id}"))
    categories = open("db/groups.txt", encoding="UTF-8").read().split("\n")

    # проверка на присутствие товара в избранном пользователя
    if current_user.is_authenticated:
        if str(good_id) in current_user.liked_goods.split(","):
            flag = True
        else:
            flag = False
    else:
        flag = False

    return render_template("good.html", shop=current_shop, good=current_good,
                           title=current_good.name, lst_pic=list_of_pictures,
                           form=AddGood(), categories=categories, delete=DeleteShop(),
                           pic_form=AddPicture(), flag=flag,
                           add_like=AddLikedEntity(), delete_like=DeleteLikedEntity())


@login_required
@app.route("/shop/<shop_id>/goods/<good_id>/add_liked_good", methods=["POST"])
def add_liked_good(shop_id, good_id):
    """ Форма-обработчик для лобавления в избранное товара """
    db_sess = db_session.create_session()
    # находим товар, ставим лайк
    current_good = db_sess.query(Good).filter(Good.id == good_id).first()
    current_good.likes += 1
    # находим пользоваетля, добавляем товар в список
    db_sess.query(User).filter(User.id == current_user.id).first().liked_goods += f"{current_good.id},"
    db_sess.commit()
    return redirect(f"/shop/{shop_id}/goods/{good_id}")


@login_required
@app.route("/shop/<shop_id>/goods/<good_id>/delete_liked_good", methods=["POST"])
def delete_liked_good(shop_id, good_id):
    """ Форма-обработчик для удаления из избранноого товара """
    db_sess = db_session.create_session()
    # находим товар, отнимаем лайк
    current_good = db_sess.query(Good).filter(Good.id == good_id).first()
    current_good.likes -= 1

    # находим пользователя, убираем товар из избранного
    user_now = db_sess.query(User).filter(User.id == current_user.id).first()
    list_of_liked_goods = user_now.liked_goods.split(",")
    index_liked = list_of_liked_goods.index(str(current_good.id))
    list_of_liked_goods[index_liked] = ""
    user_now.liked_goods = ",".join(list_of_liked_goods)

    db_sess.commit()
    return redirect(f"/shop/{shop_id}/goods/{good_id}")


@app.route("/shop/<shop_id>/goods/<good_id>/add_good_photo", methods=["POST"])
def add_good_photo(shop_id, good_id):
    """ Функция для добавление фотографии товару """
    db_sess = db_session.create_session()
    # находим магазин, товар
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    current_good = db_sess.query(Good).filter(Good.id == good_id).first()

    # проверяем на владельца магазина
    if current_shop.creator_id == current_user.id:
        file = request.files['file_photo']  # пикча

        # проверка на общее количество фотографий (не больше 10)
        if current_good.count_pictures >= 10:
            return "Too many pictures"
        # проверка на формат файла, допустимое разрешение
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)  # защищаем название фото
            current_good.count_pictures += 1  # добавляем +1 к количеству
            db_sess.commit()

            # определяем папку для загрузки фотографий, сохраняем
            app.config['UPLOAD_FOLDER'] = f"static/img/shops/{current_shop.id}/goods/{current_good.id}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # изменяем фотографию ( сжатие до 420*420 пикселей )
            img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            maxsize = (420, 420)
            img.thumbnail(maxsize, PIL.Image.ANTIALIAS)
            # сохраняем фотографию, старую удаляем
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], f"good_photo_{current_good.count_pictures}.png"))
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(f"/shop/{current_shop.id}/goods/{good_id}")
    else:
        return "no permission"


@login_required
@app.route("/shop/<shop_id>/goods/<good_id>/change_good_info", methods=["POST"])
def change_good_info(shop_id, good_id):
    """Функция-обработчик для изменения товара"""
    db_sess = db_session.create_session()
    # определяем магазин, товар
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    current_good = db_sess.query(Good).filter(Good.id == good_id).first()
    form_creation = AddGood()

    # проверка на владельца магазина
    if current_shop.creator_id == current_user.id:
        # изменяем необходимые параметры
        desc = request.form.get('text')
        group = request.form.get('select_city')
        current_good.description = desc
        current_good.name = form_creation.name.data
        current_good.group = group
        current_good.price = form_creation.price.data
        current_good.active = form_creation.active.data
        current_good.count_goods = form_creation.count_goods.data
        db_sess.commit()
        return redirect(f"/shop/{current_shop.id}/goods/{current_good.id}")
    else:
        return "no permission"


@login_required
@app.route("/shop/<shop_id>/goods/<good_id>/good_delete", methods=["POST"])
def good_delete(shop_id, good_id):
    """Удаление товара по id"""
    db_sess = db_session.create_session()
    # определение товара и магазина
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    current_good = db_sess.query(Good).filter(Good.id == good_id).first()

    # удаление товара из списка магазина
    new_list = current_shop.goods_id.split(",")
    index_of_delete = new_list.index(str(current_good.id))
    new_list[index_of_delete] = ""
    current_shop.goods_id = ",".join(new_list)

    # удаление товара из бд
    db_sess.delete(current_good)
    db_sess.commit()

    # удаление всех фото товара и папки товара
    shutil.rmtree(f"static/img/shops/{shop_id}/goods/{good_id}")
    return redirect(f"/shop/{shop_id}")


@login_required
@app.route("/shop/<shop_id>/create_good", methods=["POST", "GET"])
def create_good(shop_id):
    """Страница создания товара"""
    form = AddGood()  # необходимая форма
    db_sess = db_session.create_session()
    # определяем магазин
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    # определяем категории товаров
    categories = open("db/groups.txt", encoding="UTF-8").read().split("\n")
    # проверка на владельца магазина
    if current_shop.creator_id == current_user.id:
        return render_template("create_good.html", form=form, categories=categories,
                               shop=current_shop, title="Добавить товар")
    else:
        return "no permission"


@login_required
@app.route("/shop/<shop_id>/creation_good", methods=["POST"])
def creation_good(shop_id):
    """Фунция-обработчик для создания товара"""
    db_sess = db_session.create_session()
    # определяем магазин, категории, формы
    categories = open("db/groups.txt", encoding="UTF-8").read().split("\n")
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    form_creation = AddGood()

    # проверка на владельца магазина
    if current_shop.creator_id == current_user.id:
        # извлечение информации из запроса
        file = request.files['file']
        desc = request.form.get('text')
        group = request.form.get('select_city')
        # проверка на допустимую фотографию (расширение, формат)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)  # шифруемся

            # создаем товар
            good = Good(
                description=desc,
                name=form_creation.name.data,
                group=group,
                price=form_creation.price.data,
                shop_id=current_shop.id,
                likes=0,
                active=form_creation.active.data,
                count_goods=form_creation.count_goods.data
            )

            db_sess.add(good)  # добавляем товар
            db_sess.commit()

            # добавляем товар к магазину
            current_shop.goods_id += f"{good.id},"
            db_sess.commit()
            # создаем для товара папку
            os.mkdir(f"static/img/shops/{current_shop.id}/goods/{good.id}")
            app.config['UPLOAD_FOLDER'] = f"static/img/shops/{current_shop.id}/goods/{good.id}"
            # сохраняеи файл, видоизменив его
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            maxsize = (420, 420)
            img.thumbnail(maxsize, PIL.Image.ANTIALIAS)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], "good_photo_1.png"))
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(f"/shop/{current_shop.id}")
        else:
            return render_template("create_good.html", form=form_creation, categories=categories,
                                   shop=current_shop, message="Неподдерживаемый формат фото", title="Добавить товар")
    else:
        return "no permission"


@login_required
@app.route("/create_shop", methods=["POST", "GET"])
def create_shop():
    """Страница создания магазина"""
    form_creation = CreateShop()  # необходимая форма
    cities = open("db/cities.txt", encoding="UTF-8").read().split("\n")  # возможные города магазина
    return render_template("create_shop.html", title="Создать Магазин", form=form_creation,
                           cities=cities)


@login_required
@app.route("/create", methods=["POST"])
def create():
    """Фунция-обработчик для создания магазина"""
    form_creation = CreateShop()  # необходимая форма
    cities = open("db/cities.txt", encoding="UTF-8").read().split("\n")  # возможные города

    # извлекаем информацию из запроса
    file = request.files['file']
    desc = request.form.get('text')
    phone = form_creation.phone.data
    city = request.form.get('select_city')
    db_sess = db_session.create_session()

    # определяем пользователя-создателя
    user = db_sess.query(User).filter(User.id == current_user.id).first()

    # проверка корректности ввода телефона
    if ("+" in check_number(phone)) or (phone == ""):
        # проверка формата фотографии обложки
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)  # шифруемся
            # создаём магазин
            shop = Shop(
                description=desc,
                name=form_creation.name.data,
                email=form_creation.email.data,
                phone=phone,
                city=city,
                goods_id="",
                creator_id=current_user.id,
                show_email=form_creation.show_email.data,
                show_phone=form_creation.show_phone.data
            )
            db_sess.add(shop)
            db_sess.commit()
            # добавляем пользователю магазин
            user.shops_created += f"{shop.id},"
            db_sess.commit()

            # определяем папки для магазина
            app.config['UPLOAD_FOLDER'] = f"static/img/shops/{shop.id}"
            os.mkdir(f"static/img/shops/{shop.id}")
            os.mkdir(f"static/img/shops/{shop.id}/goods")
            # сохраняем видоизменённую обложку (сжатие до 500*500 пикселей)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            maxsize = (500, 500)
            img.thumbnail(maxsize, PIL.Image.ANTIALIAS)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], "main.png"))
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect("/my_profile")

        return render_template("create_shop.html", title="Создать Магазин",
                               form=form_creation, cities=cities, message="Недопустимый формат файлов")
    return render_template("create_shop.html", title="Создать Магазин",
                           form=form_creation, cities=cities, message="Недопустимый формат телефона")


@app.route('/')
def main_page():
    """Функция для обработки '/' запроса"""
    return redirect("/store")


@app.route('/access', methods=['GET', 'POST'])
def log():
    form = LoginForm()
    form2 = RegisterForm()
    return render_template('login.html', form=form, form2=form2, message="", title="Авторизация")


@app.route("/store")
def store():
    """Функция для загрузки всех товаров"""
    db_sess = db_session.create_session()
    goods = db_sess.query(Good).filter(Good.active).limit(20).all()  # все товары (для теста первые 20)
    return render_template("store.html", title="Магазин", goods=goods)


@app.route('/logout')
@login_required
def logout():
    """Функция-обработчик для выхода пользователя из аккаунта"""
    logout_user()
    return redirect("/access")


@app.route('/register', methods=['POST'])
def register():
    """Функция-обработчик для регистрации пользователя"""
    register_form = RegisterForm()  # необходимая форма
    login_form = LoginForm()  # необходимая форма

    # проверка на корректность пароля (повтор ввода)
    if register_form.password.data != register_form.password_again.data:
        return render_template('login.html',
                               form=login_form,
                               form2=register_form,
                               message="Пароли не совпадают", title="Авторизация")
    db_sess = db_session.create_session()

    # проверка на уникальность почты
    if db_sess.query(User).filter(User.email == register_form.email.data).first():
        return render_template('login.html',
                               form=login_form,
                               form2=register_form,
                               message="Такой пользователь уже есть", title="Авторизация")
    # создание пользователя
    user = User(
        name=register_form.name.data,
        surname=register_form.surname.data,
        email=register_form.email.data,
        liked_shops=",",
        liked_goods=",",
        shops_created=","
    )
    user.set_password(register_form.password.data)  # задание пароля
    db_sess.add(user)  # добавление пользователя
    db_sess.commit()
    return redirect('/access')


@app.route('/login', methods=['POST'])
def login():
    """Функция-обработчик для авторизации пользователя"""
    register_form = RegisterForm()  # необходимые формы
    login_form = LoginForm()  # необходимые формы

    db_sess = db_session.create_session()

    # загрузка пользователя
    user = db_sess.query(User).filter(User.email == login_form.email.data).first()
    # проверка на правильность пароля и почты
    if user and user.check_password(login_form.password.data):
        login_user(user, remember=login_form.remember_me.data)
        return redirect("/store")
    # обработка ошибок ввода
    return render_template('login.html',
                           message="Неправильный email или пароль",
                           form=login_form,
                           form2=register_form, title="Авторизация")


@app.route('/my_profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Функция страницы моего профиля"""
    ch_name = ChangeName()  # форма для изменения
    ch_password = ChangePassword()  # форма для изменения
    ch_email = ChangeEmail()  # форма для изменения
    user = current_user  # данные о пользоваетеле

    liked_goods = user.liked_goods.split(",")  # понравившиеся товары (id)
    like_shops = user.liked_shops.split(",")  # понравившиеся магазины (id)

    db_sess = db_session.create_session()
    my_shops = db_sess.query(Shop).filter(Shop.creator_id == current_user.id).all()  # созданные магазины
    my_goods = db_sess.query(Good).filter(Good.id.in_(liked_goods))  # понравившиеся товары (список объектов)
    my_like_shops = db_sess.query(Shop).filter(Shop.id.in_(like_shops))  # понравившиеся магазины (список объектов)
    return render_template("my_profile.html", name=ch_name,
                           password=ch_password, email=ch_email,
                           user=user, shops=my_shops, title="Мой профиль", goods=my_goods, like_shops=my_like_shops)


@login_required
@app.route('/change_name', methods=['POST'])
def change_name():
    """Фунция для обработки смены имени пользователя"""
    ch_name = ChangeName()  # необходимая форма
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()  # пользователь
    user.name = ch_name.new_name.data  # изменение
    user.surname = ch_name.new_surname.data  # изменение
    db_sess.commit()
    return redirect("/my_profile")


@login_required
@app.route('/change_email', methods=['POST'])
def change_email():
    """Фунция для обработки смены электронной почты пользователя"""
    ch_email = ChangeEmail()  # необходимая форма
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()  # пользователь
    # проверка на доступность email
    if db_sess.query(User).filter(User.email == ch_email.new_email.data).first():
        user.email = ch_email.new_email.data  # изменение
        db_sess.commit()
        return redirect("/my_profile")
    return redirect("/my_profile")


@login_required
@app.route('/change_password', methods=['POST'])
def change_password():
    """Фунция для обработки смены пароля пользователя"""
    ch_password = ChangePassword()  # необходимая форма
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()  # пользователь
    user.set_password(ch_password.new_password.data)  # изменение с помощью хеширования
    db_sess.commit()
    return redirect("/my_profile")


if __name__ == '__main__':
    db_session.global_init("db/market.db")  # создание/инициализация базы данных
    db_sess = db_session.create_session()
    port = int(os.environ.get("PORT", 5000))  # создаём порт сервера (в основном для Heroku)
    app.run(host='0.0.0.0', port=port)  # фиксируем запуск
