import os
import PIL
from PIL import Image

from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.telephone_util import check_number
from data.__all_models import User, LoginForm, RegisterForm, ChangeEmail, ChangePassword, ChangeName, CreateShop
from data.__all_models import Shop

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
    created_shops = db_sess.query(Shop).limit(10).all()
    return render_template("shops.html", shops=created_shops)


@app.route("/shop/<shop_id>")
def shop(shop_id):
    db_sess = db_session.create_session()
    current_shop = db_sess.query(Shop).filter(Shop.id == shop_id).first()
    return render_template("shop.html", shop=current_shop)


@app.route("/create_shop", methods=["POST", "GET"])
def create_shop():
    form_creation = CreateShop()
    cities = open("db/cities.txt", encoding="UTF-8").read().split("\n")
    return render_template("create_shop.html", title="Создать Магазин", form=form_creation, cities=cities)


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
            db_sess = db_session.create_session()
            db_sess.add(shop)
            db_sess.commit()

            app.config['UPLOAD_FOLDER'] = f"static/img/shops/{shop.id}"
            os.mkdir(f"static/img/shops/{shop.id}")
            os.mkdir(f"static/img/shops/{shop.id}/goods")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            maxsize = (628, 628)
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
    return render_template("store.html", title="Магазин")


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
                               message="Пароли не совпадают")
    db_sess = db_session.create_session()
    if db_sess.query(User).filter(User.email == register_form.email.data).first():
        return render_template('login.html',
                               form=login_form,
                               form2=register_form,
                               message="Такой пользователь уже есть")
    user = User(
        name=register_form.name.data,
        surname=register_form.surname.data,
        email=register_form.email.data,
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
                           form2=register_form)


@app.route('/my_profile', methods=['GET', 'POST'])
@login_required
def profile():
    ch_name = ChangeName()
    ch_password = ChangePassword()
    ch_email = ChangeEmail()
    user = current_user

    db_sess = db_session.create_session()
    my_shops = db_sess.query(Shop).filter(Shop.creator_id == current_user.id).all()
    return render_template("my_profile.html", name=ch_name,
                           password=ch_password, email=ch_email,
                           user=user, shops=my_shops)


@app.route('/change_name', methods=['POST'])
def change_name():
    ch_name = ChangeName()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.name = ch_name.new_name.data
    user.surname = ch_name.new_surname.data
    db_sess.commit()
    return redirect("/my_profile")
    # return render_template("my_profile.html", name=ch_name, password=ch_password, email=ch_email, user=current_user)


@app.route('/change_email', methods=['POST'])
def change_email():
    ch_email = ChangeEmail()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.email = ch_email.new_email.data
    db_sess.commit()
    return redirect("/my_profile")
    # return render_template("my_profile.html", name=ch_name, password=ch_password, email=ch_email, user=current_user)


@app.route('/change_password', methods=['POST'])
def change_password():
    ch_password = ChangePassword()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.set_password(ch_password.new_password.data)
    db_sess.commit()
    return redirect("/my_profile")
    # return render_template("my_profile.html", name=ch_name, password=ch_password, email=ch_email, user=current_user)


if __name__ == '__main__':
    db_session.global_init("db/market.db")
    db_sess = db_session.create_session()
    app.run()
