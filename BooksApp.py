from flask import Flask, abort, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import secrets
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging
import paypalrestsdk

from extension import db
from models import Authorization, Books, Bookmark, Order

logging.basicConfig(filename='app.log', level=logging.ERROR)

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///BooksAppDB.db'
    app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))  # 64 символа

    app.config['PAYPAL_MODE'] = 'sandbox'  # 'live' для продакшена
    app.config['PAYPAL_CLIENT_ID'] = 'AYpJZkrz60Y-YUaLVAQjnHLdYXVe9GmRuGfesTQVlfcQ0wN54FUR7hA4p-ToZh_rs82Sew4W0a9-xAZH'
    app.config['PAYPAL_CLIENT_SECRET'] = 'EHSqoNtVWFxWVkLWhg45JeK_03Pne9iS3eTWQWhaNLY1vpvjK7TJ5oMSMKA0rZLAA4bOIkVN4N3kc5S9'
    if not app.secret_key:
        raise ValueError("Не задан FLASK_SECRET_KEY")
    # Инициализация расширений
    db.init_app(app)
    
    return app

app = create_app()
print(app)

@app.errorhandler(500)
def internal_error(e):
   logging.error(f"500 Error: {str(e)}")
   return "Ошибка сервера", 500, e

#Проверка на вход пользователя
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Требуется авторизация', 'error')
            return redirect(url_for('Log_in'))
        return f(*args, **kwargs)
    return decorated
#Проверка на администратора
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        user = Authorization.query.filter_by(Name=session['username']).first()
        if user.Rank != 'Admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated

#Регистрация пользователей
@app.route("/Registration", methods=['POST', 'GET'])
def Registration():
    if request.method == 'POST':
        username = request.form['Login']
        pswrd_check = request.form['Password']
       
        if Authorization.query.filter_by(Name=username).first():
            flash('Данный логин уже существует!')
            return redirect('/Registration') 
        if len(username) < 4:
            flash('Логин должен содержать не менее 4 символов.')
            return redirect('/Registration')
        if len(pswrd_check) < 6:
            flash('Пароль должен содержать не менее 6 символов.')
            return redirect('/Registration')
        
        pswrd = generate_password_hash(request.form['Password'])
        rank = "User"
        reg = Authorization(Name = username, Password = pswrd, Rank = rank)
        try:
            db.session.add(reg)
            db.session.commit()

            session['username'] = username
            return redirect('/')
        except:
                return 'При регистрации что-то пошло не так'
    else:        
        return render_template('Registration.html')
#Вход в аккаунт
@app.route("/Log_in", methods=['POST', 'GET'])
def Log_in():
    if request.method == 'POST':
        username = request.form['Login']
        pswrd = request.form['Password']
        
        # Поиск пользователя в базе данных
        user = Authorization.query.filter_by(Name=username).first()
        
        if user and check_password_hash(user.Password, pswrd):
            session['username'] = username
            return redirect('/')  # Главная страница
        else:
            flash('Неверное имя пользователя или пароль!')
            return render_template('Log_in.html')
    return render_template('Log_in.html')
#logout       
@app.route('/logout')
def logout():
    session.pop('username', None)  # Удаление имени пользователя из сессии
    return redirect('/')


#Главная
@app.route("/Main")
@app.route("/")
def Main():
    username = session.get('username') 
    books = Books.query.all()
    admin=False
    if 'username' not in session:
        return render_template('Main.html', books=books)
    else:
        user = Authorization.query.filter_by(Name=username).first()
        if user.Rank == 'Admin':
            admin=True
        return render_template('Main.html', books=books, username=username, admin=admin)

#Просмотр книги
@app.route('/book/<int:id>')
def book_detail(id):
    book = Books.query.get_or_404(id)
    username = session.get('username')
    #cover_path = book.Cover
    #cover_url= url_for('static', filename=cover_path)
    
    user = Authorization.query.filter_by(Name=username).first()

    if 'username' not in session:
        return render_template('Book.html', book=book,existing_bookmark=False)#, cover_url = cover_url
    else:
        existing_bookmark = Bookmark.query.filter_by(user_id=user.id, book_id=id).first()
        admin=False
        if user.Rank == 'Admin':
            admin=True
        return render_template('Book.html', book=book, username=username, admin=admin, existing_bookmark=existing_bookmark) #cover_url = cover_url,

#Добавление книг в базу данных  
@app.route("/AddBooks", methods=['POST', 'GET'])
@admin_required
def AddBooks():
    username = session.get('username')
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        about = request.form['about']
        file_path = "book/"+request.form['file_path']
        cover = "Cover/"+request.form['cover']
        cost = request.form['cost'] 
        Add = Books(Title = title, Cover = cover, Author = author, About = about, File_path = file_path, Cost = cost )
        if Books.query.filter_by(Title=title).first():
            return "Данная книга уже существует!"
        try:
            db.session.add(Add)
            db.session.commit()
            return redirect('/')
        except:
            return 'При добавлении книги что-то пошло не так'
    else:        
        return render_template('AddBooks.html', username=username)

