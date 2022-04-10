from geopy.geocoders import Nominatim
import smtplib
from geopy.distance import great_circle
from flask import Flask, render_template, request, redirect, url_for
import pymongo
from playwright.sync_api import sync_playwright
from time import asctime

app = Flask(__name__)
client = pymongo.MongoClient(
    "mongodb+srv://admin:admin@cluster0.lifk8.mongodb.net/test")
db = client.get_database('Carpool')
data = db['Clients']
user_id = ''
geolocator = Nominatim(user_agent="Carpool")
user_Query = False
flag = 0
travel_history = {}
reg_no = ''
user_type = 'Traveller'


def checkUser(username, userEmail):
    """Checks whether the user data already exists in db"""
    if(data.find_one({'_id': username, 'email': userEmail})):
        return True
    else:
        return False


def checkLoc(x, y):
    """Checks whether the location exists or not"""
    userloc = geolocator.geocode(x)
    ownerloc = geolocator.geocode(y)
    if(bool(userloc) and bool(ownerloc)):
        return int(great_circle((userloc.latitude, userloc.longitude), (ownerloc.latitude, ownerloc.longitude)).km)
    else:
        return False


def genMap(userData, ownerData):
    """Generates the url for the map"""
    values = {}
    userFrom = userData['from_loc']
    ownerFrom = ownerData['from_loc']
    values['distanceBtw'] = checkLoc(userFrom, ownerFrom)
    values['timeTaken'] = values['distanceBtw']/40
    values['cost'] = values['distanceBtw']*100
    values['Insuarance_Exp'] = ownerData['insaurance_exp']
    values['Vehicle_Reg'] = ownerData['reg_no']

    user = geolocator.geocode(userFrom)
    owner = geolocator.geocode(ownerFrom)
    uLat = user.latitude
    uLong = user.longitude

    oLat = owner.latitude
    oLong = owner.longitude

    values['map_url'] = f"https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route={uLat}%2C{uLong}%3B{oLat}%2C{oLong}&layers=O"

    return values


@app.route('/details')
def details():
    global travel_history
    sendMail()
    connectID = request.args.get('connectId')
    connectData = data.find_one({'_id': connectID})
    userData = data.find_one({'_id': user_id})
    travel_history = userData['history']
    travel_history[asctime()] = connectID
    data.find_one_and_update({'_id': user_id},
                             {"$set": {
                                 'history': travel_history
                             }})
    imp_val = genMap(userData, connectData)

    return render_template('details.html', ownerData=connectData, travelVal=imp_val)


@app.route('/send_mail')
def sendMail():

    connectData = data.find({'_id': request.args.get('connectId')})
    global user_id
    userData = data.find_one({'_id': user_id})
    connectData = connectData.next()
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login("testmailcarpool@gmail.com", "carpoolTestMail")
    connectMsg = f"""Subject: Details Requested Alert | Carpool\n\n
Greetings from Carpool,\n
The below mentioned person has viewed your details.
Name : {userData['name']}
Phone : {userData['mobile']}
Email : {userData['email']}
Gender : {userData['gender']}
Age : {userData['age']}
Destination : {userData['to_loc']}
\nKindly please contact them for further clarification
Thanks & Regards
Team Carpool"""
    server.sendmail("testmailcarpool@gmail.com",
                    connectData['email'], connectMsg)
    server.quit()


@app.route('/login/', methods=['GET', 'POST'])
def login():

    global user_id
    user_id = ''
    if(request.method == 'POST'):
        user_id = request.form.get('username')
        user_data = data.find_one({'_id': user_id})

        if(user_data):
            if(user_data['password'] == request.form.get('password')):
                return redirect(url_for("home"))
            else:
                error = "Incorrect Password"
                return render_template('login.html', login_error=error)
        else:
            return render_template('login.html', login_error="Incorrect Username")
    return render_template('login.html')


