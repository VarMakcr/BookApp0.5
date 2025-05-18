from flask import url_for
from extension import db

#База данных пользователей
class Authorization(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    Name = db.Column(db.String(100), nullable = False)
    Password = db.Column(db.String(100), nullable = False)
    Rank = db.Column(db.String(100), nullable = False)
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
        return url_for('static', filename=self.Cover)

    @property
    def file_url(self):
        return url_for('static', filename=self.File_path)
    pass
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
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))
    status = db.Column(db.String(20), default="pending")  # pending/paid/failed
    paypal_payment_id = db.Column(db.String(50))  # ID платежа PayPal
    pass
