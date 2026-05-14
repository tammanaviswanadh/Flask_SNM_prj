from flask import Flask,request,redirect,url_for,render_template,flash,session,send_file
#send_file is used to send files from the server to the client, allowing you to serve files for download or display in the browser.
from flask_session import Session #it is used to manage user sessions in a Flask application, allowing you to store and retrieve data across multiple requests for a specific user.
from otp import genotp
from cmail import sendmail
from stoken import endata,dndata
import mysql.connector
import flask_excel as excel
from io import BytesIO #io means input output module, it is used to handle binary data in memory, allowing you to create file-like objects that can be used to read and write binary data without the need for actual files on disk.
mydb=mysql.connector.connect(user='root',password='Viswa@0210',host='localhost',db='snm_prj_db')
app=Flask(__name__)
excel.init_excel(app) #it initializes the Flask-Excel extension with the Flask application instance, enabling Excel-related functionality in the app.
app.config['SESSION_TYPE']='filesystem' #it configures the session type to be stored on the filesystem, allowing you to store session data in files on the server.
Session(app) #it initializes the Flask-Session extension with the Flask application instance, enabling session management in the app.
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
                    session['user']=login_useremail
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
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('please login to access dashboard')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('user logged out successfully')
        return redirect(url_for('login'))
    else:
        flash('No user is currently logged in')
        return redirect(url_for('login'))

@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if not session.get('user'):
        flash('please login to access addnotes page')
        return redirect(url_for('login'))
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
            user_id=cursor.fetchone() #(1,) or (2,)
            if user_id[0]:
                cursor.execute('insert into notesdata (notes_title, notes_description, userid) values (%s, %s, %s)', [title, description, user_id[0]])
                mydb.commit()
                cursor.close()
            else:
                flash('user not found, could not fetch user details')
                return redirect(url_for('addnotes')) 
        except Exception as e:
            print(e)
            flash('could not store notesdata details')
            return redirect(url_for('addnotes'))
        else:
            flash('notes added successfully')
            return redirect(url_for('addnotes'))
    return render_template('addnotes.html')