@app.route('/', methods=['GET', 'POST'])
def home():
    # global user_id
    if(request.method == 'POST'):
        if(user_id != ''):
            srchLoc = geolocator.geocode(request.form.get('search'))
            if(bool(srchLoc)):
                user_Query = True
                result = data.find(
                    {"to_loc": request.form.get('search').lower()})
                return render_template('index1.html', searchQuery=user_Query, record=result, userID=user_id)
            return render_template('index1.html', location_error="Try another Destination")
        return render_template('login.html', login_error="Please login first")
    return render_template('index1.html', userID=user_id)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if(request.method == 'POST'):
        user_password = request.form.get('password')
        user_email = request.form.get('email')

        if (not checkUser(user_id, user_email)):
            if(checkLoc(request.form.get('from'), request.form.get('to'))):
                if(reg_no == ''):
                    data.update_one({'_id': user_id},
                                    {"$set": {
                                        'type': user_type,
                                        'name': request.form.get('name')
                                    }})
                elif(reg_no):
                    data.update_one({'_id': user_id},
                                    {"$set": {
                                        'type': 'Owner',
                                    }})
                data.update_one({'_id': user_id},
                                {"$set": {
                                    'gender': request.form.get('gender'),
                                    'age': int(request.form.get('age')),
                                    'email': user_email,
                                    'mobile': int(request.form.get('phone')),
                                    'from_loc': request.form.get('from').lower(),
                                    'to_loc': request.form.get('to').lower(),
                                    'password': user_password,
                                }})

                return redirect(url_for("home"))
            return render_template("owner.html", location_error="Try other Location")
        return render_template("login.html", register_error="User Already Exist")
    return render_template('owner.html', type=user_type)


@app.route('/id/', methods=['GET', 'POST'])
def id():
    global user_id
    if(request.method == 'POST'):
        user_id = request.form.get('username')
        print(user_id)
        if(not data.find_one({'_id': user_id})):
            data.insert_one({
                '_id': user_id,
            })
            return render_template('type.html', user_data=user_id)
    return render_template('id.html', user_data=user_id)


@app.route('/modify/', methods=['GET', 'POST'])
def modify():
    global user_id
    user_data = data.find_one({'_id': user_id})
    if(request.method == 'POST'):
        if(user_data):
            if(checkLoc(request.form.get('from'), request.form.get('to'))):
                data.update_one({'_id': user_id},
                                {"$set": {
                                    'type': request.form.get('user_type'),
                                    'age': int(request.form.get('age')),
                                    'email': request.form.get('email'),
                                    'mobile': int(request.form.get('phone')),
                                    'from_loc': request.form.get('from').lower(),
                                    'to_loc': request.form.get('to').lower(),
                                    'password': request.form.get('password'),
                                }})
                return redirect(url_for("home"))
            return render_template("modify.html", location_error="Try another location")
    return render_template('modify.html', data=user_data)


@app.route('/fetch', methods=['GET', 'POST'])
def fetch():
    global flag
    global reg_no
    global user_type

    details = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto('https://rtovehicleinfo.onlineseva.xyz/rtovehicle.php')
        page.locator('#card_details').wait_for(timeout=0)

        details['reg_no'] = page.query_selector(
            '//html/body/div/div/div[1]/div[2]/p').inner_text()
        details['name'] = page.query_selector(
            '//html/body/div/div/div[2]/div[2]/p').inner_text()
        details['fuel_type'] = page.query_selector(
            '//html/body/div/div/div[7]/div[2]/p').inner_text()
        details['insaurance_exp'] = page.query_selector(
            '//html/body/div/div/div[12]/div[2]/p').inner_text()
        reg_no = details['reg_no']

        if(details):
            flag = 1
            user_type = 'Owner'
            data.update_one({
                '_id': user_id},
                {"$set": {'reg_no': details['reg_no'],
                          'name': details['name'],
                          'fuel_type': details['fuel_type'],
                          'insaurance_exp': details['insaurance_exp'],
                          }})
            return redirect(url_for("register"))

    return details


if __name__ == "__main__":
    app.run(debug=True)
