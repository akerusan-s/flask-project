import os

from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.__all_models import User, LoginForm, RegisterForm, ChangeEmail, ChangePassword, ChangeName

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


@app.route('/test_upl', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


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
    return render_template("my_profile.html", name=ch_name, password=ch_password, email=ch_email, user=user)


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
