from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import os

app = Flask(__name__)

# Inicializar Firebase
if not firebase_admin._apps:
    # Reemplazar con tu archivo de credenciales
    if os.path.exists('firebase-credentials.json'):
        cred = credentials.Certificate('firebase-credentials.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://TU-PROYECTO.firebaseio.com'  # Reemplazar con tu URL
        })
    else:
        print("⚠️ No se encontró firebase-credentials.json")
        print("Crea un proyecto en Firebase y descarga las credenciales")

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/api/mensajes', methods=['GET'])
def obtener_mensajes():
    """Obtener los últimos mensajes"""
    try:
        ref = db.reference('mensajes')
        mensajes = ref.order_by_child('timestamp').limit_to_last(50).get()
        
        if mensajes:
            # Convertir a lista ordenada
            mensajes_lista = []
            for key, value in mensajes.items():
                value['id'] = key
                mensajes_lista.append(value)
            
            # Ordenar por timestamp
            mensajes_lista.sort(key=lambda x: x.get('timestamp', ''))
            return jsonify(mensajes_lista)
        
        return jsonify([])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mensajes', methods=['POST'])
def enviar_mensaje():
    """Enviar un nuevo mensaje"""
    data = request.json
    
    if not data.get('usuario') or not data.get('texto'):
        return jsonify({'error': 'Usuario y texto requeridos'}), 400
    
    try:
        ref = db.reference('mensajes')
        nuevo_mensaje = {
            'usuario': data['usuario'],
            'texto': data['texto'],
            'timestamp': datetime.now().isoformat(),
            'avatar': data.get('avatar', '👤')
        }
        
        # Guardar mensaje
        nueva_ref = ref.push(nuevo_mensaje)
        nuevo_mensaje['id'] = nueva_ref.key
        
        return jsonify(nuevo_mensaje), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mensajes/<mensaje_id>', methods=['DELETE'])
def eliminar_mensaje(mensaje_id):
    """Eliminar un mensaje"""
    try:
        ref = db.reference(f'mensajes/{mensaje_id}')
        ref.delete()
        return jsonify({'mensaje': 'Mensaje eliminado'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios/online', methods=['POST'])
def registrar_usuario_online():
    """Registrar usuario como online"""
    data = request.json
    usuario = data.get('usuario')
    
    if not usuario:
        return jsonify({'error': 'Usuario requerido'}), 400
    
    try:
        ref = db.reference(f'usuarios_online/{usuario}')
        ref.set({
            'ultima_actividad': datetime.now().isoformat(),
            'online': True
        })
        
        return jsonify({'mensaje': 'Usuario registrado'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios/online', methods=['GET'])
def obtener_usuarios_online():
    """Obtener lista de usuarios online"""
    try:
        ref = db.reference('usuarios_online')
        usuarios = ref.get()
        
        if usuarios:
            return jsonify(list(usuarios.keys()))
        
        return jsonify([])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🔥 Firebase Chat App")
    print("📝 Asegúrate de tener firebase-credentials.json configurado")
    app.run(debug=True)