from threading import Thread
# from flask import Flask

# app = Flask('')

# @app.route('/')
# def home():
#     return "I'm alive"

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
  t = Thread(target=run)
  t.start()
