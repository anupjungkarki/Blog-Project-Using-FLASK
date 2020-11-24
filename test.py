from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def hello_world():
    # return 'Hello, World!'
    return render_template('test.html')
@app.route('/home')
def blog_website():
    return render_template('home.html')


app.run()
