import os
import PIL
from PIL import Image

from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.telephone_util import check_number
from data.__all_models import User, LoginForm, RegisterForm, ChangeEmail, ChangePassword, ChangeName, CreateShop
from data.__all_models import Shop, AddGood, Good

UPLOAD_FOLDER = ''
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.errorhandler(401)
def problem_401(e):
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/all_shops")
def all_shops():
    db_sess = db_session.create_session()
    created_shops = sorted(db_sess.query(Shop).limit(10).all(), key=lambda x: -x.likes)
    return render_template("shops.html", shops=created_shops, title="Все Магазины")


@app.route("/shop/<shop_id>")
def shop(shop_id):
    db_sess = db_session.create_session()
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()

    shop_goods_find = current_shop.goods_id.split(",")
    shop_goods = db_sess.query(Good).filter(Good.id.in_(shop_goods_find))
    return render_template("shop.html", shop=current_shop, goods=shop_goods, title=current_shop.name)


@app.route("/shop/<shop_id>/<good_id>")
def good(shop_id, good_id):
    db_sess = db_session.create_session()
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    current_good = db_sess.query(Good).filter(Good.id == good_id).first()
    list_of_pictures = filter(lambda x: "." in x, os.listdir(f"static/img/shops/{shop_id}/goods/{good_id}"))

    return render_template("good.html", shop=current_shop, good=current_good,
                           title=current_good.name, lst_pic=list_of_pictures)


@login_required
@app.route("/shop/<shop_id>/create_good", methods=["POST", "GET"])
def create_good(shop_id):
    form = AddGood()
    db_sess = db_session.create_session()
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    categories = open("db/groups.txt", encoding="UTF-8").read().split("\n")
    if current_shop.creator_id == current_user.id:
        return render_template("create_good.html", form=form, categories=categories,
                               shop=current_shop, title="Добавить товар")
    else:
        return "no permission"


@login_required
@app.route("/shop/<shop_id>/creation_good", methods=["POST"])
def creation_good(shop_id):
    db_sess = db_session.create_session()
    categories = open("db/groups.txt", encoding="UTF-8").read().split("\n")
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    form_creation = AddGood()
    if current_shop.creator_id == current_user.id:
        file = request.files['file']
        desc = request.form.get('text')
        group = request.form.get('select_city')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

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
            current_shop.goods_id += f"{good.id},"
            db_sess.add(good)
            db_sess.commit()

            os.mkdir(f"static/img/shops/{current_shop.id}/goods/{good.id}")
            app.config['UPLOAD_FOLDER'] = f"static/img/shops/{current_shop.id}/goods/{good.id}"
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
    form_creation = CreateShop()
    cities = open("db/cities.txt", encoding="UTF-8").read().split("\n")
    return render_template("create_shop.html", title="Создать Магазин", form=form_creation,
                           cities=cities)


@login_required
@app.route("/create", methods=["POST"])
def create():
    form_creation = CreateShop()
    cities = open("db/cities.txt", encoding="UTF-8").read().split("\n")

    file = request.files['file']
    desc = request.form.get('text')
    phone = form_creation.phone.data
    city = request.form.get('select_city')
    if ("+" in check_number(phone)) or (phone == ""):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
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
            current_user.shops_created += f"{shop.id},"
            db_sess = db_session.create_session()
            db_sess.add(shop)
            db_sess.commit()

            app.config['UPLOAD_FOLDER'] = f"static/img/shops/{shop.id}"
            os.mkdir(f"static/img/shops/{shop.id}")
            os.mkdir(f"static/img/shops/{shop.id}/goods")
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
    return redirect("/store")


@app.route('/access', methods=['GET', 'POST'])
def log():
    form = LoginForm()
    form2 = RegisterForm()
    return render_template('login.html', form=form, form2=form2, message="")


@app.route("/store")
def store():
    db_sess = db_session.create_session()
    goods = db_sess.query(Good).filter(Good.active).limit(20).all()
    return render_template("store.html", title="Магазин", goods=goods)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/access")


@app.route('/register', methods=['POST'])
def register():
    register_form = RegisterForm()
    login_form = LoginForm()
    if register_form.password.data != register_form.password_again.data:
        return render_template('login.html',
                               form=login_form,
                               form2=register_form,
                               message="Пароли не совпадают", title="Авторизация")
    db_sess = db_session.create_session()
    if db_sess.query(User).filter(User.email == register_form.email.data).first():
        return render_template('login.html',
                               form=login_form,
                               form2=register_form,
                               message="Такой пользователь уже есть", title="Авторизация")
    user = User(
        name=register_form.name.data,
        surname=register_form.surname.data,
        email=register_form.email.data,
        liked_shops=","
    )
    user.set_password(register_form.password.data)
    db_sess.add(user)
    db_sess.commit()
    return redirect('/store')


@app.route('/login', methods=['POST'])
def login():
    register_form = RegisterForm()
    login_form = LoginForm()

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == login_form.email.data).first()
    if user and user.check_password(login_form.password.data):
        login_user(user, remember=login_form.remember_me.data)
        return redirect("/store")
    return render_template('login.html',
                           message="Неправильный email или пароль",
                           form=login_form,
                           form2=register_form, title="Авторизация")


@app.route('/my_profile', methods=['GET', 'POST'])
@login_required
def profile():
    ch_name = ChangeName()
    ch_password = ChangePassword()
    ch_email = ChangeEmail()
    user = current_user

    liked_shops = user.liked_shops.split(",")
    db_sess = db_session.create_session()
    my_shops = db_sess.query(Shop).filter(Shop.creator_id == current_user.id).all()
    my_goods = db_sess.query(Good).filter(Good.id.in_(liked_shops))

    return render_template("my_profile.html", name=ch_name,
                           password=ch_password, email=ch_email,
                           user=user, shops=my_shops, title="Мой профиль", goods=my_goods)


@login_required
@app.route('/change_name', methods=['POST'])
def change_name():
    ch_name = ChangeName()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.name = ch_name.new_name.data
    user.surname = ch_name.new_surname.data
    db_sess.commit()
    return redirect("/my_profile")


@login_required
@app.route('/change_email', methods=['POST'])
def change_email():
    ch_email = ChangeEmail()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.email = ch_email.new_email.data
    db_sess.commit()
    return redirect("/my_profile")


@login_required
@app.route('/change_password', methods=['POST'])
def change_password():
    ch_password = ChangePassword()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.set_password(ch_password.new_password.data)
    db_sess.commit()
    return redirect("/my_profile")


if __name__ == '__main__':
    db_session.global_init("db/market.db")
    db_sess = db_session.create_session()
    app.run()
