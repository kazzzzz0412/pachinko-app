from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "パチンコ羽根モノ期待値アプリ、動いてます！"

if __name__ == '__main__':
    app.run()
