import mysql.connector
from werkzeug.security import generate_password_hash

db=mysql.connector.connect(
    host='localhost',
    user='root',
    password='Root@122',
    database='qr_restaurant'
)
cursor=db.cursor()
username=input('Enter admin username:')
password=input('Enter admin password:')

hashed_pw= generate_password_hash(password)
cursor.execute("INSERT INTO admin_users (username, password_hash) VALUES (%s, %s)", (username, hashed_pw))
db.commit()
db.close()
print('Admin created!')
