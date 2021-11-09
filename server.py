#!/usr/bin/env python

"""
Columbia's COMS W4111.003 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.152.219/proj1part2
#
# For example, if you had username biliris and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://biliris:foobar@104.196.152.219/proj1part2"
#
DATABASEURI = "postgresql://yc4005:4111Pswd@35.196.73.133/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/', methods=['GET','POST'])
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print (request.args)
  result = []
  if request.form.get('teachers') or request.form.get('department'):
    teachers = request.form.get('teachers')
    department = request.form.get('department')
    cursor = g.conn.execute('''SELECT S.name, S.tid, S.birthday, S.salary, S.department, T.rating, T.class_id
                                FROM teachers S, teach T
                                WHERE T.tid=S.tid
                                AND ('%s' = 'None' OR S.name ILIKE '%%%%%s%%%%')
                                AND ('%s' = 'None' OR S.department ILIKE '%%%%%s%%%%')
                                ORDER BY T.rating DESC''' % (teachers, teachers, department, department))
    result = cursor.fetchall()

  #
  # example of a database query
  #
    cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = result)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/student', methods=['GET','POST'])
def student():
  result = []
  if request.form.get('students') or request.form.get('major'):
    students = request.form.get('students')
    major = request.form.get('major')
    cursor = g.conn.execute('''SELECT S.name, S.sid, S.birthday, S.year, S.major, S.gpa, SE.class_id, SO.organization_name
                                FROM students S, student_enroll SE, student_organizations SO
                                WHERE ('%s' = 'None' OR S.name ILIKE '%%%%%s%%%%')
                                AND ('%s' = 'None' OR S.major ILIKE '%%%%%s%%%%')
                                AND S.sid = SE.sid
                                AND SO.sid = S.sid
                                ORDER BY S.name
                                ''' % (students, students, major, major))
    result = cursor.fetchall()

  #
  # example of a database query
  #
    cursor.close()
  context = dict(data=result)
  return render_template("student.html", **context)

@app.route('/class', methods=['GET','POST'])
def classes():
  result = []
  if request.form.get('classes') or request.form.get('location'):
    classes = request.form.get('classes')
    location = request.form.get('location')
    cursor = g.conn.execute('''SELECT Cl.class_id, Cl.capacity, Cl.held_days, Cr.room_id, T.name
                                FROM classes Cl, classrooms Cr, classes_are_held Ch, Teach Te, teachers T
                                WHERE ('%s' = 'None' OR Cl.class_id ILIKE '%%%%%s%%%%')
                                AND ('%s' = 'None' OR Cr.room_id ILIKE '%%%%%s%%%%') 
                                AND Cl.class_id = Ch.class_id
                                AND Ch.room_id = Cr.room_id
                                AND Te.class_id = Cl.class_id
                                AND Te.tid = T.tid
                                ''' % (classes, classes, location, location))
    result = cursor.fetchall()

  #
  # example of a database query
  #
    cursor.close()
  context = dict(data=result)
  return render_template("class.html", **context)

@app.route('/top10student', methods=['GET', 'POST'])
def top10student():
  cursor = g.conn.execute('''SELECT S.name, S.sid, S.birthday, S.year, S.major, S.gpa
                              FROM students S
                              ORDER BY S.gpa DESC LIMIT 10
                              ''')
  result = cursor.fetchall()
  cursor.close()
  context = dict(data=result)
  return render_template("top10student.html", **context)

@app.route('/top10teacher', methods=['GET', 'POST'])
def top10teacher():
  cursor = g.conn.execute('''SELECT S.name, S.tid, S.birthday, S.salary, S.department, T.rating, T.class_id
                              FROM teachers S, teach T
                              WHERE T.tid=S.tid
                              ORDER BY T.rating DESC LIMIT 10''')
  result = cursor.fetchall()
  cursor.close()
  context = dict(data=result)
  return render_template("top10teacher.html", **context)


@app.route('/department', methods=['GET', 'POST'])
def department():
  cursor = g.conn.execute('''SELECT DISTINCT S.name AS formalname, 'student' AS identities
                            FROM students S
                            WHERE S.major = 'CS'
                            UNION
                            SELECT DISTINCT T.name AS formalname, 'teacher' AS identities
                            FROM teachers T
                            WHERE T.department = 'CS'
                            UNION
                            SELECT DISTINCT A.name AS formalname, 'administrator' AS identities
                            FROM administrators A
                            WHERE A.department = 'CS'
                            ORDER BY identities
                            ''')
  csResult = cursor.fetchall()
  cursor.close()

  cursor = g.conn.execute('''SELECT DISTINCT S.name AS formalname, 'student' AS identities
                            FROM students S
                            WHERE S.major = 'Music'
                            UNION
                            SELECT DISTINCT T.name AS formalname, 'teacher' AS identities
                            FROM teachers T
                            WHERE T.department = 'Music'
                            UNION
                            SELECT DISTINCT A.name AS formalname, 'administrator' AS identities
                            FROM administrators A
                            WHERE A.department = 'Music'
                            ORDER BY identities
                            ''')
  musicResult = cursor.fetchall()
  cursor.close()

  cursor = g.conn.execute('''SELECT DISTINCT S.name AS formalname, 'student' AS identities
                            FROM students S
                            WHERE S.major = 'English'
                            UNION
                            SELECT DISTINCT T.name AS formalname, 'teacher' AS identities
                            FROM teachers T
                            WHERE T.department = 'English'
                            UNION
                            SELECT DISTINCT A.name AS formalname, 'administrator' AS identities
                            FROM administrators A
                            WHERE A.department = 'English'
                            ORDER BY identities
                            ''')
  englishResult = cursor.fetchall()
  cursor.close()

  cursor = g.conn.execute('''SELECT DISTINCT S.name AS formalname, 'student' AS identities
                            FROM students S
                            WHERE S.major = 'Math'
                            UNION
                            SELECT DISTINCT T.name AS formalname, 'teacher' AS identities
                            FROM teachers T
                            WHERE T.department = 'Math'
                            UNION
                            SELECT DISTINCT A.name AS formalname, 'administrator' AS identities
                            FROM administrators A
                            WHERE A.department = 'Math'
                            ORDER BY identities
                            ''')
  mathResult = cursor.fetchall()
  cursor.close()

  cursor = g.conn.execute('''SELECT DISTINCT S.name AS formalname, 'student' AS identities
                            FROM students S
                            WHERE S.major = 'History'
                            UNION
                            SELECT DISTINCT T.name AS formalname, 'teacher' AS identities
                            FROM teachers T
                            WHERE T.department = 'History'
                            UNION
                            SELECT DISTINCT A.name AS formalname, 'administrator' AS identities
                            FROM administrators A
                            WHERE A.department = 'History'
                            ORDER BY identities
                            ''')
  historyResult = cursor.fetchall()
  cursor.close()
  return render_template("department.html", csResult=csResult, mathResult=mathResult, musicResult=musicResult,
                         englishResult=englishResult, historyResult=historyResult)


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
