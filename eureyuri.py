from flask import Flask, render_template

app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(e):
    # TODO
    print(e)
    return "404"


@app.route('/', methods=["GET"])
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.debug = True
    app.run()
    app.run(debug=True)
