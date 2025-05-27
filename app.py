from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import json

from maps_search import buscar_dados_cards_maps
from search_engine import buscar_links_site_maps
from scraper import extrair_contatos

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_mega_segura'  # Altere isso!
CORS(app)

# === Funções auxiliares ===

def load_users():
    with open('users_db.json') as f:
        return json.load(f)

def check_login(username, password):
    users = load_users()
    user = users.get(username)
    if user and user['password'] == password:
        return True
    return False


# === ROTAS DE LOGIN ===

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_login(username, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# === DASHBOARD (PROTEGIDO) ===

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])


# === APIs protegidas ===

def login_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Não autorizado"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@app.route('/api/buscar-dados-maps', methods=['POST'])
@login_required
def buscar_dados_maps():
    data = request.json
    termo = data.get("termo")
    limite = data.get("limite", 5)

    if not termo:
        return jsonify({"error": "Termo não informado"}), 400

    resultado = buscar_dados_cards_maps(termo, limite=limite)
    return jsonify(resultado)


@app.route('/api/buscar-links-sites', methods=['POST'])
@login_required
def buscar_links_sites():
    data = request.json
    termo = data.get("termo")

    if not termo:
        return jsonify({"error": "Termo não informado"}), 400

    links = buscar_links_site_maps(termo)
    return jsonify(links)


@app.route('/api/scrapear-contato', methods=['POST'])
@login_required
def scrapear_contato():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL não informada"}), 400

    contatos = extrair_contatos(url)
    return jsonify(contatos)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
