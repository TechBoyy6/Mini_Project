""" Flask Webapp made for the carpooling system"""

import smtplib
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from flask import Flask, render_template, request, redirect, url_for
import pymongo
from webScrapping import fetchDetails


app = Flask(__name__)
client = pymongo.MongoClient(MongoDB_URL)
db = client.get_database('Carpool')
data = db['Clients']
USER_ID = ''
USER_LOCATION = ''
geolocator = Nominatim(user_agent="Carpool")
USER_QUERY = False


def sort_list(element):
    return element['distanceBtw']


def check_user(user_name, user_email):
    """ This function checks if the user already exists in DB"""

    if data.find_one({'_id': user_name, 'email': user_email}):
        return True
    return False


def check_loc(loc1, loc2):
    """Checks the given user n owner location if they exists and if yes return distance between them. """

    userloc = geolocator.geocode(loc1)
    ownerloc = geolocator.geocode(loc2)
    if(bool(userloc) and bool(ownerloc)):
        return int(great_circle((userloc.latitude, userloc.longitude), (ownerloc.latitude, ownerloc.longitude)).km)
    return False


def gen_map(user_from, owner_from):
    """This function returns a dictionary which consists of
    - Distance between users
    - Time taken to reach users
    - Travel cost to reach users
    - Map url to reach users"""

    values = {}
    values['distanceBtw'] = check_loc(user_from, owner_from)
    values['timeTaken'] = values['distanceBtw']/40
    values['cost'] = values['distanceBtw'] * 100

    user = geolocator.geocode(user_from)
    owner = geolocator.geocode(owner_from)
    user_lati = user.latitude
    user_long = user.longitude

    owner_lat = owner.latitude
    owner_long = owner.longitude

    values['map_url'] = f"https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route={user_lati}%2C{user_long}%3B{owner_lat}%2C{owner_long}&layers=O"

    return values


@app.route('/send-mail')
def send_mail(connect_data, user_data):
    """Sends mail to """

    global USER_ID
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login("testmailcarpool@gmail.com", "carpoolTestMail")
    connect_msg = f'''Subject: Details Requested Alert | Carpool\n\n
Greetings from Carpool,\n
The below mentioned person has viewed your details.
Name : {user_data['name']}
Phone : {user_data['mobile']}
Email : {user_data['email']}
Gender : {user_data['gender']}
Age : {user_data['age']}
Destination : {user_data['to_loc']}
\nKindly please contact them for further clarification
Thanks & Regards
Team Carpool'''
    server.sendmail("testmailcarpool@gmail.com",
                    connect_data['email'], connect_msg)
    server.quit()


@app.route('/details')
def details():
    requested_user_data = data.find_one({'_id': request.args.get('connectId')})
    user_data = data.find_one({'_id': USER_ID})
    send_mail(requested_user_data, user_data)
    imp_val = gen_map(user_data['from_loc'], requested_user_data['from_loc'])

    return render_template('details.html', ownerData=requested_user_data, travelVal=imp_val)


@app.route('/login/', methods=['GET', 'POST'])
def login():

    global USER_ID, USER_LOCATION
    USER_ID = ''
    if request.method == 'POST':
        USER_ID = request.form.get('username')
        user_data = data.find_one({'_id': USER_ID})
        USER_LOCATION = user_data['from_loc']
        if user_data:
            if user_data['password'] == request.form.get('password'):
                return redirect(url_for("home"))
            return render_template('login.html', login_error="Incorrect Password")
        return render_template('login.html', login_error="Incorrect Username")
    return render_template('login.html')


@app.route('/', methods=['GET', 'POST'])
def home():
    global USER_ID
    if request.method == 'POST':
        if USER_ID != '':
            srch_loc = geolocator.geocode(request.form.get('search'))
            if bool(srch_loc):
                USER_QUERY = True
                result = []
                query_result = data.find(
                    {"to_loc": request.form.get('search').lower()})
                for query in query_result:
                    query['distanceBtw'] = check_loc(
                        USER_LOCATION, query['from_loc'])
                    result.append(query)
                result.sort(key=sort_list)
                return render_template('index1.html', searchQuery=USER_QUERY, record=result, userID=USER_ID)
            return render_template('index1.html', location_error="Try another Destination")
        return render_template('login.html', login_error="Please login first")
    return render_template('index1.html', userID=USER_ID)


@ app.route('/<string:action_type>', methods=['GET', 'POST'])
def register(action_type):
    global USER_ID
    if action_type == 'UPDATE':
        user_already_data = data.find_one({'_id': USER_ID})
        if request.method == 'POST':
            if check_loc(request.form.get('from'), request.form.get('to')):
                data.update_one(
                    {'_id': USER_ID},
                    {'$set': {
                        'type': request.form.get('user_type'),
                        'age': int(request.form.get('age')),
                        'email': request.form.get('email'),
                        'mobile': int(request.form.get('phone')),
                        'from_loc': request.form.get('from').lower(),
                        'to_loc': request.form.get('to').lower(),
                        'password': request.form.get('password'),
                    }
                    }, upsert=False
                )
                return redirect(url_for("home"))
            return render_template("register.html", location_error="Try other Location", ActionType=action_type)
        return render_template("register.html", user_data=user_already_data, ActionType=action_type)
    elif(action_type == 'REGISTER' and request.method == 'POST'):
        USER_ID = request.form.get('username')
        user_password = request.form.get('password')
        user_email = request.form.get('email')

        if not check_user(USER_ID, user_email):
            if check_loc(request.form.get('from'), request.form.get('to')):
                data.insert_one({
                    '_id': USER_ID,
                    'name': request.form.get('name'),
                    'type': request.form.get('user_type'),
                    'gender': request.form.get('gender'),
                    'age': int(request.form.get('age')),
                    'email': user_email,
                    'mobile': int(request.form.get('phone')),
                    'from_loc': request.form.get('from').lower(),
                    'to_loc': request.form.get('to').lower(),
                    'password': user_password,
                })
                return redirect(url_for("home"))
            return render_template("register.html", location_error="Try other Location", ActionType=action_type)
        return render_template("login.html", register_error="User Already Exist")
    return render_template('register.html', user_data="", ActionType=action_type)


if __name__ == "__main__":
    app.run(debug=True)
