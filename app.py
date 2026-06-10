from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import shodan
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__)
CORS(app)

# CONFIGURACIÓN (Pon tus llaves aquí si las tienes)
SHODAN_API_KEY = "TU_API_KEY_AQUI"
UPTIMEROBOT_API_KEY = "TU_API_KEY_AQUI"

# Base de datos temporal en memoria
cyber_data = {
    "threats": [],
    "news": [],
    "infrastructure": []
}

# --- RUTAS PARA VER LA WEB ---

@app.route('/')
def index():
    """Esta ruta carga tu archivo HTML automáticamente"""
    try:
        # Buscamos el archivo index.html en la misma carpeta
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "<h1>Error: No se encontró el archivo index.html</h1><p>Asegúrate de que el archivo HTML se llame 'index.html' y esté en la misma carpeta que este script.</p>"

# --- FUNCIONES DE MONITOREO ---

def check_shodan():
    print("Consultando Shodan...")
    if SHODAN_API_KEY == "TU_API_KEY_AQUI":
        return
    api = shodan.Shodan(SHODAN_API_KEY)
    targets = ["8.8.8.8", "1.1.1.1"] 
    results = []
    for ip in targets:
        try:
            host = api.host(ip)
            results.append({
                "ip": ip,
                "ports": host['ports'],
                "vulns": host.get('vulns', []),
                "org": host.get('org', 'Desconocido')
            })
        except Exception as e:
            print(f"Error en Shodan para {ip}: {e}")
    cyber_data["threats"] = results

def check_uptime():
    print("Consultando UptimeRobot...")
    if UPTIMEROBOT_API_KEY == "TU_API_KEY_AQUI":
        # Datos de prueba si no hay API Key para que no se vea vacío
        cyber_data["infrastructure"] = [
            {"friendly_name": "Banco Central de Prueba", "status": 2},
            {"friendly_name": "Agencia de Ciberdefensa", "status": 2}
        ]
        return
    url = "https://api.uptimerobot.com/v2/getMonitors"
    payload = f"api_key={UPTIMEROBOT_API_KEY}&format=json"
    headers = {'content-type': "application/x-www-form-urlencoded"}
    try:
        response = requests.post(url, data=payload, headers=headers)
        cyber_data["infrastructure"] = response.json().get("monitors", [])
    except Exception as e:
        print(f"Error en UptimeRobot: {e}")

def scrape_news():
    print("Scrapeando noticias de The Hacker News...")
    url = "https://thehackernews.com/"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = []
        # Buscamos los posts en la página
        for item in soup.find_all('div', class_='body-post', limit=5):
            title = item.find('h2', class_='home-title').text.strip()
            link = item.find('a')['href']
            articles.append({"title": title, "link": link})
        cyber_data["news"] = articles
        print(f"Éxito: {len(articles)} noticias encontradas.")
    except Exception as e:
        print(f"Error en Scraping: {e}")

# --- PLANIFICADOR ---
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_shodan, trigger="interval", hours=1)
scheduler.add_job(func=check_uptime, trigger="interval", minutes=30)
scheduler.add_job(func=scrape_news, trigger="interval", hours=1)
scheduler.start()

# --- API ENDPOINTS ---

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(cyber_data)

if __name__ == '__main__':
    # Ejecución inicial para tener datos de inmediato
    scrape_news()
    check_uptime()
    
    print("Servidor iniciado en http://127.0.0.1:5000")
    app.run(debug=True, port=5000)