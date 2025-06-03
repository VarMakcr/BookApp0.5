from flask_mail import Message
from flask import render_template, current_app, url_for
from threading import Thread
from extensions.mail import mail

class EmailService:
    @staticmethod
    def send_async_email(app, msg):
        with app.app_context():
            try:
                current_app.logger.info(f"Попытка отправки письма на {msg.recipients}")
                mail.send(msg)  # Используем mail из extensions
                current_app.logger.info("Письмо успешно отправлено")
            except Exception as e:
                current_app.logger.error(f"Ошибка отправки: {str(e)}")
                if hasattr(e, 'smtp_code'):
                    current_app.logger.error(f"SMTP код ошибки: {e.smtp_code}")
                if hasattr(e, 'smtp_error'):
                    current_app.logger.error(f"SMTP ошибка: {e.smtp_error.decode()}")
    @staticmethod
    def send_email(to, subject, template, **kwargs):
        app = current_app._get_current_object()
        msg = Message(
            subject,
            recipients=[to],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        msg.body = render_template(f'email/{template}.txt', **kwargs)
        msg.html = render_template(f'email/{template}.html', **kwargs)
        
        thr = Thread(target=EmailService.send_async_email, args=[app, msg])
        thr.start()
        return thr

    @staticmethod
    def send_confirmation(user, token):
        confirm_url = url_for('confirm_email', token=token, _external=True)
        EmailService.send_email(
            to=user.email,
            subject="Подтверждение email для BookApp",
            template='confirm_email',
            username=user.Name,
            confirm_url=confirm_url
        )

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    
    # Создаём сообщение
    msg = Message(
        subject=subject,
        recipients=[to],
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    msg.body = render_template(f'email/{template}.txt', **kwargs)
    msg.html = render_template(f'email/{template}.html', **kwargs)
    
    # Запускаем в отдельном потоке
    thr = Thread(target=EmailService.send_async_email, args=[app, msg])
    thr.start()
    return thr
