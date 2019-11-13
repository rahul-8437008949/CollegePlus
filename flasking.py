#=========================================================================
import os
from flask import Flask, render_template, request, flash, url_for, redirect, sessions, session
from flask_mysqldb import MySQL
import random
from datetime import date
import xlrd
import sms
from werkzeug.utils import secure_filename

#==========================================================================


otp1 = 'none'
studentTableName = 'studentlogininfo'
facultyTableName = 'facultylogininfo'
#==========================================================================
app = Flask(__name__)


#==========================================================================
app.config['SECRET_KEY'] = 'AjJ0lXaX5K9tai8QsUhwwQ'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Anant@1707'
app.config['MYSQL_DB'] = 'collegeplus'
msql = MySQL(app)

#===========================================================================
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    cur = msql.connection.cursor()
    if request.method == 'POST':
        logininfo = request.form
        fname = logininfo['fname']
        lname = logininfo['lname']
        email = logininfo['email']
        sid = logininfo['sid']
        phone = logininfo['phone']
        password = logininfo['password']
        confirmpassword = logininfo['confirmpass']
        stream = logininfo['stream']

        values = (fname, lname, sid, email, password, phone,stream)
        if (password == confirmpassword):
            flash("Thanks for Registering", 'success')
            cur.execute(f"INSERT INTO " + studentTableName + " VALUES" + f"{values}")
            msql.connection.commit()
            cur.close()
            return redirect(url_for('home'))
        else:
            flash("Password didnt match", 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/studentlogin', methods=['GET', 'POST'])
def studentlogin():
    cur = msql.connection.cursor()
    if request.method == 'POST':
        slogininfo = request.form
        ssid = slogininfo['sid']
        password = slogininfo['password']
        cur.execute(f"SELECT sid FROM {studentTableName} ")
        a = cur.fetchall()
        flag = 0
        for x in a:
            if (str(x[0]) == ssid):
                flag += 1

        if flag == 0:
            flash("You are not registered!!,REGISTER NOW", 'danger')
            return redirect(url_for('register'))
        elif flag != 0:
            cur.execute(f"SELECT passwordd FROM {studentTableName} where sid = '{ssid}'")
            a = cur.fetchall()

            if (password == a[0][0]):

                session['logged_in'] = True
                session['username'] = ssid
                cur.execute(f"SELECT fname FROM {studentTableName} where sid = '{ssid}'")
                fname = cur.fetchall()

                flash(f'welcome {fname[0][0]}', 'success')

                cur.close()
                return redirect(url_for('studentloggedin'))
            else:
                flash("WRONG PASSWORD", 'danger')
                cur.close()
                return redirect(url_for('studentlogin'))

    return render_template("student-login.html")


@app.route('/facultylogin', methods=['GET', 'POST'])
def facultylogin():
    cur = msql.connection.cursor()
    if request.method == 'POST':
        flogininfo = request.form
        username = flogininfo['logid']
        password = flogininfo['password']

        cur.execute(f"select passwordd from {facultyTableName} where loginid= '{username}'")
        a = cur.fetchall()[0][0]


        if password == a:
            cur.execute(f"select loginid from facultylogininfo")
            session['log-in'] = True
            session['username']=username

            return redirect(url_for('facultyloggedin'))
        else:
            flash('Invalid Username or Password', 'danger')
            return redirect(url_for('facultylogin'))
    return render_template('faculty-login.html')


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    global otp1
    cur = msql.connection.cursor()
    if request.method == 'POST':
        slogininfo = request.form
        ssid = slogininfo['sid']
        cur.execute(f"SELECT sid FROM {studentTableName} ")
        a = cur.fetchall()
        flag = 0
        for x in a:
            if (str(x[0]) == ssid):
                flag += 1

        if flag == 0:
            flash("You are not registered!!,REGISTER NOW", 'danger')
            return redirect(url_for('register'))
        elif flag != 0:

            otp1 = str(random.randrange(100000, 999999))

            URL = 'https://www.way2sms.com/api/v1/sendCampaign'
            cur.execute(f"SELECT phone FROM {studentTableName} where sid= {ssid}")
            a = cur.fetchall()[0][0]
            #sms.sendPostRequest(URL, 'C23FTIDPYUYZVP7UV238S0QC1POBFWMR', 'N1AY9Q2S52NHUADE', 'stage', a, '9781396442', "Your OTP (One Time Password) to change your password is: "+str(otp1)+" Do not share this with anyone!   Team college+")
            return redirect(url_for('resetpass', phonenumber=a))

    return render_template('forgot.html')


@app.route('/reset<phonenumber>', methods=['GET', 'POST'])
def resetpass(phonenumber):
    cur = msql.connection.cursor()
    print(otp1)
    if request.method == 'POST':
        slogininfo = request.form
        ootp = slogininfo['otp']


        if ootp == (otp1):
            return redirect(url_for('newpass', phonenumber2=phonenumber))
        else:
            flash('INVALID OTP', 'danger')
            return redirect(url_for('resetpass', phonenumber=phonenumber))

    return render_template('otpverify.html')


@app.route('/newpass<phonenumber2>', methods=['GET', 'POST'])
def newpass(phonenumber2):
    cur = msql.connection.cursor()
    if request.method == 'POST':
        slogininfo = request.form
        newpassword = slogininfo['password']
        confirmnewpassword = slogininfo['cpassword']

        if (newpassword == confirmnewpassword):

            query = f" UPDATE  {studentTableName}  set passwordd = '{newpassword}' where phone =  {phonenumber2}  ; "

            cur.execute(query)
            msql.connection.commit()
            return redirect(url_for('studentlogin'))
        else:
            flash("passwords didnt match", 'danger')
            return redirect(url_for('newpass', phonenumber2=phonenumber2))
    return render_template('newpass.html')


@app.route('/studentloggedin')
def studentloggedin():
    cur = msql.connection.cursor()
    cur.execute(f"select stream from studentlogininfo where sid='{session['username']}'")
    a = cur.fetchone()
    strin = a[0]
    cur.execute(f"select f.fname,f.lname , a.postdate,a.title,a.content from announcements a join facultylogininfo f on a.author=f.loginid where receivers='{strin}' order by a.postdate desc ,a.priority  ")
    a = cur.fetchall()


    ssid = session.get('username')
    cur.execute(f"select * from studentlogininfo where sid={ssid}")
    b = cur.fetchone()
    name = b[0] + " " + b[1]

    email = b[3]
    phonenumber = b[5]

    return render_template('studenthome.html', tasks=a,name=name, email=email,ssid=ssid, phonenumber=phonenumber)


@app.route('/coursemanager')
def coursemanager():
    cur=msql.connection.cursor()
    cur.execute("select subid from subjectlist")
    courses=cur.fetchall()
    subjects=[]
    for i in range(len(courses)):
        cur.execute(f"select f.fname,f.lname from facultylogininfo f JOIN subjectlist s on s.instructorid=f.loginid where subid = '{courses[i][0]}'")
        names=cur.fetchone()
        subjects.append((courses[i][0],names[0]+" "+names[1]))



    return render_template('coursemanager.html',subjects=subjects)


@app.route('/course<courseid>')
def course(courseid):
    cur=msql.connection.cursor()
    cur.execute("select column_name from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME='marklist'")
    a=cur.fetchall()
    cur.execute(f"select * from marklist where subid = '{courseid}' and sid = '{session['username']}'")
    b=cur.fetchall()
    return render_template('course.html',a=a,b=b)

@app.route('/facultyloggedin', methods=['GET', 'POST'])
def facultyloggedin():
    cur = msql.connection.cursor()
    cur.execute(f"select department from facultylogininfo where loginid='{session['username']}'")
    a = cur.fetchone()
    department = a[0]
    cur.execute(f"select DISTINCT f.fname, f.lname , a.postdate , a.title , a.content, a.ano from announcements a join facultylogininfo f on a.author = f.loginid where f.loginid = '{session['username']}'")
    a  = cur.fetchall()

    loginid=session['username']
    cur.execute(f"select * from facultylogininfo where loginid= '{loginid}'")
    b = cur.fetchone()
    name = b[0] + " " + b[1]

    email = b[3]
    phonenumber = b[6]

    return render_template('facultyhome.html', tasks=a, name=name, email=email, department=department, phonenumber=phonenumber)


@app.route('/facultyannouncement', methods=['GET', 'POST'])
def facultyannouncement():
    cur=msql.connection.cursor()


    if request.method == 'POST':
        cur.execute(f"select max(ano) from announcements")
        abc=cur.fetchone()[0]

        if (abc == None):
            ano = 0
        else:
            ano = int(abc)

        ano += 1
        info = request.form
        loginid=session['username']
        today=date.today()
        title=info['title']
        content=info['content']
        priority=info['priority']
        for i in info.getlist('stream'):
            receivers=i
            values=f"('{loginid}','{content}','{today}','{receivers}','{title}','{priority}','{ano}')"
            cur.execute(f"INSERT into announcements values{values}")
        msql.connection.commit()
        flash('announcement successfully added','success')
        return redirect(url_for('facultyloggedin'))

    return render_template("facultyannouncement.html")


@app.route('/delete<ano>')
def delete(ano):
    cur=msql.connection.cursor()
    cur.execute(f"DELETE FROM ANNOUNCEMENTS WHERE ano = '{ano}'")
    msql.connection.commit()
    return redirect(url_for('facultyloggedin'))


@app.route('/edit<ano>',methods=["GET","POST"])
def edit (ano):
    cur=msql.connection.cursor()
    if request.method == 'POST':
        info=request.form
        content=info['content']
        title=info['title']
        cur.execute(f" update  announcements set title='{title}',content='{content}' where ano={ano} ")
        msql.connection.commit()
        return redirect(url_for('facultyloggedin'))

    cur.execute(f"SELECT * FROM ANNOUNCEMENTS WHERE ano= {ano}")
    a=cur.fetchone()
    return render_template('update.html',task=a)


@app.route('/addresult',methods=['GET', 'POST'])
def addresult():
    cur = msql.connection.cursor()
    if request.method == 'POST':
        data=request.form
        subject=data['subject']
        file=request.files['markscsv']
        file.save(secure_filename(file.filename))
        book=xlrd.open_workbook(f'{file.filename}')
        sheet=book.sheet_by_name("marks")
        for r in range(1, sheet.nrows):
            sid = sheet.cell(r, 0).value
            mst = sheet.cell(r, 1).value
            mstt = sheet.cell(r, 2).value
            est = sheet.cell(r, 3).value
            estt = sheet.cell(r, 4).value
            project = sheet.cell(r, 5).value
            projectt= sheet.cell(r, 6).value
            quiz = sheet.cell(r, 7).value
            quizt= sheet.cell(r, 8).value
            sid=str(sid)
            sid=sid[0:8]
            cur.execute(F"INSERT INTO MARKLIST VALUES ('{subject}','{sid}','{mst}','{mstt}','{est}','{estt}','{project}','{projectt}','{quiz}','{quizt}')")
            msql.connection.commit()
        flash('Result added successfully','success')
        return redirect(url_for('facultyloggedin'))



    cur.execute("select subid from subjectlist")
    a=cur.fetchall()
    return render_template('addresult.html',a=a)

@app.route('/logout', methods=['GET', 'POST'])
def logout():

        session.pop('username', None)
        return redirect(url_for('home'))

#==================================================================
if __name__ == '__main__':
    app.run(host='172.31.77.165', port=5000, debug=True)

