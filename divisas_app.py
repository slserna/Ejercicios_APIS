from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# ExchangeRate-API (obtener en https://www.exchangerate-api.com/)
API_KEY = 'd1a3aea98c7c710f19221f87'
BASE_URL = 'https://v6.exchangerate-api.com/v6'

@app.route('/')
def index():
    return render_template('divisas.html')

@app.route('/api/divisas/tasas/<moneda_base>')
def obtener_tasas(moneda_base):
    """Obtener todas las tasas de cambio para una moneda base"""
    try:
        url = f'{BASE_URL}/{API_KEY}/latest/{moneda_base.upper()}'
        response = requests.get(url)
        data = response.json()
        
        if data['result'] != 'success':
            return jsonify({'error': 'Error al obtener tasas'}), 400
        
        return jsonify({
            'moneda_base': data['base_code'],
            'tasas': data['conversion_rates'],
            'ultima_actualizacion': data['time_last_update_utc']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/divisas/convertir')
def convertir():
    """Convertir entre dos monedas"""
    monto = request.args.get('monto', type=float)
    de = request.args.get('de', 'USD').upper()
    a = request.args.get('a', 'MXN').upper()
    
    if not monto:
        return jsonify({'error': 'Monto requerido'}), 400
    
    try:
        url = f'{BASE_URL}/{API_KEY}/pair/{de}/{a}/{monto}'
        response = requests.get(url)
        data = response.json()
        
        if data['result'] != 'success':
            return jsonify({'error': 'Error en conversión'}), 400
        
        return jsonify({
            'monto_original': monto,
            'moneda_origen': de,
            'moneda_destino': a,
            'monto_convertido': data['conversion_result'],
            'tasa_conversion': data['conversion_rate'],
            'ultima_actualizacion': data['time_last_update_utc']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/divisas/monedas')
def listar_monedas():
    """Lista de monedas más comunes"""
    monedas = {
        'USD': {'nombre': 'Dólar Estadounidense', 'simbolo': '$', 'bandera': '🇺🇸'},
        'EUR': {'nombre': 'Euro', 'simbolo': '€', 'bandera': '🇪🇺'},
        'GBP': {'nombre': 'Libra Esterlina', 'simbolo': '£', 'bandera': '🇬🇧'},
        'JPY': {'nombre': 'Yen Japonés', 'simbolo': '¥', 'bandera': '🇯🇵'},
        'MXN': {'nombre': 'Peso Mexicano', 'simbolo': '$', 'bandera': '🇲🇽'},
        'CAD': {'nombre': 'Dólar Canadiense', 'simbolo': '$', 'bandera': '🇨🇦'},
        'AUD': {'nombre': 'Dólar Australiano', 'simbolo': '$', 'bandera': '🇦🇺'},
        'CHF': {'nombre': 'Franco Suizo', 'simbolo': 'Fr', 'bandera': '🇨🇭'},
        'CNY': {'nombre': 'Yuan Chino', 'simbolo': '¥', 'bandera': '🇨🇳'},
        'BRL': {'nombre': 'Real Brasileño', 'simbolo': 'R$', 'bandera': '🇧🇷'},
        'ARS': {'nombre': 'Peso Argentino', 'simbolo': '$', 'bandera': '🇦🇷'},
        'COP': {'nombre': 'Peso Colombiano', 'simbolo': '$', 'bandera': '🇨🇴'},
        'CLP': {'nombre': 'Peso Chileno', 'simbolo': '$', 'bandera': '🇨🇱'}
    }
    return jsonify(monedas)

if __name__ == '__main__':
    print("💰 Conversor de Divisas")
    print("🔑 API Key:", API_KEY)
    app.run(debug=True)