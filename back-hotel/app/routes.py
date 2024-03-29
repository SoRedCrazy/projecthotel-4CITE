import os
from . import create_app, db
from .models import hotel,Image,user,chambres,booking
from flask import jsonify,request
from flask_migrate import Migrate
from flask_jwt_extended import create_access_token ,get_jwt_identity ,unset_jwt_cookies,jwt_required,JWTManager
from flask_swagger_ui import get_swaggerui_blueprint

app = create_app(os.getenv('FLASK_ENV') or 'default')
app.config["JWT_SECRET_KEY"] = os.environ["APP_SUPER_KEY"] 
migrate = Migrate(app, db)
jwt = JWTManager(app)

##############
#   swagger   #
##############


SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  
    API_URL,
    config={
        'app_name': "Test application"
    },
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


##############
#   images   #
##############

@app.route('/image/<int:hotel_id>', methods=['GET'])
def get_images(hotel_id):
    hotel_obj = hotel.query.get(hotel_id)
    if not hotel_obj:
        return jsonify({'error': 'Hotel not found'}), 404

    images = Image.query.filter_by(hotel_id=hotel_id).all()
    image_list = [image.to_json() for image in images]
    return image_list, 200

@app.route('/image', methods=['POST'])
@jwt_required()
def upload_image():
    if get_jwt_identity()["role"] == "admin":
        if 'image' not in request.files and 'hotel_id' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        hotel_id = request.form['hotel_id']

        if image_file.filename == '':
            return jsonify({'error': 'No image selected'}), 400

        new_image = Image(name=image_file.filename, data=image_file.read(), hotel_id=hotel_id)
        db.session.add(new_image)
        db.session.commit()
        return jsonify({'message': 'Image uploaded successfully'}), 200
    else:
        return jsonify({'error': 'You have not the permission for this'}), 404

