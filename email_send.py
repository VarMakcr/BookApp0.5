from flask import current_app, render_template, url_for
from flask_mail import Message
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        try:
            current_app.mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Ошибка отправки email: {str(e)}")

def send_email(to, subject, template, **kwargs):
    """
    Отправка email через Gmail
    :param to: получатель (email)
    :param subject: тема письма
    :param template: имя шаблона (без расширения)
    :param kwargs: переменные для шаблона
    """
    app = current_app._get_current_object()
    
    # Создаем сообщение
    msg = Message(
        subject=subject,
        recipients=[to],
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    
    # Устанавливаем текст и HTML
    msg.body = render_template(f'{template}.txt', **kwargs)
    msg.html = render_template(f'{template}.html', **kwargs)
    
    # Отправляем асинхронно
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
def send_confirmation_email(user):
    # Генерируем токен подтверждения
    token = user.email_confirmation_token
    confirm_url = url_for('confirm_email', token=token, _external=True)
    
    # Отправляем email
    send_email(
        to=user.email,
        subject="Подтверждение регистрации на BookApp",
        template='email/confirm_email',  # Шаблоны в папке templates/email/
        username=user.Name,
        confirm_url=confirm_url
    )