from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pizza_restaurants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define models
class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    address = db.Column(db.String(100), nullable=False)
    pizzas = db.relationship('Pizza', secondary='restaurant_pizza', backref='restaurants')

class Pizza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    ingredients = db.Column(db.String(100), nullable=False)

class RestaurantPizza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizza.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    restaurant = db.relationship('Restaurant', backref=backref('restaurant_pizza', cascade='all,delete'))

# Define routes
@app.route('/restaurants')
def get_restaurants():
    restaurants = Restaurant.query.all()
    data = [{
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address
    } for restaurant in restaurants]
    return jsonify(data)

@app.route('/restaurants/<int:id>')
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant:
        pizzas = [{
            "id": pizza.id,
            "name": pizza.name,
            "ingredients": pizza.ingredients
        } for pizza in restaurant.pizzas]
        return jsonify({
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "pizzas": pizzas
        })
    else:
        return jsonify({"error": "Restaurant not found"}), 404

@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant:
        db.session.delete(restaurant)
        db.session.commit()
        return '', 204
    else:
        return jsonify({"error": "Restaurant not found"}), 404

@app.route('/pizzas')
def get_pizzas():
    pizzas = Pizza.query.all()
    data = [{
        "id": pizza.id,
        "name": pizza.name,
        "ingredients": pizza.ingredients
    } for pizza in pizzas]
    return jsonify(data)

@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.json
    price = data.get('price')
    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')

    if price is None or pizza_id is None or restaurant_id is None:
        return jsonify({"errors": ["validation errors"]}), 400

    if not (1 <= price <= 30):
        return jsonify({"errors": ["Price must be between 1 and 30"]}), 400

    restaurant = Restaurant.query.get(restaurant_id)
    pizza = Pizza.query.get(pizza_id)
    if not restaurant:
        return jsonify({"errors": ["Restaurant not found"]}), 404
    if not pizza:
        return jsonify({"errors": ["Pizza not found"]}), 404

    existing_restaurant = Restaurant.query.filter_by(name=restaurant.name).first()
    if existing_restaurant:
        return jsonify({"errors": ["Restaurant with the same name already exists"]}), 400

    restaurant_pizza = RestaurantPizza(price=price, pizza=pizza, restaurant=restaurant)
    db.session.add(restaurant_pizza)
    db.session.commit()
    return jsonify({
        "id": restaurant_pizza.id,
        "price": restaurant_pizza.price,
        "pizza": {
            "id": pizza.id,
            "name": pizza.name,
            "ingredients": pizza.ingredients
        },
        "restaurant": {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address
        }
    }), 201

def seed_data():
    RestaurantPizza.query.delete()
    Pizza.query.delete()
    Restaurant.query.delete()

    pizza_lovers = Restaurant(name="Pizza Lovers", address="789 Elm Street")
    pizza_world = Restaurant(name="Pizza World", address="321 Maple Avenue")
    
    db.session.add(pizza_lovers)
    db.session.add(pizza_world)
 
    db.session.commit()

    margherita_pizza = Pizza(name="Margherita", ingredients="Dough, Tomato Sauce, Mozzarella, Basil")
    veggie_supreme_pizza = Pizza(name="Veggie Supreme", ingredients="Dough, Tomato Sauce, Mozzarella, Bell Peppers, Onions, Mushrooms, Olives")
   
    db.session.add(margherita_pizza)
    db.session.add(veggie_supreme_pizza)

    db.session.commit()

    db.session.add(RestaurantPizza(price=15, restaurant_id=pizza_lovers.id, pizza_id=margherita_pizza.id))
    db.session.add(RestaurantPizza(price=18, restaurant_id=pizza_world.id, pizza_id=veggie_supreme_pizza.id))

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()  
    app.run(debug=True)