#Удаление книг
@app.route("/book/<int:id>/del")
@admin_required
def delete_book(id):
    del_book = Books.query.get_or_404(id)
    try:
        db.session.delete(del_book)
        db.session.commit()
        return redirect('/')
    except:
        return 'При удалении книги что-то пошло не так'    

#Изменение книг
@app.route("/book/<int:id>/edit", methods=['POST', 'GET'])
@admin_required
def BookUpdate(id):
    username = session.get('username')
    edit = Books.query.get_or_404(id)
    if request.method == 'POST':
        edit.Title = request.form['title']
        edit.Author = request.form['author']
        edit.About = request.form['about']
        edit.File_path = request.form['file_path']
        edit.Cover = request.form['cover']
        edit.Cost = request.form['cost']
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'При изменении что-то пошло не так'
    else:   
        
        return render_template('Book_edit.html', edited=edit, username=username)

#Закладки
@login_required
@app.route('/Bookmarks')
def Bookmarks():
    username = session.get('username')
    user = Authorization.query.filter_by(Name=session['username']).first()
    bookmarks = Bookmark.query.filter_by(user_id=user.id).options(    db.joinedload(Bookmark.book)    ).all()
    return render_template('Bookmarks.html', bookmarks=bookmarks,  username=username)

#Добавление закладок
@app.route('/add_bookmark/<int:book_id>', methods=['POST'])
@login_required
def add_bookmark(book_id):
    user = Authorization.query.filter_by(Name=session['username']).first()

    #Проверка, существует ли уже закладка
    existing_bookmark = Bookmark.query.filter_by(user_id=user.id, book_id=book_id).first()

    #Удаление закладки если она уже существовала
    if existing_bookmark:
        flash('Книга убрана из закладок!')
        return remove_bookmark(existing_bookmark.id)
    
    # Если закладки нет, добавляем новую
    bookmark = Bookmark(user_id=user.id, book_id=book_id)
    db.session.add(bookmark)
    db.session.commit()

   
    
    str_id = str(book_id)
    flash('Книга добавлена в закладки!')
    return redirect('/book_log/'+str_id, )

#Удаление закладок
@app.route('/remove_bookmark/<int:bookmark_id>', methods=['POST'])
@login_required
def remove_bookmark(bookmark_id):
    bookmark = Bookmark.query.get(bookmark_id)
    str_id = str(bookmark.book_id)
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
    
    return redirect('/book_log/'+str_id)

#Проверка на добавленную закладку
@app.route('/check_bookmark/<int:book_id>', methods=['GET'])
def check_bookmark(book_id):
    if 'username' not in session:
        flash('Пожалуйста, войдите в систему, чтобы добавлять закладки.')
        return redirect('/Log_in')
    
    user = Authorization.query.filter_by(Name=session['username']).first()

    #Проверка, существует ли уже закладка
    has_bookmark = Bookmark.query.filter_by(user_id=user.id, book_id=book_id).first() is not None

    #Если она уже существовала
    if has_bookmark:
         return {"has_bookmark" : True}
    return {"has_bookmark" : False}


#Поиск книг по названию
@app.route('/search_books', methods=['GET'])
def search_books():
    title = request.args.get('title', '')
    books = []
    username = session.get('username')
    user = Authorization.query.filter_by(Name=username).first()
    if title:
        books = Books.query.filter(Books.Title.ilike(f'%{title}%')).all()  # Поиск с нечувствительностью к регистру
    if 'username' not in session:
        return render_template('Main.html', books=books) # Возвращаем шаблон если зарегистрирован
        # Проверка ранга пользователя
    if user.Rank == 'Admin':
        admin = True
        return render_template('Main.html', books=books, username=username, admin = admin)  # Перенаправление для админа
    else:
        return render_template('Main.html', books=books, username=username)  # Перенаправление для обычного пользователя


#Чтение книг
@app.route('/read_book/<int:book_id>')
@login_required
def read_book(book_id):
    book = Books.query.get_or_404(book_id)

    if not os.path.exists(os.path.join(app.static_folder, book.File_path)):
        abort(404)
    

#Создание пользователя с уровнем доступа админ если его еще нет
def create_admin_user():
    admin_user = Authorization.query.filter_by(Name='admin').first()
    if not admin_user:
        new_admin = Authorization(
            Name='admin',
            Password=generate_password_hash('admin!secure!pswrd'),  # Замените на ваш пароль
            Rank='Admin'
        )
        db.session.add(new_admin)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")
    return app


#class Config:
 #   PAYPAL_MODE = 'sandbox'  # или 'live' для продакшена
 #   PAYPAL_CLIENT_ID = 'ваш_client_id'
 #   PAYPAL_CLIENT_SECRET = 'ваш_client_secret'

