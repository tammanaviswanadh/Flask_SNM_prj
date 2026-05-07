from flask import Flask,request,redirect,url_for,render_template,flash
from otp import genotp
from cmail import sendmail
from stoken import endata,dndata
import mysql.connector
mydb=mysql.connector.connect(user='root',password='Viswa@0210',host='localhost',db='snm_prj_db')
app=Flask(__name__)
app.secret_key='code0909'
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        useremail=request.form['email']
        userpassword=request.form['password']
        try:
            cursor=mydb.cursor()
            cursor.execute("select count(useremail) from userdata where useremail=%s", [useremail])
            count_email=cursor.fetchone() #output will be in tuple format (0,) or (1,)
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not verify email')
            return redirect(url_for('register'))
        else:
            if count_email[0]==0:
                gotp=genotp() #'G6nG5k'
                userdata={'username':username,'useremail':useremail,'userpassword':userpassword,'server_otp':gotp}
                subject=f'SNM APP Verification'
                body=f'Use the OTP for Verify:{gotp}'
                sendmail(to=useremail,subject=subject,body=body)
                flash('The OTP has been given mail')
                return redirect(url_for('otpverification',serverdata=endata(userdata)))
            elif count_email[0] == 1:
                flash('Email already exists')
    return render_template('register.html')
@app.route('/otpverification/<serverdata>',methods=['GET','POST'])
def otpverification(serverdata):
    try:
        de_otp=dndata(serverdata) #it returns the deserialized userdata dictionary {'username':username,'useremail':useremail,'userpassword':userpassword,'server_otp':gotp}
    except Exception as e:
        print(e)
        flash('Could not verify otp')
        return redirect(url_for('register'))
    else:
        if request.method=='POST':
            user_otp=request.form['otp']
            if user_otp==de_otp['server_otp']:
                cursor=mydb.cursor() #it is a mysql cursor created using mysqldb connection object
                cursor.execute("insert into userdata (username, useremail, userpassword) values (%s, %s, %s)", [de_otp['username'], de_otp['useremail'], de_otp['userpassword']])
                mydb.commit()
                cursor.close()
                flash('details registered successfully')
                return redirect(url_for('login'))
            else:
                flash('otp was wrong')
                return redirect(url_for('otpverification',serverotp=serverdata))
        return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        login_useremail=request.form['email']
        login_password=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(useremail) from userdata where useremail=%s', [login_useremail])
            count_email=cursor.fetchone() #(0,) or (1,)
            print(count_email)
        except Exception as e:
            print(e)
            flash('Could not verify email')
            return redirect(url_for('login'))
        else:
            if count_email[0]==1:
                cursor.execute("select userpassword from userdata where useremail=%s", [login_useremail])
                stored_password=cursor.fetchone() #it will return a tuple like ('password123',)
                if stored_password[0]==login_password:
                    flash('user logged in successfully')
                    return redirect(url_for('dashboard'))
                else:
                    flash('invalid password')
                    return redirect(url_for('login'))
            elif count_email[0]==0:
                flash('email does not exist')
                return redirect(url_for('login'))
    return render_template('login.html')
    
@app.route('/dashboard')
def dashboard():
    return ('dashboard.html')
app.run(debug=True,use_reloader=True)