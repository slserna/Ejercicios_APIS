from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'tu_secret_key_super_secreta_aqui'  # Cambiar por una clave secreta

# Spotify API Credentials
CLIENT_ID = '0a4ffc8bb39d46ad8695bc6fe97c6'
CLIENT_SECRET = 'a0900a1068b04577b6700909d5d5fc3a'

# URLs de Spotify
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_URL = 'https://api.spotify.com/v1'

def get_access_token():
    """
    Obtener token de acceso de Spotify usando Client Credentials Flow.
    Este método es para búsquedas públicas sin necesidad de login de usuario.
    """
    # Verificar si tenemos un token guardado y aún válido
    if 'access_token' in session and 'token_expiry' in session:
        if datetime.now() < datetime.fromisoformat(session['token_expiry']):
            return session['access_token']
    
    # Crear credenciales en base64
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    # Solicitar token
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}
    
    try:
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=10)
        
        if response.status_code != 200:
            print(f"Error al obtener token: {response.status_code}")
            print(response.json())
            return None
        
        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = token_data['expires_in']
        
        # Guardar en sesión
        session['access_token'] = access_token
        session['token_expiry'] = (datetime.now() + timedelta(seconds=expires_in - 60)).isoformat()
        
        return access_token
        
    except Exception as e:
        print(f"Error al obtener token: {e}")
        return None

@app.route('/')
def index():
    return render_template('spotify.html')

