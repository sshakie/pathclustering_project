from flask import *
from flask_login import *
from data.users import User
from data.orders import Orders
from blanks.loginform import LoginForm
from blanks.registerform import RegisterForm
from blanks.orderform import OrderForm
from data.db_session import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_promises'

lm = LoginManager()
lm.init_app(app)
global_init('db/sql.db')

db_sess = create_session()
if not db_sess.query(User).filter(User.name == 'admin').first():
    user = User()
    user.name = 'admin'
    user.email = 'admin@admin.py'
    user.status = 'admin'
    user.set_password('admin')
    db_sess.add(user)
    db_sess.commit()


@lm.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', message='Неправильный логин или пароль', form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/')
def homepage():
    if current_user.is_authenticated:
        db_sess = create_session()
        return render_template('homepage.html', sql=db_sess.query(Orders).all(), name=current_user.name)
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/login')

    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user:
            return render_template('register.html', message='Данная почта уже зарегистрирована. Попробуйте войти.',
                                   form=form)
        else:
            db_sess = create_session()
            user = User()
            user.name = form.name.data
            user.email = form.email.data
            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.commit()

            login_user(user, remember=form.remember_me.data)
            return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


def get_goods():
    goods = ['Пицца-пепперони', 'Суши филадельфия', 'Игровой стул']
    return goods


@app.route('/add_job', methods=['GET', 'POST'])
def add_job():
    if current_user.is_authenticated:
        form = OrderForm()
        form.goods.choices = get_goods()
        if form.validate_on_submit():
            db_sess = create_session()
            order = db_sess.query(Orders).filter(Orders.address == form.address.data).first()
            if order:
                return render_template('add_order.html', title='Данному адресу уже доставляют', form=form)

            db_sess = create_session()
            order = Orders()
            order.address = form.address.data
            order.city = form.city.data
            order.goods = ', '.join(form.goods.data)
            order.scheduled_date = form.scheduled_date.data
            order.is_delivered = form.is_delivered.data
            db_sess.add(order)
            db_sess.commit()
            return redirect('/')
        return render_template('add_order.html', title='Добавление заказа', form=form)
    else:
        return redirect('/login')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


def main():
    app.run()


if __name__ == '__main__':
    main()
