from flask import Flask,request, render_template,session,jsonify
#from flask_qrcode import QRcode
import sqlite3
from flask_session import Session
import json

app = Flask(__name__)
#QRcode(app)
app.config['SECRET_KEY'] = 'sadasdasdassadas'
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_PERMANENT"] = False
Session(app)

@app.route("/",methods=["GET","POST"])
def mainpage():
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM fooditems')
    foods = cur.fetchall()


    
    cur.execute('SELECT * FROM categories')
    categories = cur.fetchall()

    jsonobj = []
    if session.get("foodqueue"):
        loads = json.loads(session.get('foodqueue'))
        for i in loads:
            jsonobj.append(i)

    if request.method == "POST":
        if "foodqueue" in request.form:
            if session.get("foodqueue"):
                session["foodqueue"] = request.form["foodqueue"] + session["foodqueue"]
            elif not session.get("foodqueue"):
                session["foodqueue"] = request.form["foodqueue"]
            
            return render_template("home.html", foods=foods,categories=categories,showing=False,foodqueue=session["foodqueue"],length=len(jsonobj))
            #return jsonify(request.form["foodqueue"])
        
        if "food_id" in request.form:
            cur.execute('SELECT food_name,cost,image,description From fooditems WHERE food_id=?',(request.form["food_id"],))
            foodresults = cur.fetchall()

            return render_template("home.html", foods=foods,categories=categories,showing=True,food=foodresults,length=len(jsonobj))

    return render_template("home.html", foods=foods,categories=categories,showing=False,length=len(jsonobj))


@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route('/start-reward', methods=["GET", "POST"])
def start():
    print(request.form)
    return render_template("main_page.html")

@app.route('/activatereward', methods=["GET", "POST"])
def button():
    if request.method == "POST":
        if request.form["reward"]:
            print(request.form["reward"]) 
            conn = sqlite3.connect('data.db')
            cur = conn.cursor()
            cur.execute('SELECT name,photo,description,reward_price,expiry_time From products WHERE name=?',(request.form["reward"],))
            results = cur.fetchall()

            return render_template("main_page.html", productresult=results)
      #  if request.form['activate-reward']:
            
          #  return render_template("main_page.html")

"""
@app.route("/hometest")
def home():
    return render_template("home.html",title="Bob")
    
@app.route("/contacts")
def contacts():
    return render_template("contacts.html",title="Contacts")

@app.route("/about")
def about():
    return render_template("about.html",title="About")

@app.route('/all_pizzas')
def all_pizzas():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM Pizza')
    results = cur.fetchall()

    return render_template("all_pizzas.html",results=results)

@app.route('/pizza/<int:id>')
def pizza(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM Pizza WHERE id=?",(id,))
    pizza = cur.fetchone()
    
    cur.execute("SELECT name FROM Base WHERE id IN (SELECT base FROM Pizza WHERE id=?)",(id,))
    base = cur.fetchone()

    cur.execute("SELECT name FROM Topping WHERE id IN (SELECT tid FROM PizzaTopping WHERE pid=?)",(id,))
    toppings = cur.fetchall()

    return render_template('pizza.html',pizza=pizza,base=base,toppings=toppings)
"""

if __name__ == '__main__':
    app.run(debug=True)
