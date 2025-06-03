import smtplib

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.ehlo()
        server.starttls()
        server.login('bookappex@gmail.com', 'amvc rkej gntp ypga')
        print("SMTP подключение успешно!")
except Exception as e:
    print(f"SMTP ошибка: {str(e)}")