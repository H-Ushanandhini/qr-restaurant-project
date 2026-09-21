from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash
import mysql.connector
from flask import jsonify
app=Flask(__name__)
app.secret_key='mysecret123'

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Root@122',
        database='qr_restaurant'
    )

@app.route('/')
def home():
    return 'Hello, QR Restaurant!'
@app.route('/menu')
def menu():
    db=get_db()
    cursor=db.cursor()
    cursor.execute('SELECT * FROM menu_items')
    items=cursor.fetchall()
    db.close()
    return render_template('menu.html', items=items)
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_id=request.form.get('item_id')
    cart=session.get('cart',{})
    cart[item_id]=cart.get(item_id,0) + 1
    session['cart']=cart
    return redirect('/menu')

@app.route('/cart')
def view_cart():
    cart=session.get('cart',{})
    table_number=session.get('table_number',1)
    if not cart:
        return render_template('cart.html', cart_items=[], total=0, table_number=table_number)
    
    db=get_db()
    cursor=db.cursor()
    cart_items=[]
    total=0
    for item_id , qty in cart.items():
        cursor.execute("SELECT * FROM menu_items WHERE item_id = %s", (item_id,))
        item=cursor.fetchone()
        subtotal=float(item[2])*qty
        total+=subtotal
        cart_items.append((item[1],qty, subtotal))
    db.close()
    return render_template('cart.html', cart_items=cart_items, total=total, table_number=table_number)


@app.route('/place_order', methods=['POST'])
def place_order():
    cart=session.get('cart', {})
    if not cart:
        return redirect('/menu')
    db=get_db()
    cursor=db.cursor()

    cursor.execute("INSERT INTO orders (status) VALUES ('pending')")
    order_id=cursor.lastrowid
    for item_id, qty in cart.items():
        cursor.execute("INSERT INTO order_items(order_id, item_id, quantity) VALUES (%s, %s, %s)",(order_id, item_id, qty))
    db.commit()
    db.close()
    session['cart']={}
    return f'Order placed! Your order ID is {order_id}'

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        db=get_db()
        cursor=db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users WHERE username = %s", (username,))
        admin=cursor.fetchone()
        db.close()

        if admin and check_password_hash(admin['password_hash'],password):
            session['admin_logged_in']=True
            session['admin_username']=admin['username']
            return redirect('/admin/dashboard')
        else:
            return "Invalid username or password"
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    db=get_db()
    cursor=db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders=cursor.fetchall()
    db.close()
    return render_template('admin_dashboard.html', orders=orders)

@app.route('/admin/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    new_status=request.form['status']
    db=get_db()
    cursor=db.cursor()
    cursor.execute('UPDATE orders SET status = %s WHERE order_id = %s', (new_status, order_id))
    db.commit()
    db.close()
    return redirect('/admin/dashboard')

# GET all menu items as JSON
@app.route('/api/menu', methods=['GET'])
def api_get_menu():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_items")
    items = cursor.fetchall()
    db.close()

    for item in items:
        item['price'] = float(item['price'])   # Decimal isn't JSON-friendly

    return jsonify(items)


# GET a single order's status
@app.route('/api/order/<int:order_id>', methods=['GET'])
def api_get_order(order_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()
    db.close()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(order)


# PUT to update an order's status (admin only)
@app.route('/api/order/<int:order_id>', methods=['PUT'])
def api_update_order(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    new_status = request.json.get('status')
    if new_status not in ['Pending', 'Preparing', 'Served']:
        return jsonify({"error": "Invalid status"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id))
    db.commit()
    db.close()

    return jsonify({"message": "Status updated", "order_id": order_id, "status": new_status})

if __name__=='__main__':
    app.run(debug=True) 
    