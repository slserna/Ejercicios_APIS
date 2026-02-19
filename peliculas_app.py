from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# TMDB API Key (obtener en https://www.themoviedb.org/settings/api)
TMDB_API_KEY = '81d96fa7d95e7a2a7ed46b32a7fb029a'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'

@app.route('/')
def index():
    return render_template('peliculas.html')

@app.route('/api/peliculas/buscar')
def buscar_peliculas():
    """Buscar películas por título"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return jsonify({'error': 'Consulta requerida'}), 400
    
    try:
        url = f'{TMDB_BASE_URL}/search/movie'
        params = {
            'api_key': TMDB_API_KEY,
            'query': query,
            'language': 'es-MX',
            'page': page,
            'include_adult': False
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'error': 'Error al buscar películas'}), 500
        
        data = response.json()
        
        peliculas = []
        for movie in data.get('results', []):
            peliculas.append({
                'id': movie['id'],
                'titulo': movie['title'],
                'titulo_original': movie['original_title'],
                'descripcion': movie['overview'],
                'poster': f"{TMDB_IMAGE_BASE}{movie['poster_path']}" if movie.get('poster_path') else None,
                'backdrop': f"https://image.tmdb.org/t/p/original{movie['backdrop_path']}" if movie.get('backdrop_path') else None,
                'fecha_estreno': movie.get('release_date', ''),
                'popularidad': movie.get('popularity', 0),
                'calificacion': movie.get('vote_average', 0),
                'votos': movie.get('vote_count', 0)
            })
        
        return jsonify({
            'peliculas': peliculas,
            'pagina': data['page'],
            'total_paginas': data['total_pages'],
            'total_resultados': data['total_results']
        })
        
    except Exception as e:
        print(f"Error en buscar_peliculas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/peliculas/<int:movie_id>')
def detalle_pelicula(movie_id):
    """Obtener detalles completos de una película"""
    try:
        # Información básica + créditos, videos y similares
        url = f'{TMDB_BASE_URL}/movie/{movie_id}'
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'es-MX',
            'append_to_response': 'credits,videos,similar,recommendations'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return jsonify({'error': 'Película no encontrada'}), 404
        
        if response.status_code != 200:
            return jsonify({'error': 'Error al obtener detalles'}), 500
        
        movie = response.json()
        
        # Procesar reparto
        cast = [
            {
                'nombre': actor['name'],
                'personaje': actor['character'],
                'foto': f"{TMDB_IMAGE_BASE}{actor['profile_path']}" if actor.get('profile_path') else None,
                'orden': actor.get('order', 999)
            }
            for actor in movie.get('credits', {}).get('cast', [])[:10]
        ]
        
        # Procesar crew (director, guionista, etc.)
        crew = movie.get('credits', {}).get('crew', [])
        director = next((c['name'] for c in crew if c['job'] == 'Director'), None)
        guionistas = [c['name'] for c in crew if c['job'] in ['Writer', 'Screenplay']][:3]
        
        # Procesar videos (trailers)
        videos = [
            {
                'nombre': video['name'],
                'tipo': video['type'],
                'sitio': video['site'],
                'key': video['key'],
                'url': f"https://www.youtube.com/watch?v={video['key']}" if video['site'] == 'YouTube' else None
            }
            for video in movie.get('videos', {}).get('results', [])
            if video['site'] == 'YouTube' and video['type'] in ['Trailer', 'Teaser']
        ]
        
        # Películas similares
        similares = [
            {
                'id': sim['id'],
                'titulo': sim['title'],
                'poster': f"{TMDB_IMAGE_BASE}{sim['poster_path']}" if sim.get('poster_path') else None,
                'calificacion': sim.get('vote_average', 0)
            }
            for sim in movie.get('similar', {}).get('results', [])[:6]
        ]
        
        # Recomendaciones
        recomendaciones = [
            {
                'id': rec['id'],
                'titulo': rec['title'],
                'poster': f"{TMDB_IMAGE_BASE}{rec['poster_path']}" if rec.get('poster_path') else None,
                'calificacion': rec.get('vote_average', 0)
            }
            for rec in movie.get('recommendations', {}).get('results', [])[:6]
        ]
        
        detalle = {
            'id': movie['id'],
            'titulo': movie['title'],
            'titulo_original': movie['original_title'],
            'descripcion': movie['overview'],
            'tagline': movie.get('tagline', ''),
            'poster': f"{TMDB_IMAGE_BASE}{movie['poster_path']}" if movie.get('poster_path') else None,
            'backdrop': f"https://image.tmdb.org/t/p/original{movie['backdrop_path']}" if movie.get('backdrop_path') else None,
            'fecha_estreno': movie.get('release_date', ''),
            'duracion': movie.get('runtime', 0),
            'presupuesto': movie.get('budget', 0),
            'ingresos': movie.get('revenue', 0),
            'calificacion': movie.get('vote_average', 0),
            'votos': movie.get('vote_count', 0),
            'popularidad': movie.get('popularity', 0),
            'generos': [g['name'] for g in movie.get('genres', [])],
            'productoras': [p['name'] for p in movie.get('production_companies', [])],
            'paises': [p['name'] for p in movie.get('production_countries', [])],
            'idiomas': [l['english_name'] for l in movie.get('spoken_languages', [])],
            'director': director,
            'guionistas': guionistas,
            'reparto': cast,
            'trailers': videos,
            'similares': similares,
            'recomendaciones': recomendaciones,
            'homepage': movie.get('homepage', ''),
            'imdb_id': movie.get('imdb_id', '')
        }
        
        return jsonify(detalle)
        
    except Exception as e:
        print(f"Error en detalle_pelicula: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/peliculas/populares')
def peliculas_populares():
    """Obtener películas populares"""
    page = request.args.get('page', 1, type=int)
    
    try:
        url = f'{TMDB_BASE_URL}/movie/popular'
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'es-MX',
            'page': page
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        peliculas = [
            {
                'id': movie['id'],
                'titulo': movie['title'],
                'poster': f"{TMDB_IMAGE_BASE}{movie['poster_path']}" if movie.get('poster_path') else None,
                'calificacion': movie.get('vote_average', 0),
                'fecha_estreno': movie.get('release_date', '')
            }
            for movie in data.get('results', [])
        ]
        
        return jsonify({
            'peliculas': peliculas,
            'pagina': data['page'],
            'total_paginas': data['total_pages']
        })
        
    except Exception as e:
        print(f"Error en peliculas_populares: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/peliculas/cartelera')
def peliculas_cartelera():
    """Obtener películas en cartelera"""
    try:
        url = f'{TMDB_BASE_URL}/movie/now_playing'
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'es-MX',
            'region': 'MX'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        peliculas = [
            {
                'id': movie['id'],
                'titulo': movie['title'],
                'poster': f"{TMDB_IMAGE_BASE}{movie['poster_path']}" if movie.get('poster_path') else None,
                'calificacion': movie.get('vote_average', 0)
            }
            for movie in data.get('results', [])[:10]
        ]
        
        return jsonify(peliculas)
        
    except Exception as e:
        print(f"Error en peliculas_cartelera: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/series/buscar')
def buscar_series():
    """Buscar series de TV"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Consulta requerida'}), 400
    
    try:
        url = f'{TMDB_BASE_URL}/search/tv'
        params = {
            'api_key': TMDB_API_KEY,
            'query': query,
            'language': 'es-MX'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        series = [
            {
                'id': show['id'],
                'nombre': show['name'],
                'descripcion': show.get('overview', ''),
                'poster': f"{TMDB_IMAGE_BASE}{show['poster_path']}" if show.get('poster_path') else None,
                'primera_fecha': show.get('first_air_date', ''),
                'calificacion': show.get('vote_average', 0)
            }
            for show in data.get('results', [])
        ]
        
        return jsonify(series)
        
    except Exception as e:
        print(f"Error en buscar_series: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generos/peliculas')
def generos_peliculas():
    """Obtener lista de géneros de películas"""
    try:
        url = f'{TMDB_BASE_URL}/genre/movie/list'
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'es-MX'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        return jsonify(data.get('genres', []))
        
    except Exception as e:
        print(f"Error en generos_peliculas: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🎬 Buscador de Películas - TMDB API")
    print("=" * 60)
    
    if TMDB_API_KEY == 'TU_API_KEY_AQUI':
        print("⚠️  ADVERTENCIA: API Key no configurada")
        print("   Obtén tu key en: https://www.themoviedb.org/settings/api")
    else:
        print(f"✅ API Key configurada: {TMDB_API_KEY[:10]}...")
    
    print("🌐 Servidor corriendo en: http://127.0.0.1:5000")
    print("=" * 60)
    
    app.run(debug=True)