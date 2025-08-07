from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import json
import threading
import time
# Certifique-se de que estes módulos existem e estão acessíveis
from maps_search import buscar_dados_cards_maps
from search_engine import buscar_links_site_maps
from scraper import extrair_contatos
import os, requests
from pprint import pprint # <<<< Mude para ESTA linha
import re

# Variáveis de ambiente (ou use .env)
# 🔒 Recomendado usar os.environ.get() para tokens em produção
ACCESS_TOKEN = 'EAANuRAtxBYEBPMSuTHGlmjkRKCSixxg3cyZAhW9xEyZAph1ED3Y5YJyJLyGYsOJ24oZBNXDAbZBT96ZAhQ4Rl0zn2QvU5KhEkqhUYXHvZAFlgFOFiO93eK4ml4ZAwQSGywpfAcjQqSssMhexHDvEJgC4hYrGyCkS3sKZBgm6KbiUFBdHjMPgaH305RHgvrg8K3KKcgZDZD'
WHATSAPP_BUSINESS_ACCOUNT_ID = '684848121166205' # Este ID é para gerenciar a conta e buscar templates
PHONE_NUMBER_ID = '655247557670398'
VERIFY_TOKEN_WEBHOOK = '2yhrqG6O4JBvT2zGXm1CWsxDadz_56XSWTU2BU6XwXcgNqnko' # Token de verificação do Webhook da Meta

app = Flask(__name__)
app.secret_key = '6e9750a7f8050c604ba15d542bfcd5b1d2453c264b8f9770'  # 🔥 Troque por uma chave segura
CORS(app)

# 🔥 Status das buscas por usuário
status_buscas = {}

# Diretório base da aplicação (onde app.py está localizado)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define os caminhos para os arquivos de dados
DATA_DIR = os.path.join(BASE_DIR, 'data')
LEADS_FILE = os.path.join(DATA_DIR, 'leads.json')
PENDING_LEADS_FILE = os.path.join(DATA_DIR, 'pending_leads.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json') # Ajustado para usar DATA_DIR

# Caminho correto para o diretório de mensagens dentro de 'data'
MESSAGES_DIR = os.path.join(DATA_DIR, 'mensagens')

# Garante que os diretórios 'data' e 'mensagens' existam
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MESSAGES_DIR, exist_ok=True)

# Garante que os diretórios 'data' e 'mensagens' existam
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(MESSAGES_DIR):
    os.makedirs(MESSAGES_DIR)


# --- Funções de Gerenciamento de Leads Globais ---

