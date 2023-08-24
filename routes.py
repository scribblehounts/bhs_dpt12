from flask import Flask,request, render_template,session,jsonify,redirect
import random
import math
#from flask_qrcode import QRcode
import sqlite3
import json

app = Flask(__name__)

app.secret_key = 'serversecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

@app.route("/",methods=["GET","POST"])
def beginorder(): 
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM fooditems')
    foods = cur.fetchall()

    cur.execute('SELECT * FROM categories')
    categories = cur.fetchall()

    if 'cart' not in session: # view if session has cart 
        session['cart'] = []

    phone = session.get('phone')

    if phone: # view if current session has alrdy ordered
        cur.execute('SELECT * FROM Orders WHERE phonenumb=?', (phone,))
        order_details = cur.fetchone()

        if order_details:
            return redirect("/orderstatus") # prevent access to order page if current session alrdy in place

    if request.method == "POST": # post method
        if "addfood" in request.form: # adding food to cart
            cart_list = session['cart']
            cart_list.append(request.form["addfood"])
            session['cart'] = cart_list

            # Redirect back to the main page after adding the food to the cart
            return redirect('/')

        if "food_id" in request.form: # food show up when clicking on grid item
            cur.execute('SELECT food_name,cost,image,description,food_id From fooditems WHERE food_id=?',(request.form["food_id"],))
            foodresults = cur.fetchall()

            return render_template("order.html", foods=foods, categories=categories, showing=True, food=foodresults, foodcart=session['cart'], foodlength=len(session['cart']))

    return render_template("order.html", foods=foods, categories=categories, showing=False, foodcart=session['cart'], foodlength=len(session['cart']))


@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()

    # Handle form submission for new reviews
    if request.method == "POST":
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        rating = request.form["rating"]
        ratingmessage = request.form["ratingmessage"]

        cur.execute("INSERT INTO Reviews (firstname, lastname, rating, ratingmessage) VALUES(?, ?, ?, ?)", (firstname, lastname, rating, ratingmessage))
        conn.commit()

        # Redirect back to the same page after processing the form
        return redirect('/reviews')

    # Fetch all reviews from the database
    cur.execute('SELECT * FROM Reviews')
    reviews = cur.fetchall()

    return render_template("reviews.html", reviews=reviews)


@app.route("/orderstatus")
def orderstatus():
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()

    # fetch the phone number from the session
    phone = session.get('phone')

    if phone:
        cur.execute('SELECT * FROM Orders WHERE phonenumb=?', (phone,))
        order_details = cur.fetchone()

        if order_details:
            # conv. the foodlist string back to a list
            print(order_details[4])
            food_ids = json.loads(order_details[4])
            
            cur.execute('SELECT food_name, cost, image, description FROM fooditems WHERE food_id IN ({})'.format(','.join(['?']*len(food_ids))), food_ids)
            foods = cur.fetchall()
            return render_template("orderstatus.html", order_status=order_details[5], foods=foods,foodcart=session['cart'], foodlength=len(session['cart']))
        else:
            return render_template("orderstatus.html", order_status=None)
    else:
        return render_template("orderstatus.html", order_status=None)




@app.route("/cart", methods=["GET","POST"])
def cart():
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()

    if 'cart' not in session:
        session['cart'] = []

    formattedtbl = []

    if request.method == "POST":
        if "removefood" in request.form:
            cart_list = session['cart']

            if request.form["removefood"] in cart_list:
                cart_list.remove(request.form["removefood"])
                session['cart'] = cart_list

            # Redirect back to the cart page after removing the food from the cart
            return redirect('/cart')

    for i in session['cart']:
        cur.execute('SELECT food_name,cost,image,description,food_id From fooditems WHERE food_id=?', (i,))
        foodresults = cur.fetchall()
        formattedtbl.append(foodresults[0])
        # append food items into table 

    return render_template('cart.html', foodcart=formattedtbl, foodlength=len(session['cart']))



@app.route("/admin", methods=["GET","POST"])
def admin():
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()

    if request.method == "POST":
        if "confirmorder" in request.form:
            cur.execute('UPDATE Orders SET status="progress" WHERE orderid=?', (request.form["confirmorder"],))

        if "cancelorder" in request.form:
            cur.execute('DELETE FROM Orders WHERE orderid=?', (request.form["cancelorder"],))

        if "readypickup" in request.form:
            cur.execute('DELETE FROM Orders WHERE orderid=?', (request.form["readypickup"],))

        conn.commit()

        # Redirect back to the admin page after performing the action
        return redirect('admin')

    cur.execute('SELECT * From Orders')
    results = cur.fetchall()

    cur.execute('SELECT * FROM fooditems')
    foods = cur.fetchall()

    return render_template("admin.html", order=results, foods=foods)


@app.route("/submitorder")
def submit():
    data = request.args
    fname = data.get('fname') # first name
    lname = data.get('lname') # last name
    phone = data.get('phone') # phone ( identifier )

    foods = json.dumps(session['cart'])

    conn = sqlite3.connect('data.db')
    cur = conn.cursor()

    cur.execute("INSERT INTO Orders (firstname,lastname,phonenumb,foodlist,status) VALUES(?, ?, ?, ?,?)", (fname, lname, str(phone), foods,'avail'))
    conn.commit()

    # Store the phone number in the session
    session['phone'] = str(phone)

    session['cart'] = []
    return redirect("/orderstatus")

# misc funcs

@app.errorhandler(404) # 404 for non pages
def page_not_found(e):
    return render_template('404.html'),404
    

@app.template_filter('to_dict') # template filter, convert json string to json obj
def to_dict(my_string):
    
    return json.loads(my_string)

if __name__ == '__main__':
    app.run(debug=True)
