import datetime
from time import timezone
from flask import url_for
from extension import db
import os

#База данных пользователей
class Authorization(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    Name = db.Column(db.String(100), nullable = False)
    Password = db.Column(db.String(100), nullable = False)
    Rank = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(100), nullable=False, unique=True)  # Добавляем email
    email_confirmed = db.Column(db.Boolean, default=False)  # Подтвержден ли email
    email_confirmation_token = db.Column(db.String(100))  # Токен для подтверждения
    token_expiration = db.Column(db.DateTime)  # Срок действия токена
    pass
#База данных книг
class Books(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    Title = db.Column(db.String(100), nullable = False)
    Cover = db.Column(db.String(100), nullable = False)
    Author = db.Column(db.String(100), nullable = False)
    About = db.Column(db.Text, nullable = False)
    File_path = db.Column(db.String(100), nullable = False)
    Cost = db.Column(db.Float, nullable = False)
    @property
    def cover_url(self):
        # Заменяем обратные слеши на прямые
        clean_path = self.Cover.replace('\\', '/')
        return url_for('static', filename=f'uploads/{clean_path}')

    @property
    def book_file_url(self):
        clean_path = self.File_path.replace('\\', '/')
        return url_for('static', filename=f'uploads/{clean_path}')
    
#База данных закладок пользователей
class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    user_id = db.Column(db.Integer, db.ForeignKey('authorization.id'), nullable=False)  
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)  

    user = db.relationship('Authorization', backref='bookmarks')  
    book = db.relationship('Books', backref='bookmarks') 
    pass
#База данных платежей
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('authorization.id'), nullable=False)  
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)  # Changed to nullable=False
    status = db.Column(db.String(20), default="pending")
    paypal_payment_id = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    
    # Explicit relationship
    book = db.relationship('Books', backref='orders')
    user = db.relationship('Authorization', backref='orders')
