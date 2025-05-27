from flask import Flask, jsonify
from flask_cors import CORS
from maps_search import buscar_dados_cards_maps
from leads_controller import salvar_leads_em_csv

app = Flask(__name__)
CORS(app)  # <-- Isso libera o acesso externo via browser


@app.route("/")
def home():
    return "🚀 Backend Flask ativo!"


@app.route("/buscar-leads")
def buscar_leads():
    termo = "Clínica Odontológica em Goiânia"
    resultados = buscar_dados_cards_maps(termo, LIMITE_CARDS=5)

    salvar_leads_em_csv(resultados)
    return jsonify(resultados)


if __name__ == "__main__":
    app.run(debug=True)
