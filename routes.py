from flask import Flask,request, render_template,session,jsonify,redirect
import random
import math
#from flask_qrcode import QRcode
import sqlite3
import json

app = Flask(__name__)

app.secret_key = 'str(math.floor(random.randint(10000,50000)))'
app.config['SESSION_TYPE'] = 'filesystem'

app.config['SESSION_PERMANENT'] = False

@app.route("/",methods=["GET","POST"])
def mainpage(): #add comments
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM fooditems')
    foods = cur.fetchall()


    
    cur.execute('SELECT * FROM categories')
    categories = cur.fetchall()

    if 'cart' not in session:
        session['cart'] = []

    if request.method == "POST":
        if "addfood" in request.form:

            cart_list = session['cart']
            cart_list.append(request.form["addfood"])
            session['cart'] = cart_list

            return render_template("order.html", foods=foods,categories=categories,showing=False,foodcart= session['cart'],foodlength= len(session['cart']))
            #return jsonify(request.form["foodqueue"])
        
        if "food_id" in request.form:
            cur.execute('SELECT food_name,cost,image,description,food_id From fooditems WHERE food_id=?',(request.form["food_id"],))
            foodresults = cur.fetchall()

            return render_template("order.html", foods=foods,categories=categories,showing=True,food=foodresults,foodcart= session['cart'],foodlength= len(session['cart']))

    return render_template("order.html", foods=foods,categories=categories,showing=False,foodcart= session['cart'],foodlength= len(session['cart']))

@app.route("/reviews")
def reviews():
    return render_template("reviews.html")

@app.route("/orderstatus")
def orderstatus():
    return render_template("orderstatus.html")

@app.route("/cart", methods=["GET","POST"])
def cart():
    
    if 'cart' not in session:
        session['cart'] = []
    
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()

    formattedtbl = []
    
    if request.method == "POST":
        if "removefood" in request.form:
            cart_list = session['cart']

            if request.form["removefood"] in cart_list:
                cart_list.remove(request.form["removefood"])
                session['cart'] = cart_list
                    


    for i in session['cart']:
        cur.execute('SELECT food_name,cost,image,description,food_id From fooditems WHERE food_id=?',(i,))
        foodresults = cur.fetchall()
        formattedtbl.append(foodresults[0])



    return render_template('cart.html',foodcart=formattedtbl,foodlength= len(session['cart']))
    
@app.template_filter('to_dict')
def to_dict(my_string):
    
    return eval(my_string)

@app.route("/admin", methods=["GET","POST"])
def admin():
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()

    
    if request.method == "POST":
        if "confirmorder" in request.form:
            cur.execute('UPDATE Orders SET status="progress" WHERE orderid=?',(request.form["confirmorder"],))

        if "cancelorder" in request.form:
            cur.execute('DELETE FROM Orders WHERE orderid=?',(request.form["cancelorder"],))
        
        if "readypickup" in request.form:
            cur.execute('DELETE FROM Orders WHERE orderid=?',(request.form["readypickup"],))
        
        conn.commit()
    
    cur.execute('SELECT * From Orders')
    results = cur.fetchall()

    cur.execute('SELECT * FROM fooditems')
    foods = cur.fetchall()

    return render_template("admin.html",order=results,foods=foods)

@app.route("/submitorder")
def submit():
    data = request.args
    fname = (data.get('fname'))
    lname = (data.get('lname'))
    phone = (data.get('phone'))

    foods = str(session['cart'])

    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    

    cur.execute("INSERT INTO Orders (firstname,lastname,phonenumb,foodlist) VALUES(?, ?, ?, ?)",(fname,lname,phone,foods))

    conn.commit()
    session['cart'] = []

    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)