@app.route('/image/<int:hotel_id>/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(hotel_id, image_id):
    if get_jwt_identity()["role"] == "admin":
        hotel_obj = hotel.query.get(hotel_id)
        if not hotel_obj:
            return jsonify({'error': 'Hotel not found'}), 404
        
        image = Image.query.filter_by(id=image_id, hotel_id=hotel_id).first()
        if not image:
            return jsonify({'error': 'Image not found for the specified hotel'}), 404
        
        db.session.delete(image)
        db.session.commit()
        return jsonify({'message': 'Image deleted successfully'}), 200
    else:
        return jsonify({'error': 'You have not the permission for this'}), 404


##############
#   hotel   #
##############


@app.route("/hotel", methods=["GET"])
def get_hotels():
    if not request.args:
        limit = 10
    else:
        limit = int(request.args.get('limit'))

    hotels = hotel.query.order_by(hotel.create_at.asc(), hotel.name.asc() , hotel.location.asc()).limit(limit).all()
    return jsonify([hotel.to_json() for hotel in hotels]) , 200

@app.route('/hotel', methods=['POST'])
@jwt_required()
def create_hotel():
    if get_jwt_identity()["role"] == "admin":
        if not request.json:
            return jsonify({'error': 'json not found'}), 400
        if not request.json.get('name') or not request.json.get('location') or not request.json.get('description'):
            return jsonify({'error': 'missing parameter'}), 400
        hotel_obj = hotel(
            name=request.json.get('name'),
            location=request.json.get('location'),
            description=request.json.get('description')
        )
        db.session.add(hotel_obj)
        db.session.commit()
        return jsonify(hotel_obj.to_json()), 201
    else:
        return jsonify({'error': 'You have not the permission for this'}), 404

@app.route('/hotel/<int:id>', methods=['PUT'])
@jwt_required()
def update_hotel(id):
    if get_jwt_identity()["role"] == "admin":
        if not request.json:
            return jsonify({'error': 'json not found'}), 400
        hotel_obj = hotel.query.get(id)
        if hotel_obj is None:
            return jsonify({'error': 'hotel not found'}), 404
        hotel_obj.name = request.json.get('name', hotel_obj.name)
        hotel_obj.location = request.json.get('location', hotel_obj.location)
        hotel_obj.description = request.json.get('description', hotel_obj.description)
        db.session.commit()
        return jsonify(hotel_obj.to_json()), 200
    else:
        return jsonify({'error': 'You have not the permission for this'}), 404


@app.route("/hotel/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_hotel(id):
    if get_jwt_identity()["role"] == "admin":
        hotel_obj = hotel.query.get(id)
        if hotel_obj is None:
            return jsonify({'error': 'hotel not found'}), 404
        images = Image.query.filter_by(hotel_id=hotel_obj.id)
        for image in images:
            db.session.delete(image)
        for c in chambres.query.filter_by(hotel_id=id).all():
            for b in booking.query.filter_by(chambre_id=c.id).all():
                db.session.delete(b)
            db.session.delete(c)
        db.session.delete(hotel_obj)
        db.session.commit()
        return jsonify({'result': True}), 200
    else:
        return jsonify({'error': 'You have not the permission for this'}), 404
    
################
#   chambres   #
################


@app.route("/chambres", methods=["GET"])
def get_chambres():
    if not request.args.get('limit'):
        limit = 10
    else:
        limit = int(request.args.get('limit'))
    
    if request.args.get('hotel_id'):
            chambres_list = chambres.query.filter_by(hotel_id=request.args.get('hotel_id')).limit(limit).all()
    else:
        chambres_list = chambres.query.order_by().limit(limit).all()
    return jsonify([chambre.to_json() for chambre in chambres_list]) , 200

@app.route('/chambres', methods=['POST'])
@jwt_required()
def create_chambres():
    if get_jwt_identity()["role"] == "admin":
        if not request.json:
            return jsonify({'error': 'json not found'}), 400
        chambres_obj = chambres(
            numero=request.json.get('numero'),
            nb_personne=request.json.get('nb_personne'),
            hotel_id=request.json.get('hotel_id')
        )
        db.session.add(chambres_obj)
        db.session.commit()
        return jsonify(chambres_obj.to_json()), 201
    else:
        return jsonify({'error': 'You have not the permission for this'}), 404

@app.route('/chambres/<int:id>', methods=['PUT'])
@jwt_required()
def update_chambres(id):
    if get_jwt_identity()["role"] == "admin":
        if not request.json:
            return jsonify({'error': 'json not found'}), 400
        chambres_obj = chambres.query.get(id)
        if chambres_obj is None:
            return jsonify({'error': 'hotel not found'}), 404
        chambres_obj.numero = request.json.get('numero', chambres_obj.numero)
        chambres_obj.nb_personne = request.json.get('nb_personne', chambres_obj.nb_personne)
        db.session.commit()
        return jsonify(chambres_obj.to_json()), 200
    else:
        return jsonify({'error': 'You have not the permission for this'}), 404


@app.route("/chambres/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_chambres(id):
    if get_jwt_identity()["role"] == "admin":
        chambres_obj = chambres.query.get(id)
        if chambres_obj is None:
            return jsonify({'error': 'hotel not found'}), 404
        
        for b in booking.query.filter_by(chambre_id=id).all():
             db.session.delete(b)
        db.session.delete(chambres_obj)
        db.session.commit()
        return jsonify({'result': True}), 200
    else:
        return jsonify({'error': 'You have not the permission for this'}), 404


##############
#   user     #
##############

@app.route("/user", methods=["GET"])
@jwt_required()
def get_user():
    user_logged = get_jwt_identity()
    if user_logged["role"] == "employee":
        users = user.query.all()
        return jsonify([user.to_json() for user in users]) , 200
    else:
        return jsonify([user.query.get(user_logged["id"]).to_json()]) , 200

@app.route('/user', methods=['POST'])
def create_user():
    if not request.json:
        return jsonify({'error': 'json not found'}), 415
    if not request.json.get('pseudo') or not request.json.get('email') or not request.json.get('password'):
        return jsonify({'error': 'missing parameter'}), 400
    user_obj = user(
        pseudo=request.json.get('pseudo'),
        email=request.json.get('email'),
    )
    user_obj.set_password(request.json.get('password'))
    db.session.add(user_obj)
    db.session.commit()
    return jsonify(user_obj.to_json()), 201

@app.route('/user/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    if not request.json:
        return jsonify({'error': 'json not found'}), 400
    if get_jwt_identity()["id"]==id or get_jwt_identity()["role"] == "admin":
        user_obj = user.query.get(id)
        if user_obj is None:
            return jsonify({'error': 'user not found'}), 404
        user_obj.pseudo = request.json.get('pseudo', user_obj.pseudo)
        user_obj.email = request.json.get('email', user_obj.email)
        if request.json.get('password') and request.json.get('password') != "":
            user_obj.set_password(request.json.get('password'))
        db.session.commit()
        return jsonify(user_obj.to_json()), 200
    else: 
        return jsonify({'error': 'You have not the permission for modify this profile'}), 404

@app.route("/user", methods=["DELETE"])
@jwt_required()
def delete_user():
    id = get_jwt_identity()["id"]
    user_obj = user.query.get(id)
    if user_obj is None:
        return jsonify({'error': 'user not found'}), 404
    for b in booking.query.filter_by(user_id=id).all():
        db.session.delete(b)
    db.session.delete(user_obj)
    db.session.commit()
    return jsonify({'result': True}), 200

@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response, 200 

@app.route("/login", methods=["POST"])
def login():
    if not request.json:
        return jsonify({'error': 'json not found'}), 400
    user_obj = user.query.filter_by(email=request.json.get('email')).first()
    if user_obj is None:
        return jsonify({'error': 'user not found'}), 404
    
    if user_obj.check_password(request.json.get('password')):
        access_token = create_access_token(identity=user_obj.to_json())
        return jsonify({ "access_token": access_token, "user": user_obj.to_json() }) , 200
    else:   
        return jsonify({'error': 'password is wrong'}), 400
    
##############
#   booking  #
##############

@app.route("/booking", methods=["GET"])
@jwt_required()
def get_booking():
    user_logged = get_jwt_identity()
    if user_logged["role"] == "admin":
        if request.args.get('email'):
            user_obj = user.query.filter_by(email=request.args.get('email')).first()
            bookings = booking.query.filter_by(user_id=user_obj.id).all()
        else:
            bookings =booking.query.all()
    else:
        bookings = booking.query.filter_by(user_id=user_logged["id"])

    return jsonify([booking.to_json() for booking in bookings]) , 200

@app.route('/booking', methods=['POST'])
@jwt_required()
def create_booking():
    if not request.json:
        return jsonify({'error': 'json not found'}), 400
    booking_obj = booking(
        chambre_id=request.json.get('chambre_id'),
        user_id=get_jwt_identity()["id"],
        datein=request.json.get('datein'),# format 1987-01-17
        dateout=request.json.get('dateout')# format 1987-01-17
    )
    db.session.add(booking_obj)
    db.session.commit()
    return jsonify(booking_obj.to_json()), 201

@app.route('/booking/<int:id>', methods=['PUT'])
@jwt_required()
def update_booking(id):
    if not request.json:
        return jsonify({'error': 'json not found'}), 400
    booking_obj = booking.query.get(id)
    if booking_obj is None:
            return jsonify({'error': 'booking not found'}), 404
    if get_jwt_identity()["id"]==booking_obj.user_id or get_jwt_identity()["role"] == "admin":
        booking_obj.datein = request.json.get('datein', booking_obj.datein)
        booking_obj.dateout = request.json.get('dateout', booking_obj.dateout)
        db.session.commit()
        return jsonify(booking_obj.to_json()), 200
    else: 
        return jsonify({'error': 'You have not the permission for modify this'}), 404

@app.route("/booking/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_booking(id):
    booking_obj = booking.query.get(id)
    if booking_obj is None:
        return jsonify({'error': 'booking not found'}), 404
    if get_jwt_identity()["id"]==booking_obj.user_id or get_jwt_identity()["role"] == "admin":
        db.session.delete(booking_obj)
        db.session.commit()
        return jsonify({'result': True}), 200
    else: 
        return jsonify({'error': 'You have not the permission for modify this'}), 404
    
if __name__ == "__main__":
    print("passe")
    app.run(host="127.0.0.1",threaded=True)