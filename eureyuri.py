from flask import Flask, render_template

app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(e):
    print(e)
    return render_template("notfound.html")


@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


@app.route('/about', methods=["GET"])
def about():
    return render_template("about.html")


@app.route('/blog', methods=["GET"])
def work():
    return render_template("blog.html")


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