def load_leads():
    """Carrega leads do arquivo JSON."""
    if not os.path.exists(LEADS_FILE):
        return []
    with open(LEADS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_leads(leads):
    """Salva leads no arquivo JSON."""
    with open(LEADS_FILE, 'w', encoding='utf-8') as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

# --- Funções de Gerenciamento de Leads Pendentes ---

def load_pending_leads():
    """Carrega leads pendentes do arquivo JSON."""
    if not os.path.exists(PENDING_LEADS_FILE):
        return []
    with open(PENDING_LEADS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_pending_leads(pending_leads):
    """Salva leads pendentes no arquivo JSON."""
    with open(PENDING_LEADS_FILE, 'w', encoding='utf-8') as f:
        json.dump(pending_leads, f, indent=2, ensure_ascii=False)

# <<< FUNÇÃO MOVIDA E TORNADA GLOBAL >>>
def remove_pending_lead_by_phone(phone_number_to_remove):
    normalized_phone = normalize_phone_number(phone_number_to_remove)
    if not normalized_phone:
        print(f"ERROR: Não foi possível normalizar o número '{phone_number_to_remove}' para remoção de lead pendente.")
        return False

    print(f"DEBUG_REMOVE_PENDING: Tentando remover lead pendente com número normalizado: '{normalized_phone}'")
    pending_leads = load_pending_leads()
    initial_count = len(pending_leads)

    # Filtra os leads, mantendo apenas aqueles cujo telefone não é o que queremos remover
    # Garante que a comparação também seja com o número normalizado do lead salvo
    new_pending_leads = [
        lead for lead in pending_leads
        if normalize_phone_number(lead.get('telefone')) != normalized_phone
    ]

    if len(new_pending_leads) < initial_count:
        save_pending_leads(new_pending_leads)
        print(f"DEBUG_REMOVE_PENDING: Lead '{normalized_phone}' removido de pending_leads.json. Novos leads: {len(new_pending_leads)}")
        return True
    else:
        print(f"DEBUG_REMOVE_PENDING: Lead '{normalized_phone}' NÃO encontrado em pending_leads.json para remoção.")
        return False
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def add_new_leads_to_system(new_leads):
    """
    Adiciona novos leads ao sistema (tanto leads gerais quanto pendentes),
    evitando duplicatas.
    """
    existing_leads = load_leads()
    existing_pending_leads = load_pending_leads()
    added_to_general_count = 0
    added_to_pending_count = 0

    # Identificadores de leads já existentes (geral e pendentes)
    existing_identifiers = set()
    for lead_list in [existing_leads, existing_pending_leads]:
        for lead in lead_list:
            if lead.get('site') and lead['site'] != "Site não encontrado":
                existing_identifiers.add(lead['site'])
            else:
                # Usar nome e endereço para identificar se não há site
                existing_identifiers.add((lead.get('nome'), lead.get('endereco')))

    leads_to_add_to_general = []
    leads_to_add_to_pending = []

    for lead in new_leads:
        identifier = None
        if lead.get('site') and lead['site'] != "Site não encontrado":
            identifier = lead['site']
        else:
            identifier = (lead.get('nome'), lead.get('endereco'))

        # Apenas adicione se o identificador não for None e não existir
        if identifier and identifier not in existing_identifiers:
            # ===> AQUI ESTÁ A LINHA ADICIONADA <===
            # Garante que todo novo lead adicionado já tenha o status inicial
            lead['status_contato'] = 'pendente'
            # ====================================

            leads_to_add_to_general.append(lead)
            # Adiciona à fila de pendentes se tiver telefone
            if lead.get('telefone') and lead['telefone'] != "Telefone não encontrado":
                leads_to_add_to_pending.append(lead)
            existing_identifiers.add(identifier)  # Adiciona o novo identificador ao conjunto
            added_to_general_count += 1

    if leads_to_add_to_general:
        existing_leads.extend(leads_to_add_to_general)
        save_leads(existing_leads)

    if leads_to_add_to_pending:
        existing_pending_leads.extend(leads_to_add_to_pending)
        save_pending_leads(existing_pending_leads)
        added_to_pending_count = len(leads_to_add_to_pending)  # Conta os que foram adicionados à fila

    return added_to_general_count, added_to_pending_count


def migrate_leads_status():
    """Adiciona o campo 'status_contato' e normaliza telefones de leads existentes."""
    leads = load_leads()
    pending_leads = load_pending_leads()

    updated_leads = False

    # Migra leads gerais
    for lead in leads:
        if 'status_contato' not in lead:
            lead['status_contato'] = 'novo'
            updated_leads = True
        # ===> Normaliza o telefone ao migrar <===
        if lead.get('telefone'):
            original_phone = lead['telefone']
            normalized_phone = normalize_phone_number(original_phone)
            if original_phone != normalized_phone: # Se houve alteração
                lead['telefone'] = normalized_phone
                updated_leads = True
                print(f"DEBUG: Telefone de lead {original_phone} normalizado para {normalized_phone}.")
        # ========================================

    # Migra leads pendentes
    for lead in pending_leads:
        if 'status_contato' not in lead:
            lead['status_contato'] = 'pendente'
            updated_leads = True
        # ===> Normaliza o telefone ao migrar <===
        if lead.get('telefone'):
            original_phone = lead['telefone']
            normalized_phone = normalize_phone_number(original_phone)
            if original_phone != normalized_phone:
                lead['telefone'] = normalized_phone
                updated_leads = True
                print(f"DEBUG: Telefone de lead pendente {original_phone} normalizado para {normalized_phone}.")
        # ========================================

    if updated_leads:
        save_leads(leads)
        save_pending_leads(pending_leads)
        print("DEBUG: Leads migrados e telefones normalizados para a nova estrutura.")

# === Funções auxiliares existentes ===

def salvar_mensagem(numero_original, texto, timestamp, remetente="received"):
    print(f"DEBUG_SAVE: Início de salvar_mensagem para número original: '{numero_original}' (remetente: '{remetente}')")

    numero = normalize_phone_number(numero_original) # Normaliza o número

    if not numero:
        print(f"ERROR_SAVE: Não foi possível normalizar o número para salvar mensagem: '{numero_original}'. Abortando.")
        return False # Indica que falhou

    # Constrói o caminho completo para o arquivo JSON do chat
    path = os.path.join(MESSAGES_DIR, f"{numero}.json")
    print(f"DEBUG_SAVE: Caminho do arquivo de chat esperado: '{path}'")

    mensagens = []

    # Tenta ler o arquivo JSON existente
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                mensagens = json.load(f)
            print(f"DEBUG_SAVE: Arquivo de chat existente lido com sucesso: '{path}'. Contém {len(mensagens)} mensagens.")
        except json.JSONDecodeError as e:
            print(f"ERROR_SAVE: Arquivo JSON de chat corrompido para '{numero}'. Erro: {e}. Criando um novo arquivo.")
            mensagens = [] # Se corrompido, começa com uma lista vazia
        except Exception as e:
            print(f"ERROR_SAVE: Erro inesperado ao ler arquivo de chat '{path}': {e}. Criando um novo arquivo.")
            mensagens = [] # Para outros erros de leitura

    # Adiciona a nova mensagem
    nova_mensagem = {
        "sender": remetente,
        "text": texto,
        "timestamp": timestamp
    }
    mensagens.append(nova_mensagem)
    print(f"DEBUG_SAVE: Nova mensagem adicionada à lista. Total de mensagens: {len(mensagens)}.")

    # Tenta salvar a lista de mensagens atualizada no arquivo JSON
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(mensagens, f, indent=2, ensure_ascii=False)
        print(f"DEBUG_SAVE: Mensagem de '{remetente}' para '{numero}' salva COM SUCESSO em '{path}'.")
        return True # Indica que salvou com sucesso
    except Exception as e:
        print(f"ERROR_SAVE: ERRO CRÍTICO ao salvar mensagem para '{numero}' em '{path}': {e}")
        return False # Indica que falhou


def load_users():
    """Carrega usuários do arquivo JSON."""
    users_file = USERS_FILE
    if not os.path.exists(users_file):
        # Cria um arquivo de usuários padrão se não existir
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump({"admin": {"password": "admin"}}, f, indent=2)
    with open(users_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_phone_number(phone_number):
    """
    Normaliza números de telefone brasileiros para o formato E.164 (+55DD9XXXXXXXX).
    Remove caracteres não numéricos.
    Garante que o '9' seja adicionado para números de celular brasileiros
    que deveriam tê-lo e que o DDI/DDD estejam presentes.
    """
    if not phone_number:
        return None

    # 1. Remove todos os caracteres não numéricos
    digits_only = re.sub(r'\D', '', phone_number)
    print(f"DEBUG_NORM: Original: '{phone_number}' -> Digits Only: '{digits_only}'")

    # 2. Garante que começa com '55' (DDI Brasil)
    if not digits_only.startswith('55'):
        # Se tem 10 ou 11 dígitos, assume que é DDD + Número e adiciona '55'
        if len(digits_only) == 10 or len(digits_only) == 11:
            digits_only = '55' + digits_only
            print(f"DEBUG_NORM: Adicionado '55'. Novo digits_only: '{digits_only}'")
        else:
            # Se não tem '55' e não parece um número brasileiro típico,
            # tenta retornar o que tem com '+' ou None.
            print(f"WARN_NORM: Número '{phone_number}' não parece um número brasileiro e não começa com '55'.")
            return f"+{digits_only}" if digits_only else None

    # 3. Lógica para o 9º dígito em celulares (aplica-se após o DDI e DDD)
    # Um número de celular brasileiro no formato E.164 (com DDI e DDD) tem 13 dígitos:
    # +55 (2) + DD (2) + 9 (1) + XXXXXXXX (8) = 13 dígitos
    # Se tem 12 dígitos, significa que falta o '9' (ou é um fixo, mas para WhatsApp, focamos em celular)
    # Ex: 556188898193 (12 dígitos) -> Precisa virar 5561988898193 (13 dígitos)

    # Verifica se o número tem o formato esperado para um celular brasileiro sem o 9 inicial (12 dígitos)
    # e o 5º dígito (índice 4) não é '9'.
    # Isso cobre casos como 556181234567 que deveria ser 5561981234567
    if len(digits_only) == 12 and digits_only.startswith('55') and len(digits_only[4:]) == 8:
        # Insere '9' após o DDD (na posição de índice 4)
        digits_only = digits_only[:4] + '9' + digits_only[4:]
        print(f"DEBUG_NORM: '9' adicionado. Novo digits_only: '{digits_only}'")

    # Verifica se o número já tem o 9º dígito e 13 dígitos
    # Isso é o formato ideal: +55DD9XXXXXXXXX
    if len(digits_only) == 13 and digits_only.startswith('55') and digits_only[4] == '9':
        print(f"DEBUG_NORM: Número já no formato correto (13 dígitos com '9').")
        # Já está no formato esperado, sem necessidade de mais modificações

    # Se o número tem mais de 13 dígitos ou menos de 10 após o DDI (55),
    # pode ser um formato inesperado.
    elif len(digits_only) > 13:
         print(f"WARN_NORM: Número '{digits_only}' tem mais de 13 dígitos. Pode estar incorreto.")
    elif len(digits_only) < 10:
         print(f"WARN_NORM: Número '{digits_only}' tem menos de 10 dígitos (após 55). Pode estar incorreto.")


    final_number = f"+{digits_only}"
    print(f"DEBUG_NORM: Resultado final da normalização para '{phone_number}': '{final_number}'")
    return final_number


def check_login(username, password):
    """Verifica as credenciais de login."""
    users = load_users()
    user = users.get(username)
    if user and user['password'] == password:
        return True
    return False


# 🔥 Função que executa a busca em segundo plano
def executar_busca(username, termo, limite=50):
    try:
        status_buscas[username]["mensagem"] = "Iniciando busca..."
        status_buscas[username]["progresso"] = 5

        status_buscas[username]["mensagem"] = f"Buscando no Google Maps por: '{termo}'..."
        status_buscas[username]["progresso"] = 10

        resultado_da_busca_selenium = buscar_dados_cards_maps(
            termo=termo,
            limite=limite,
            username=username,
            status_buscas=status_buscas
        )

        status_buscas[username]["mensagem"] = "Verificando e salvando novos leads..."
        status_buscas[username]["progresso"] = 80

        added_to_general, added_to_pending = add_new_leads_to_system(resultado_da_busca_selenium)

        status_buscas[username][
            "mensagem"] = f"Busca finalizada! Total de leads encontrados: {len(resultado_da_busca_selenium)}. Novos leads gerais salvos: {added_to_general}. Novos leads adicionados à fila de contato: {added_to_pending}."
        status_buscas[username]["progresso"] = 100
        status_buscas[username]["status"] = "concluido"
        status_buscas[username]["resultado"] = resultado_da_busca_selenium

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
        username = request.form.get('username')
        password = request.form.get('password')

        if check_login(username, password):
            session['username'] = username
            return jsonify({"status": "success", "redirect": url_for('dashboard')})
        else:
            return jsonify({"status": "error", "message": "Usuário ou senha inválidos"}), 401
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
    """Decorador para proteger rotas que exigem login."""
    from functools import wraps # Importa aqui para garantir que está disponível
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            # Para APIs, retornar JSON; para páginas, redirecionar
            if request.path.startswith('/api/'):
                return jsonify({"error": "Não autorizado"}), 401
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper


# === APIs ===

@app.route('/api/iniciar-busca', methods=['POST'])
@login_required
def iniciar_busca_api():
    data = request.json
    termo = data.get("termo")
    limite = data.get("limite", 5)

    if not termo:
        return jsonify({"error": "Termo não informado"}), 400

    username = session['username']

    if username in status_buscas and status_buscas[username]["status"] == "buscando":
        return jsonify({"mensagem": "Já existe uma busca em andamento."}), 409 # Conflict

    status_buscas[username] = {
        "status": "buscando",
        "mensagem": "Iniciando busca...",
        "progresso": 0,
        "parciais": [],
        "resultado": []
    }

    thread = threading.Thread(target=executar_busca, args=(username, termo, limite))
    thread.start()

    return jsonify({"mensagem": "Busca iniciada com sucesso"})


@app.route('/api/status-busca', methods=['GET'])
@login_required
def status_busca_api():
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
def resetar_busca_api():
    username = session['username']
    status_buscas.pop(username, None)
    return jsonify({"mensagem": "Busca resetada com sucesso"})


# 🔍 APIs auxiliares opcionais

@app.route('/api/buscar-links-sites', methods=['POST'])
@login_required
def buscar_links_sites_api():
    data = request.json
    termo = data.get("termo")

    if not termo:
        return jsonify({"error": "Termo não informado"}), 400

    links = buscar_links_site_maps(termo)
    return jsonify(links)


@app.route('/api/scrapear-contato', methods=['POST'])
@login_required
def scrapear_contato_api():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL não informada"}), 400

    contatos = extrair_contatos(url)
    return jsonify(contatos)


@app.route('/api/chats', methods=['GET'])
@login_required
def listar_chats_api():
    if not os.path.exists(MESSAGES_DIR):
        return jsonify([])

    arquivos = [
        f.replace('.json', '')
        for f in os.listdir(MESSAGES_DIR)
        if f.endswith('.json')
    ]
    return jsonify(arquivos)


@app.route('/api/mensagens', methods=['GET'])
@login_required
def mensagens_api():
    numero_original = request.args.get('numero')  # Recebe o número do frontend
    numero = normalize_phone_number(numero_original)  # Normaliza o número

    if not numero:
        return jsonify({"erro": "Número não informado ou inválido após normalização"}), 400

    path = os.path.join(MESSAGES_DIR, f"{numero}.json")
    print(f"DEBUG: Tentando carregar mensagens de: {path}")  # Log para depuração
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                mensagens = json.load(f)
            print(f"DEBUG: Mensagens carregadas para {numero}: {len(mensagens)} mensagens.")
            return jsonify(mensagens)
        except json.JSONDecodeError as e:
            print(f"ERROR: Arquivo JSON corrompido para {numero}: {e}")
            return jsonify([]), 500  # Retorna vazio e erro se o JSON estiver corrompido
    print(f"DEBUG: Arquivo de mensagens não encontrado para {numero}.")
    return jsonify([])


# ** Este endpoint NÃO é para enviar mensagens do frontend, é um webhook para receber da Meta **
# Foi renomeado de 'enviar_mensagem' para 'enviar_mensagem_whatsapp_api' para clareza,
# mas o endpoint correto para mensagens DE TEXTO LIVRE do frontend é 'enviar_mensagem_personalizada'
# ou 'enviar_template'.
@app.route('/api/enviar-mensagem-padrao', methods=['POST'])
@login_required
def enviar_mensagem_padrao_api():
    """
    OBS: Este endpoint agora é 'enviar-mensagem-padrao'.
    Se o seu frontend ainda chama '/api/enviar-mensagem', ele precisa ser atualizado
    para '/api/enviar-mensagem-personalizada' ou '/api/enviar-template'.
    Esta função foi movida para que o nome '/api/enviar-mensagem' fique livre
    para um futuro uso de Webhook ou outro propósito mais claro.
    """
    data = request.json
    numero = data.get('numero')
    mensagem = data.get('mensagem') # A mensagem completa vem do frontend

    if not numero or not mensagem:
        return jsonify({"erro": "Número e mensagem são obrigatórios"}), 400

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensagem
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        if response.ok:
            salvar_mensagem(numero, mensagem, int(time.time()), remetente='sent')
            # remove_pending_lead_by_phone(numero) # Removido daqui, pois o chat normal não remove o lead pendente automaticamente
            return jsonify(response_data), 200
        else:
            print(f"Erro da API do WhatsApp ao enviar mensagem padrão: {response_data}")
            error_message = response_data.get('error', {}).get('message', 'Erro desconhecido da API do WhatsApp.')
            return jsonify({"erro": error_message}), response.status_code
    except Exception as e:
        print(f"Erro na requisição para a API do WhatsApp (padrão): {str(e)}")
        return jsonify({"erro": f"Falha interna ao enviar mensagem padrão: {str(e)}"}), 500


# RECEBER MENSAGENS (WEBHOOK)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook_whatsapp():
    if request.method == 'GET':
        # Lógica de verificação do webhook (já existe)
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode and token:
            if mode == 'subscribe' and token == VERIFY_TOKEN_WEBHOOK:
                print('WEBHOOK_VERIFIED')
                return Response(challenge, mimetype='text/plain'), 200
            else:
                return 'Forbidden', 403
        else:
            return 'Bad Request', 400

    elif request.method == 'POST':
        data = request.get_json()
        print("🔔 Nova mensagem recebida (Webhook POST):")
        pprint(data) # Para depuração

        if data and 'object' in data and 'entry' in data:
            for entry in data['entry']:
                for change in entry['changes']:
                    if change.get('field') == 'messages':
                        value = change.get('value', {})
                        messages = value.get('messages', [])
                        contacts = value.get('contacts', [])

                        # Mapear contatos por wa_id para facilitar a busca de nome
                        contact_names = {c.get('wa_id'): c.get('profile', {}).get('name', c.get('wa_id')) for c in contacts}

                        for mensagem in messages:
                            numero = normalize_phone_number(mensagem.get('from'))
                            mensagem_id = mensagem.get('id')
                            timestamp = mensagem.get('timestamp')
                            tipo_mensagem = mensagem.get('type')
                            # Extrai o nome do contato se disponível
                            nome_contato = contact_names.get(numero, numero)

                            texto = None
                            if tipo_mensagem == 'text':
                                texto = mensagem.get('text', {}).get('body')
                            elif tipo_mensagem == 'button':
                                texto = f"Botão clicado: {mensagem.get('button', {}).get('text')}"
                                # Opcional: registrar payload do botão se necessário
                            elif tipo_mensagem == 'interactive':
                                # Para mensagens interativas, você pode extrair o texto de acordo com o tipo
                                # Ex: list_reply, button_reply
                                interactive_data = mensagem.get('interactive', {})
                                if interactive_data.get('type') == 'list_reply':
                                    texto = f"Resposta da lista: {interactive_data.get('list_reply', {}).get('title')} (ID: {interactive_data.get('list_reply', {}).get('id')})"
                                elif interactive_data.get('type') == 'button_reply':
                                    texto = f"Resposta do botão: {interactive_data.get('button_reply', {}).get('title')} (ID: {interactive_data.get('button_reply', {}).get('id')})"
                            elif tipo_mensagem == 'reaction':
                                emoji = mensagem.get('reaction', {}).get('emoji')
                                texto = f"Reação: {emoji}"
                            elif tipo_mensagem == 'image':
                                texto = "Imagem recebida" # Ou você pode tentar obter a caption: mensagem.get('image', {}).get('caption')
                            elif tipo_mensagem == 'video':
                                texto = "Vídeo recebido"
                            elif tipo_mensagem == 'audio':
                                texto = "Áudio recebido"
                            elif tipo_mensagem == 'document':
                                texto = "Documento recebido"
                            elif tipo_mensagem == 'location':
                                texto = "Localização recebida"
                            elif tipo_mensagem == 'contacts':
                                texto = "Contato(s) recebido(s)"
                            # Adicione mais tipos conforme necessário

                            if numero and texto:
                                # Salva a mensagem recebida no histórico (já está fazendo)
                                salvar_mensagem(numero, texto, int(timestamp), remetente='received')
                                print(f"DEBUG: Mensagem de {numero} salva: {texto}")

                                # ===> INÍCIO DAS NOVAS LINHAS <===
                                # 1. Atualizar o status do lead
                                leads = load_leads()
                                found_lead_updated = False

                                for lead in leads:
                                    if lead.get('telefone') == numero:
                                        current_status = lead.get('status_contato')
                                        # Se o lead estava como 'pendente', 'novo' ou 'contatado',
                                        # significa que ele respondeu.
                                        if current_status in ["pendente", "novo", "contatado", None]:
                                            lead['status_contato'] = "em_conversacao"
                                            found_lead_updated = True
                                            print(f"DEBUG: Status do lead {numero} atualizado para 'em_conversacao'.")
                                        # Se o lead já estava em "em_conversacao" ou outro status posterior,
                                        # não fazemos nada aqui, pois a conversa já está ativa.
                                        break # Encontrou o lead, pode sair do loop

                                if found_lead_updated:
                                    save_leads(leads) # Salva a lista de leads atualizada
                                # ===> FIM DAS NOVAS LINHAS <===
                            else:
                                print(f"Alerta: Mensagem do webhook sem número ou texto. Tipo: {tipo_mensagem}. Dados: {mensagem}")

        return 'OK', 200
    return 'Method Not Allowed', 405

@app.route('/api/whatsapp_templates', methods=['GET'])
@login_required
def get_whatsapp_templates():
    # Use WHATSAPP_BUSINESS_ACCOUNT_ID para buscar templates
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates" #
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lança exceção para erros HTTP
        templates_data = response.json()

        approved_templates = []
        for template in templates_data.get('data', []):
            if template.get('status') == 'APPROVED' and template.get('category') in ['UTILITY', 'MARKETING']:
                approved_templates.append({
                    "name": template.get('name'),
                    "language": template.get('language'),
                    "category": template.get('category'),
                    # Se precisar de informações sobre os parâmetros do template, adicione aqui
                    # "components": template.get('components', [])
                })
        return jsonify(approved_templates), 200

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar templates do WhatsApp: {e}")
        return jsonify({"erro": f"Erro ao buscar modelos de template: {str(e)}"}), 500
    except Exception as e:
        print(f"Erro inesperado ao processar templates: {e}")
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@app.route('/api/enviar-template', methods=['POST'])
@login_required
def enviar_template_api():
    data = request.json
    numero_original = data.get('numero')
    nome_lead = data.get('nome_lead', '') # Nome do lead será o valor da variável {{1}}
    template_name = data.get('template_name')

    if not numero_original or not template_name:
        return jsonify({"erro": "Número e nome do template são obrigatórios."}), 400

    numero = normalize_phone_number(numero_original) # Certifique-se que normalize_phone_number retorna no formato E.164 (+55DD9XXXXXXXX)
    if not numero:
        return jsonify({"erro": "Número é inválido após normalização"}), 400

    # Use PHONE_NUMBER_ID para enviar mensagens
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages" #
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Payload para template com uma variável no corpo, conforme seu template na imagem_bb1dbd.png
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": "pt_BR"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": nome_lead # Preenche a variável {{1}} do template
                        }
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        if response.ok:
            mensagem_para_historico = f"Template '{template_name}' enviado para {nome_lead}."
            print(f"DEBUG_CALL: Chamando salvar_mensagem para a mensagem de template enviada de '{numero}'.")
            salvar_mensagem(numero, mensagem_para_historico, int(time.time()), remetente='sent')

            leads = load_leads()
            found_lead_updated = False
            for lead in leads:
                if lead.get('telefone') == numero:
                    if lead.get('status_contato') in ["pendente", "novo", None]:
                        lead['status_contato'] = "contatado"
                        found_lead_updated = True
                        print(f"DEBUG: Status do lead {numero} atualizado para 'contatado' (via template).")
                    break
            if found_lead_updated:
                save_leads(leads)

            remove_pending_lead_by_phone(numero)
            return jsonify(response_data), 200
        else:
            print(f"Erro da API do WhatsApp ao enviar template: {response_data}")
            error_message = response_data.get('error', {}).get('message', 'Erro desconhecido da API do WhatsApp.')
            return jsonify({"erro": error_message}), response.status_code
    except Exception as e:
        print(f"Erro na requisição para a API do WhatsApp (template): {str(e)}")
        return jsonify({"erro": f"Falha interna ao enviar template: {str(e)}"}), 500

## **NOVO ENDPOINT PARA MENSAGENS PERSONALIZADAS (TEXTO LIVRE)**

## **NOVO ENDPOINT PARA MENSAGENS PERSONALIZADAS (TEXTO LIVRE)**

@app.route('/api/enviar-mensagem-personalizada', methods=['POST'])
@login_required
def enviar_mensagem_personalizada_api():
    data = request.json
    numero_cliente_original = data.get('numero') # Recebe o número do frontend
    mensagem_texto = data.get('mensagem')

    # <<<< IMPORTANTE: NORMALIZAR O NÚMERO ANTES DE USÁ-LO >>>>
    numero_cliente_normalizado = normalize_phone_number(numero_cliente_original)

    if not numero_cliente_normalizado:
        return jsonify({"erro": "Número do cliente inválido ou não normalizável."}), 400

    if not mensagem_texto:
        return jsonify({"erro": "Mensagem vazia."}), 400

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_cliente_normalizado,
        "type": "text",
        "text": {
            "body": mensagem_texto
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        if response.ok:
            # Salvar a mensagem enviada no histórico local
            print(f"DEBUG_CALL: Chamando salvar_mensagem para a mensagem enviada de '{numero_cliente_normalizado}'.")
            salvar_mensagem(numero_cliente_normalizado, mensagem_texto, int(time.time()), remetente='sent')

            # Atualiza o status do lead para 'em_conversacao'
            # E REMOVE DOS PENDENTES SE ESTIVER LÁ
            leads = load_leads()
            pending_leads_updated_in_memory = False
            for lead in leads:
                if normalize_phone_number(lead.get('telefone')) == numero_cliente_normalizado: # <<<< NORMALIZAÇÃO AQUI
                    if lead.get('status_contato') not in ["em_conversacao"]:
                        lead['status_contato'] = "em_conversacao"
                        pending_leads_updated_in_memory = True # Indica que o lead foi atualizado em 'leads.json'
                        print(f"DEBUG: Status do lead {numero_cliente_normalizado} atualizado para 'em_conversacao' (via envio de mensagem personalizada).")
                    break
            if pending_leads_updated_in_memory:
                save_leads(leads)

            # <<<< ADICIONADO AQUI: REMOVER LEAD DOS PENDENTES APÓS ENVIO DE MENSAGEM PERSONALIZADA >>>>
            # Isso é crucial para que ele desapareça da lista de pendentes.
            remove_pending_lead_by_phone(numero_cliente_normalizado) # <<<< Usa o número normalizado

            return jsonify(response_data), 200
        else:
            print(f"Erro da API do WhatsApp ao enviar mensagem: {response_data}")
            error_message = response_data.get('error', {}).get('message', 'Erro desconhecido da API do WhatsApp.')
            return jsonify({"erro": error_message}), response.status_code
    except Exception as e:
        print(f"Erro na requisição para a API do WhatsApp (mensagem): {str(e)}")
        return jsonify({"erro": f"Falha interna ao enviar mensagem: {str(e)}"}), 500


@app.route('/api/clientes-mensagens', methods=['GET'])
@login_required
def listar_clientes_com_mensagens():
    if not os.path.exists(MESSAGES_DIR):
        return jsonify([])

    numeros_com_mensagens = [
        f.replace('.json', '')
        for f in os.listdir(MESSAGES_DIR)
        if f.endswith('.json')
    ]
    print(f"DEBUG: Clientes com mensagens encontrados: {numeros_com_mensagens}")
    return jsonify(numeros_com_mensagens)


@app.route('/api/numeros', methods=['GET'])
@login_required
def listar_numeros_api():
    if not os.path.exists(MESSAGES_DIR):
        return jsonify([])

    numeros = [
        f.replace('.json', '')
        for f in os.listdir(MESSAGES_DIR)
        if f.endswith('.json')
    ]
    print(f"DEBUG: Números para atualização periódica: {numeros}")
    return jsonify(numeros)


# app.py

@app.route('/api/excluir-contato', methods=['POST'])
@login_required
def excluir_contato_api():
    data = request.json
    numero_original = data.get('numero')

    print(f"DEBUG: Requisição para excluir contato recebida. Número original: {numero_original}")

    numero = normalize_phone_number(numero_original)
    if not numero:
        print(f"DEBUG: Número original '{numero_original}' resultou em normalização inválida.")
        return jsonify({"erro": "Número inválido ou não normalizável para exclusão."}), 400

    print(f"DEBUG: Número normalizado para exclusão: {numero}")

    path = os.path.join(MESSAGES_DIR, f"{numero}.json")
    print(f"DEBUG: Tentando excluir arquivo em: {path}")

    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"DEBUG: Arquivo de chat {path} excluído com sucesso.")

            # ... (o restante do seu código para remover da lista geral de leads) ...

            return jsonify({"mensagem": f"Contato {numero} e histórico de mensagens excluídos."}), 200
        except Exception as e:
            print(f"ERROR: Erro ao excluir arquivo de chat {path}: {e}")
            return jsonify({"erro": f"Falha ao excluir o contato: {str(e)}"}), 500
    else:
        print(f"DEBUG: Arquivo de chat {path} NÃO encontrado. Retornando 404.")
        return jsonify({"mensagem": f"Contato {numero} ou histórico de mensagens não encontrado."}), 404

# Certifique-se de ter essa linha em algum lugar no seu app.py para ver o MESSAGES_DIR na inicialização
print(f"DEBUG: MESSAGES_DIR configurado como: {MESSAGES_DIR}")


### **Novas Rotas de API para Leads Salvos e Pendentes**

@app.route('/api/leads_salvos', methods=['GET'])
@login_required
def get_saved_leads_api():
    """Retorna todos os leads salvos (geral)."""
    leads = load_leads()
    return jsonify(leads)


@app.route('/api/pending_leads', methods=['GET'])
@login_required
def get_pending_leads_api():
    """Retorna todos os leads na fila de espera para contato."""
    pending_leads = load_pending_leads()
    return jsonify(pending_leads)


@app.route('/api/remove_pending_lead', methods=['POST'])
@login_required
def remove_pending_lead_api():
    """Remove um lead específico da fila de espera."""
    data = request.json
    numero_telefone = data.get('telefone')  # Espera o telefone do lead para identificar

    if not numero_telefone:
        return jsonify({"erro": "Telefone do lead não fornecido"}), 400

    if remove_pending_lead_by_phone(numero_telefone):
        return jsonify({"mensagem": "Lead removido da fila de pendentes com sucesso."})
    else:
        return jsonify({"erro": "Lead não encontrado na fila de pendentes ou telefone incorreto."}), 404

if __name__ == "__main__":
    # Garante que o arquivo de usuários existe e tem um usuário padrão
    load_users()
    # Chama a função para garantir que todos os leads existentes tenham um status
    migrate_leads_status()
    app.run(host="0.0.0.0", port=5000, debug=True)