paypalrestsdk.configure({
    "mode": app.config['PAYPAL_MODE'],
    "client_id": app.config['PAYPAL_CLIENT_ID'],
    "client_secret": app.config['PAYPAL_CLIENT_SECRET']
})

# Маршрут для создания платежа (обновленная версия)
@app.route("/create_payment/<int:book_id>", methods=['POST'])
@login_required
def create_payment(book_id):
    try:
        book = Books.query.get_or_404(book_id)
        user = Authorization.query.filter_by(Name=session['username']).first()
        
        # Проверяем, не купил ли пользователь уже эту книгу
        existing_order = Order.query.filter_by(
            user_id=user.id, 
            book_id=book.id,
            status='paid'
        ).first()
        
        if existing_order:
            flash('Вы уже приобрели эту книгу!', 'info')
            return redirect(url_for('book_detail', id=book.id))

        # Создаем заказ в БД
        order = Order(
            book_id=book.id,
            user_id=user.id,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()

        # Настройка платежа PayPal
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": url_for("execute_payment", order_id=order.id, _external=True),
                "cancel_url": url_for("payment_cancelled", order_id=order.id, _external=True),
            },
            "transactions": [{
                "amount": {
                    "total": "{0:.2f}".format(float(book.Cost)),
                    "currency": "USD",
                },
                "description": f"Покупка книги: {book.Title}",
                "item_list": {
                    "items": [{
                        "name": book.Title,
                        "price": "{0:.2f}".format(float(book.Cost)),
                        "currency": "USD",
                        "quantity": 1
                    }]
                }
            }]
        })

        if payment.create():
            order.paypal_payment_id = payment.id
            db.session.commit()
            
            # Находим URL для перенаправления на PayPal
            for link in payment.links:
                if link.method == "REDIRECT":
                    redirect_url = str(link.href)
                    return redirect(redirect_url)
            
            flash('Не удалось получить ссылку для оплаты', 'error')
        else:
            error_msg = payment.error.get('message', 'Неизвестная ошибка PayPal')
            flash(f'Ошибка при создании платежа: {error_msg}', 'error')
            app.logger.error(f"PayPal error: {payment.error}")
            
    except Exception as e:
        db.session.rollback()
        flash('Произошла ошибка при обработке платежа', 'error')
        app.logger.error(f"Payment processing error: {str(e)}")
    
    return redirect(url_for('book_detail', id=book.id))

# Маршрут для подтверждения платежа (обновленный)
@app.route("/execute_payment/<int:order_id>")
@login_required
def execute_payment(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        user = Authorization.query.filter_by(Name=session['username']).first()
        
        # Проверяем, что заказ принадлежит текущему пользователю
        if order.user_id != user.id:
            flash('Этот заказ не принадлежит вам', 'error')
            return redirect(url_for('Main'))

        payer_id = request.args.get("PayerID", "")
        payment = paypalrestsdk.Payment.find(order.paypal_payment_id)

        if payment.execute({"payer_id": payer_id}):
            order.status = "paid"
            db.session.commit()
            
            # Здесь логика предоставления доступа к книге
            book_id = order.book_id

            bookmark = Bookmark(user_id=user.id, book_id=book_id)
            db.session.add(bookmark)
            db.session.commit()
      
            flash('Книга добавлена в закладки!')
  
            return redirect(url_for("payment_success", order_id=order.id))
        else:
            error_msg = payment.error.get('message', 'Неизвестная ошибка PayPal')
            flash(f'Ошибка при выполнении платежа: {error_msg}', 'error')
            app.logger.error(f"PayPal execute error: {payment.error}")
            
    except Exception as e:
        db.session.rollback()
        flash('Произошла ошибка при подтверждении платежа', 'error')
        app.logger.error(f"Execute payment error: {str(e)}")
    
    return redirect(url_for('payment_failed', order_id=order.id))
# Маршрут для успешной оплаты
@app.route("/payment_success/<int:order_id>")
@login_required
def payment_success(order_id):
    order = Order.query.get_or_404(order_id)
    book = Books.query.get_or_404(order.book_id)
    return render_template("payment_success.html", 
                         order=order, 
                         book=book,
                         username=session.get('username'))

# Маршрут для отмененного платежа
@app.route("/payment_cancelled/<int:order_id>")
@login_required
def payment_cancelled(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = "cancelled"
    db.session.commit()
    return render_template("payment_cancelled.html", 
                         order=order,
                         username=session.get('username'))

# Маршрут для неудачного платежа
@app.route("/payment_failed/<int:order_id>")
@login_required
def payment_failed(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = "failed"
    db.session.commit()
    return render_template("payment_failed.html", 
                         order=order,
                         username=session.get('username'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем все таблицы, если их еще нет
        create_admin_user()  # Создаем пользователя с уровнем доступа админ, если его нет(admin!secure!pswrd)ssl_context="adhoc",
    app.run( debug=True)