@app.route('/api/spotify/buscar')
def buscar_spotify():
    """Buscar canciones, artistas, álbumes o playlists"""
    query = request.args.get('q', '')
    tipo = request.args.get('tipo', 'track')  # track, artist, album, playlist
    limite = request.args.get('limite', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Consulta requerida'}), 400
    
    token = get_access_token()
    if not token:
        return jsonify({'error': 'Error al autenticar con Spotify'}), 500
    
    try:
        url = f'{SPOTIFY_API_URL}/search'
        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'q': query,
            'type': tipo,
            'limit': limite,
            'market': 'MX'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'error': f'Error de Spotify API: {response.status_code}'}), 500
        
        data = response.json()
        resultados = []
        
        # Procesar según el tipo
        if tipo == 'track':
            for track in data.get('tracks', {}).get('items', []):
                resultados.append({
                    'id': track['id'],
                    'nombre': track['name'],
                    'artistas': [a['name'] for a in track['artists']],
                    'artista_principal': track['artists'][0]['name'] if track['artists'] else '',
                    'album': track['album']['name'],
                    'imagen': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'duracion_ms': track['duration_ms'],
                    'duracion': f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
                    'preview_url': track['preview_url'],
                    'spotify_url': track['external_urls']['spotify'],
                    'popularidad': track['popularity'],
                    'explicito': track['explicit']
                })
        
        elif tipo == 'artist':
            for artist in data.get('artists', {}).get('items', []):
                resultados.append({
                    'id': artist['id'],
                    'nombre': artist['name'],
                    'generos': artist['genres'],
                    'popularidad': artist['popularity'],
                    'imagen': artist['images'][0]['url'] if artist['images'] else None,
                    'seguidores': artist['followers']['total'],
                    'spotify_url': artist['external_urls']['spotify']
                })
        
        elif tipo == 'album':
            for album in data.get('albums', {}).get('items', []):
                resultados.append({
                    'id': album['id'],
                    'nombre': album['name'],
                    'artistas': [a['name'] for a in album['artists']],
                    'fecha_lanzamiento': album['release_date'],
                    'total_tracks': album['total_tracks'],
                    'imagen': album['images'][0]['url'] if album['images'] else None,
                    'spotify_url': album['external_urls']['spotify'],
                    'tipo': album['album_type']
                })
        
        elif tipo == 'playlist':
            for playlist in data.get('playlists', {}).get('items', []):
                resultados.append({
                    'id': playlist['id'],
                    'nombre': playlist['name'],
                    'descripcion': playlist['description'],
                    'owner': playlist['owner']['display_name'],
                    'total_tracks': playlist['tracks']['total'],
                    'imagen': playlist['images'][0]['url'] if playlist['images'] else None,
                    'spotify_url': playlist['external_urls']['spotify'],
                    'publica': playlist['public']
                })
        
        return jsonify(resultados)
        
    except Exception as e:
        print(f"Error en buscar_spotify: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/artista/<artist_id>')
def info_artista(artist_id):
    """Obtener información completa de un artista"""
    token = get_access_token()
    if not token:
        return jsonify({'error': 'Error al autenticar'}), 500
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # Información del artista
        artist_response = requests.get(
            f'{SPOTIFY_API_URL}/artists/{artist_id}',
            headers=headers,
            timeout=10
        )
        artist = artist_response.json()
        
        # Top tracks del artista
        top_response = requests.get(
            f'{SPOTIFY_API_URL}/artists/{artist_id}/top-tracks',
            headers=headers,
            params={'market': 'MX'},
            timeout=10
        )
        top_tracks = top_response.json().get('tracks', [])
        
        # Álbumes del artista
        albums_response = requests.get(
            f'{SPOTIFY_API_URL}/artists/{artist_id}/albums',
            headers=headers,
            params={'limit': 10, 'market': 'MX'},
            timeout=10
        )
        albums = albums_response.json().get('items', [])
        
        # Artistas relacionados
        related_response = requests.get(
            f'{SPOTIFY_API_URL}/artists/{artist_id}/related-artists',
            headers=headers,
            timeout=10
        )
        related = related_response.json().get('artists', [])
        
        resultado = {
            'id': artist['id'],
            'nombre': artist['name'],
            'generos': artist['genres'],
            'popularidad': artist['popularity'],
            'seguidores': artist['followers']['total'],
            'imagen': artist['images'][0]['url'] if artist['images'] else None,
            'spotify_url': artist['external_urls']['spotify'],
            'top_canciones': [
                {
                    'id': track['id'],
                    'nombre': track['name'],
                    'album': track['album']['name'],
                    'preview': track['preview_url'],
                    'imagen': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'duracion': f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
                    'spotify_url': track['external_urls']['spotify']
                }
                for track in top_tracks[:10]
            ],
            'albums': [
                {
                    'id': album['id'],
                    'nombre': album['name'],
                    'fecha': album['release_date'],
                    'imagen': album['images'][0]['url'] if album['images'] else None,
                    'total_tracks': album['total_tracks'],
                    'tipo': album['album_type']
                }
                for album in albums
            ],
            'artistas_relacionados': [
                {
                    'id': rel['id'],
                    'nombre': rel['name'],
                    'imagen': rel['images'][0]['url'] if rel['images'] else None,
                    'popularidad': rel['popularity']
                }
                for rel in related[:6]
            ]
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Error en info_artista: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/album/<album_id>')
def info_album(album_id):
    """Obtener información de un álbum"""
    token = get_access_token()
    if not token:
        return jsonify({'error': 'Error al autenticar'}), 500
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            f'{SPOTIFY_API_URL}/albums/{album_id}',
            headers=headers,
            params={'market': 'MX'},
            timeout=10
        )
        album = response.json()
        
        resultado = {
            'id': album['id'],
            'nombre': album['name'],
            'artistas': [a['name'] for a in album['artists']],
            'fecha_lanzamiento': album['release_date'],
            'total_tracks': album['total_tracks'],
            'imagen': album['images'][0]['url'] if album['images'] else None,
            'generos': album['genres'],
            'sello': album['label'],
            'popularidad': album['popularity'],
            'spotify_url': album['external_urls']['spotify'],
            'tracks': [
                {
                    'numero': track['track_number'],
                    'nombre': track['name'],
                    'duracion': f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
                    'preview': track['preview_url'],
                    'spotify_url': track['external_urls']['spotify']
                }
                for track in album['tracks']['items']
            ]
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Error en info_album: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/recomendaciones')
def obtener_recomendaciones():
    """Obtener recomendaciones basadas en géneros"""
    generos = request.args.get('generos', 'pop,rock')
    limite = request.args.get('limite', 20, type=int)
    
    token = get_access_token()
    if not token:
        return jsonify({'error': 'Error al autenticar'}), 500
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            f'{SPOTIFY_API_URL}/recommendations',
            headers=headers,
            params={
                'seed_genres': generos,
                'limit': limite,
                'market': 'MX'
            },
            timeout=10
        )
        data = response.json()
        
        recomendaciones = [
            {
                'id': track['id'],
                'nombre': track['name'],
                'artistas': [a['name'] for a in track['artists']],
                'album': track['album']['name'],
                'imagen': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'preview_url': track['preview_url'],
                'spotify_url': track['external_urls']['spotify']
            }
            for track in data.get('tracks', [])
        ]
        
        return jsonify(recomendaciones)
        
    except Exception as e:
        print(f"Error en recomendaciones: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/generos')
def obtener_generos():
    """Obtener lista de géneros disponibles"""
    token = get_access_token()
    if not token:
        return jsonify({'error': 'Error al autenticar'}), 500
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            f'{SPOTIFY_API_URL}/recommendations/available-genre-seeds',
            headers=headers,
            timeout=10
        )
        data = response.json()
        
        return jsonify(data.get('genres', []))
        
    except Exception as e:
        print(f"Error en obtener_generos: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🎵 Buscador de Música - Spotify Web API")
    print("=" * 60)
    
    if CLIENT_ID == 'TU_CLIENT_ID_AQUI':
        print("⚠️  ADVERTENCIA: Credenciales no configuradas")
        print("   Obtén tus credenciales en:")
        print("   https://developer.spotify.com/dashboard")
    else:
        print(f"✅ Client ID configurado: {CLIENT_ID[:20]}...")
    
    print("🌐 Servidor corriendo en: http://127.0.0.1:5000")
    print("=" * 60)
    
    app.run(debug=True)