@app.route('/viewallnotes')
def viewallnotes():
    if not session.get('user'):
        flash('please login to access viewallnotes page')
        return redirect(url_for('login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('select notesid, notes_title, created_at from notesdata where userid=%s',[user_id])
        stored_allnotesdata=cursor.fetchall() #it will return a list of tuples like [('title1', 'description1', '2023-09-01 10:00:00'), ('title2', 'description2', '2023-09-02 11:00:00')] 
        print(stored_allnotesdata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch notesdata details')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallnotes.html', stored_allnotesdata=stored_allnotesdata)


@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if not session.get('user'):
        flash('please login to access view notes page')
        return redirect(url_for('login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('select notesid, notes_title, notes_description, created_at from notesdata where userid=%s and notesid=%s',[user_id, nid])
        stored_notesdata=cursor.fetchone()  #it will return a single tuple like ('title1', 'description1', '2023-09-01 10:00:00')
        print(stored_notesdata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch notesdata details')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewnotes.html', stored_notesdata=stored_notesdata)

@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if not session.get('user'):
        flash('please login to access delete notes')
        return redirect(url_for('login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('delete from notesdata where userid=%s and notesid=%s',[user_id, nid])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not delete notesdata details')
        return redirect(url_for('dashboard'))
    else:
        flash('notes deleted successfully')
        return redirect(url_for('viewallnotes'))

@app.route('/updatenotes/<nid>', methods=['GET', 'POST'])
def updatenotes(nid):
    if not session.get('user'):
        flash('please login to access the dashboard features')
        return redirect(url_for('login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('select notesid, notes_title, notes_description, created_at from notesdata where userid=%s and notesid=%s',[user_id, nid])
        stored_notesdata=cursor.fetchone()  #it will return a single tuple like ('title1', 'description1', '2023-09-01 10:00:00')
        print(stored_notesdata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch notesdata details')
        return redirect(url_for('viewallnotes'))
    else:
        if request.method == 'POST':
            updated_title = request.form['title']
            updated_description = request.form['description']
            try:
                cursor = mydb.cursor(buffered=True)
                cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
                user_id = cursor.fetchone()  # (1) or (2)
                if user_id[0]:
                    cursor.execute('update notesdata set notes_title=%s, notes_description=%s where userid=%s and notesid=%s', [updated_title, updated_description, user_id[0], nid])
                    mydb.commit()
                    cursor.close()
                else:
                    flash('user not found, could not fetch user details')
                    return redirect(url_for('updatenotes', nid=nid))
            except Exception as e:
                print(e)
                flash('could not update notesdata details')
                return redirect(url_for('updatenotes', nid=nid))
            else:
                flash('notes updated successfully')
                return redirect(url_for('updatenotes', nid=nid))
        return render_template('updatenotes.html', stored_notesdata=stored_notesdata)

@app.route('/getexceldata')
def getexceldata():
    if not session.get('user'):
        flash('please login to access viewallnotes page')
        return redirect(url_for('login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('select notesid, notes_title, notes_description, created_at from notesdata where userid=%s',[user_id])
        stored_allnotesdata=cursor.fetchall() #it will return a list of tuples like [('title1', 'description1', '2023-09-01 10:00:00'), ('title2', 'description2', '2023-09-02 11:00:00')] 
        print(stored_allnotesdata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch notesdata details')
        return redirect(url_for('dashboard'))
    else:
        array_data = [list(i) for i in stored_allnotesdata] #it converts the list of tuples into a list of lists like [['title1', 'description1', '2023-09-01 10:00:00'], ['title2', 'description2', '2023-09-02 11:00:00']]
        columns=['Notesid', 'NotesTitle', 'NotesDescription', 'Created_at']
        array_data.insert(0, columns) #it inserts the column names as the first row in the array_data list like [['Notesid', 'NotesTitle', 'NotesDescription', 'Created_at'], ['title1', 'description1', '2023-09-01 10:00:00'], ['title2', 'description2', '2023-09-02 11:00:00']]
        return excel.make_response_from_array(array_data,'xlsx',file_name='AllNotesdata.xlsx') 

@app.route('/fileupload', methods=['GET', 'POST'])
def fileupload():
    if not session.get('user'):
        flash('please login to access the file upload feature from dashboard')
        return redirect(url_for('userlogin'))
    if request.method == 'POST':
        user_filedata=request.files['filedata'] #accepts the file uploaded by the user and stores it in the user_filedata variable as a FileStorage object
        #print(user_filedata)
        #print(user_filedata.read()) #it reads the content of the uploaded file and prints it in the console. Note that after reading the file, the file pointer will be at the end of the file, so if you want to read it again, you need to reset the file pointer using user_filedata.seek(0)
        #print(user_filedata.filename) #it prints the name of the uploaded file in the console
        fname=user_filedata.filename
        fdata=user_filedata.read() #it reads the content of the uploaded file and stores it in the fdata variable as bytes
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
            user_id=cursor.fetchone()[0] #(1) or (2)
            cursor.execute('insert into filesdata (filename, filedata, userid) values (%s, %s, %s)', [fname, fdata, user_id])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not store filedata details')
            return redirect(url_for('fileupload'))
        else:
            flash('File uploaded successfully')
            return redirect(url_for('fileupload'))
    return render_template('fileupload.html')

@app.route('/viewallfiles')
def viewallfiles():
    if not session.get('user'):
        flash('please login to access viewallfiles page')
        return redirect(url_for('login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('select filesid, filename, created_at from filesdata where userid=%s',[user_id])
        stored_allfilesdata=cursor.fetchall() #it will return a list of tuples like [('file1.txt', '2023-09-01 10:00:00'), ('file2.txt', '2023-09-02 11:00:00')] 
        # print(stored_allfilesdata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch file details')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallfiles.html', stored_allfilesdata=stored_allfilesdata)

@app.route('/deletefiles/<fid>')
def deletefiles(fid):
    if not session.get('user'):
        flash('please login to access delete files')
        return redirect(url_for('login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('delete from filesdata where userid=%s and filesid=%s',[user_id, fid])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not delete file details')
        return redirect(url_for('dashboard'))
    else:
        flash('file deleted successfully')
        return redirect(url_for('viewallfiles'))
    

@app.route('/viewfiles/<fid>')
def viewfiles(fid):
    if not session.get('user'):
        flash('please login to access view files page')
        return redirect(url_for('login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('select filesid, filename, filedata from filesdata where userid=%s and filesid=%s',[user_id, fid])
        stored_filedata=cursor.fetchone()  #it will return a single tuple like ('file1.txt', b'file content in bytes')
        print(stored_filedata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch file details')
        return redirect(url_for('dashboard'))
    else:
        bytes_array=BytesIO(stored_filedata[2]) #it converts the filedata bytes into a BytesIO object, which is a file-like object that can be used to read the file content
        return send_file(bytes_array, as_attachment=False, download_name=stored_filedata[1]) #it sends the file to the client for download, with the original filename as the download name

        return render_template('viewfiles.html', stored_filedata=stored_filedata)


@app.route('/downloadfiles/<fid>')
def downloadfiles(fid):
    if not session.get('user'):
        flash('please login to access download files page')
        return redirect(url_for('login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('select filesid, filename, filedata from filesdata where userid=%s and filesid=%s',[user_id, fid])
        stored_filedata=cursor.fetchone()  #it will return a single tuple like ('file1.txt', b'file content in bytes')
        print(stored_filedata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch file details')
        return redirect(url_for('dashboard'))
    else:
        bytes_array=BytesIO(stored_filedata[2]) #it converts the filedata bytes into a BytesIO object, which is a file-like object that can be used to read the file content
        return send_file(bytes_array, as_attachment=True, download_name=stored_filedata[1]) #it sends the file to the client for download, with the original filename as the download name

        return render_template('downloadfiles.html', stored_filedata=stored_filedata)

app.run(debug=True,use_reloader=True)