from data import db_session, users_resource
from flask import Flask, render_template, redirect, url_for
from data.__all_models import User,  LoginForm, RegisterForm, SearchForm
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_restful import Api

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.errorhandler(401)
def problem_401(e):
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/', methods=['GET', 'POST'])
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
    return redirect("/")


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
    # return render_template('login.html', form2=register_form, form=login_form)


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


if __name__ == '__main__':
    db_session.global_init("db/market.db")
    db_sess = db_session.create_session()
    app.run()
