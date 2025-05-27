from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import json
import threading
import time

from maps_search import buscar_dados_cards_maps
from search_engine import buscar_links_site_maps
from scraper import extrair_contatos


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_mega_segura'  # 🔥 Troque por uma chave segura
CORS(app)


# 🔥 Status das buscas por usuário
status_buscas = {}


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


# 🔥 Função que executa a busca em segundo plano
def executar_busca(username, termo, limite=50):
    try:
        # Etapa 1: Preparação
        status_buscas[username]["mensagem"] = "Iniciando busca..."
        status_buscas[username]["progresso"] = 5

        # Etapa 2: Buscando no Google Maps
        status_buscas[username]["mensagem"] = "Buscando no Google Maps: 'termo'..." # Exibindo o nome da etapa e o termo
        status_buscas[username]["progresso"] = 10

        resultado = buscar_dados_cards_maps(
            termo=termo,
            limite=limite,
            username=username,
            status_buscas=status_buscas
        )

        # Etapa 3: Analisando os resultados
        status_buscas[username]["mensagem"] = "Analisando os resultados da busca..." # Exibindo o nome da etapa
        status_buscas[username]["progresso"] = 60

        # Etapa 4: Processando resultados
        status_buscas[username]["mensagem"] = "Processando resultados encontrados..." # Exibindo o nome da etapa
        status_buscas[username]["progresso"] = 80

        time.sleep(1)  # Simula processamento final

        # Etapa 5: Busca finalizada
        status_buscas[username]["mensagem"] = "Busca finalizada com sucesso." # Exibindo o nome da etapa
        status_buscas[username]["progresso"] = 100
        status_buscas[username]["status"] = "concluido"
        status_buscas[username]["resultado"] = resultado

    except Exception as e:
        status_buscas[username]["mensagem"] = f"❌ Erro na busca: {str(e)}"
        status_buscas[username]["status"] = "erro"
        status_buscas[username]["progresso"] = 0

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


# === DASHBOARD ===

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])


# === Middleware de proteção ===

def login_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Não autorizado"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


# === APIs ===

@app.route('/api/iniciar-busca', methods=['POST'])
@login_required
def iniciar_busca():
    data = request.json
    termo = data.get("termo")
    limite = data.get("limite", 5)

    if not termo:
        return jsonify({"error": "Termo não informado"}), 400

    username = session['username']

    # 🔥 Inicializa o status da busca (ESSENCIAL)
    status_buscas[username] = {
        "status": "buscando",
        "mensagem": "Iniciando busca...",
        "progresso": 0,
        "parciais": [],  # 🕵️ O que está sendo visto no momento
        "resultado": []
    }

    # 🔥 Executa a busca em segundo plano
    thread = threading.Thread(target=executar_busca, args=(username, termo, limite))
    thread.start()

    return jsonify({"mensagem": "Busca iniciada com sucesso"})


@app.route('/api/status-busca', methods=['GET'])
@login_required
def status_busca():
    username = session['username']
    status = status_buscas.get(username, {
        "status": "parado",
        "mensagem": "Nenhuma busca em andamento",
        "progresso": 0,
        "parciais": [],
        "resultado": []
    })
    return jsonify(status)


@app.route('/api/resetar-busca', methods=['POST'])
@login_required
def resetar_busca():
    username = session['username']
    status_buscas.pop(username, None)
    return jsonify({"mensagem": "Busca resetada com sucesso"})


# 🔍 APIs auxiliares opcionais

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


# === App ===

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
