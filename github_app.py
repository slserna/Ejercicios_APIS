from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# GitHub API base URL
GITHUB_API = 'https://api.github.com'

@app.route('/')
def index():
    return render_template('github.html')

@app.route('/api/github/usuario/<username>')
def obtener_usuario_github(username):
    try:
        # Obtener información del usuario
        user_response = requests.get(f'{GITHUB_API}/users/{username}')
        
        if user_response.status_code == 404:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        usuario = user_response.json()
        
        # Obtener repositorios
        repos_response = requests.get(f'{GITHUB_API}/users/{username}/repos?per_page=100')
        repos = repos_response.json()
        
        # Calcular estadísticas
        total_stars = sum(repo['stargazers_count'] for repo in repos)
        total_forks = sum(repo['forks_count'] for repo in repos)
        
        # Contar lenguajes
        lenguajes = {}
        for repo in repos:
            lang = repo['language']
            if lang:
                lenguajes[lang] = lenguajes.get(lang, 0) + 1
        
        # Top 3 lenguajes
        top_lenguajes = sorted(lenguajes.items(), key=lambda x: x[1], reverse=True)[:3]
        
        resultado = {
            'nombre': usuario.get('name') or username,
            'username': usuario['login'],
            'bio': usuario.get('bio'),
            'avatar': usuario['avatar_url'],
            'repositorios': usuario['public_repos'],
            'seguidores': usuario['followers'],
            'siguiendo': usuario['following'],
            'ubicacion': usuario.get('location'),
            'empresa': usuario.get('company'),
            'blog': usuario.get('blog'),
            'twitter': usuario.get('twitter_username'),
            'creado': usuario['created_at'][:10],
            'total_stars': total_stars,
            'total_forks': total_forks,
            'lenguajes': dict(lenguajes),
            'top_lenguajes': [{'lenguaje': l[0], 'repos': l[1]} for l in top_lenguajes],
            'repos_destacados': [
                {
                    'nombre': repo['name'],
                    'descripcion': repo['description'],
                    'stars': repo['stargazers_count'],
                    'forks': repo['forks_count'],
                    'lenguaje': repo['language'],
                    'url': repo['html_url'],
                    'actualizado': repo['updated_at'][:10]
                }
                for repo in sorted(repos, key=lambda x: x['stargazers_count'], reverse=True)[:5]
            ]
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github/trending')
def repositorios_trending():
    """Buscar repos más populares de la última semana"""
    from datetime import datetime, timedelta
    
    fecha = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f'{GITHUB_API}/search/repositories'
    params = {
        'q': f'created:>{fecha}',
        'sort': 'stars',
        'order': 'desc',
        'per_page': 10
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        repos = [
            {
                'nombre': repo['full_name'],
                'descripcion': repo['description'],
                'stars': repo['stargazers_count'],
                'forks': repo['forks_count'],
                'lenguaje': repo['language'],
                'url': repo['html_url'],
                'propietario': repo['owner']['login'],
                'avatar': repo['owner']['avatar_url']
            }
            for repo in data.get('items', [])
        ]
        
        return jsonify(repos)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github/buscar/repos')
def buscar_repos():
    query = request.args.get('q', '')
    lenguaje = request.args.get('lenguaje', '')
    
    if not query:
        return jsonify({'error': 'Consulta requerida'}), 400
    
    # Construir query
    search_query = query
    if lenguaje:
        search_query += f' language:{lenguaje}'
    
    params = {
        'q': search_query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': 15
    }
    
    try:
        response = requests.get(f'{GITHUB_API}/search/repositories', params=params)
        data = response.json()
        
        repos = [
            {
                'nombre': repo['full_name'],
                'descripcion': repo['description'],
                'stars': repo['stargazers_count'],
                'lenguaje': repo['language'],
                'url': repo['html_url']
            }
            for repo in data.get('items', [])
        ]
        
        return jsonify(repos)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)