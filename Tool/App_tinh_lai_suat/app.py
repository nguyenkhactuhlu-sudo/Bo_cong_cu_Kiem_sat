"""Thin web wrapper; all interest calculations run in index.html JavaScript."""

from flask import Flask, render_template


app = Flask(__name__, template_folder='.')


@app.get('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
