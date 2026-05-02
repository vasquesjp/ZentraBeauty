from flask import Flask, render_template

app = Flask(__name__)

# Rota principal (A pagina inicial do site)
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)