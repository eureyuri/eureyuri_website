from flask import Flask, render_template

app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(e):
    # TODO
    print(e)
    return "404"


@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


@app.route('/about', methods=["GET"])
def about():
    return render_template("about.html")


@app.route('/work', methods=["GET"])
def work():
    return render_template("work.html")


@app.route('/interests', methods=["GET"])
def interests():
    return render_template("interests.html")


# @app.route('/login', methods=["GET"])
# def login():
#     return render_template("login.html")


if __name__ == '__main__':
    # app.debug = True
    # app.run()
    app.run(debug=True)
