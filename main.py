from flask import *
from flask_login import *
from data.users import User
from data.orders import Orders
from blanks.loginform import LoginForm
from blanks.registerform import RegisterForm
from blanks.orderform import OrderForm
from data.db_session import *
from datetime import *
from dateutil.relativedelta import *

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
    return create_session().query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/orders')

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/orders')
        return render_template('login.html', message='Неправильный логин или пароль', form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/')
def homepage():
    if current_user.is_authenticated:
        return redirect('/orders')
    return redirect('/login')


@app.route('/orders', methods=['GET', 'POST'])
def orders():
    if current_user.is_authenticated:
        form = OrderForm()
        db_sess = create_session()
        form.goods.choices = get_goods()
        time_min = (datetime.now() + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M')
        date_max = (datetime.now() + relativedelta(months=2)).strftime('%Y-%m-%dT23:59')

        if form.validate_on_submit():
            db_sess = create_session()
            if db_sess.query(Orders).filter(Orders.phone == form.phone.data).first():
                flash("Заказ по данному номеру телефона уже составлен", "success")
                return render_template('orders.html', sql=db_sess.query(Orders).all(), form=form, time_min=time_min,
                                       date_max=date_max)
            elif len(form.phone.data.replace('+7', '8')) != 11:
                flash("Данный номер телефона неверен/не из России", "success")
                return render_template('orders.html', sql=db_sess.query(Orders).all(), form=form, time_min=time_min,
                                       date_max=date_max)

            order = Orders()
            order.address = form.address.data
            order.city = form.city.data
            order.phone = form.phone.data
            order.goods = ', '.join(form.goods.data)
            order.scheduled_date = form.scheduled_date.data.strftime('%Y-%m-%d %H:%M')
            order.is_delivered = form.is_delivered.data
            db_sess.add(order)
            db_sess.commit()
        return render_template('orders.html', sql=db_sess.query(Orders).all(), form=form, time_min=time_min,
                               date_max=date_max)
    else:
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
            return redirect('/orders')
    return render_template('register.html', title='Регистрация', form=form)


def get_goods():
    goods = ['Пицца-пепперони', 'Суши филадельфия', 'Игровой стул']
    return goods


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


def main():
    app.run()


if __name__ == '__main__':
    main()
