from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Google Books API (gratuita, sin autenticación)
GOOGLE_BOOKS_API = 'https://www.googleapis.com/books/v1/volumes'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'

@app.route('/')
def index():
    return render_template('libros.html')

@app.route('/api/libros/buscar')
def buscar_libros():
    query = request.args.get('q', '')
    categoria = request.args.get('categoria', '')
    max_results = request.args.get('max', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Consulta requerida'}), 400
    
    # Construir query
    search_query = query
    if categoria:
        search_query += f'+subject:{categoria}'
    
    params = {
        'q': search_query,
        'maxResults': min(max_results, 40),
        'printType': 'books',
        'langRestrict': 'es'
    }
    
    try:
        response = requests.get(GOOGLE_BOOKS_API, params=params)
        data = response.json()
        
        if 'items' not in data:
            return jsonify([])
        
        libros = []
        for item in data['items']:
            info = item.get('volumeInfo', {})
            venta = item.get('saleInfo', {})
            
            libro = {
                'id': item['id'],
                'titulo': info.get('title', 'Sin título'),
                'autores': info.get('authors', []),
                'descripcion': info.get('description', '')[:300] + '...' if info.get('description') else '',
                'editorial': info.get('publisher', ''),
                'fecha_publicacion': info.get('publishedDate', ''),
                'paginas': info.get('pageCount', 0),
                'categorias': info.get('categories', []),
                'imagen': info.get('imageLinks', {}).get('thumbnail', ''),
                'preview_link': info.get('previewLink', ''),
                'rating': info.get('averageRating', 0),
                'precio': venta.get('listPrice', {}).get('amount', 0),
                'moneda': venta.get('listPrice', {}).get('currencyCode', ''),
                'disponible': venta.get('saleability') == 'FOR_SALE'
            }
            
            libros.append(libro)
        
        return jsonify(libros)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/libros/<book_id>')
def detalle_libro(book_id):
    try:
        response = requests.get(f'{GOOGLE_BOOKS_API}/{book_id}')
        data = response.json()
        
        info = data.get('volumeInfo', {})
        venta = data.get('saleInfo', {})
        
        detalle = {
            'titulo': info.get('title'),
            'subtitulo': info.get('subtitle'),
            'autores': info.get('authors', []),
            'descripcion': info.get('description', ''),
            'editorial': info.get('publisher'),
            'fecha_publicacion': info.get('publishedDate'),
            'paginas': info.get('pageCount'),
            'categorias': info.get('categories', []),
            'imagen_grande': info.get('imageLinks', {}).get('large') or 
                             info.get('imageLinks', {}).get('thumbnail'),
            'idioma': info.get('language'),
            'preview_link': info.get('previewLink'),
            'rating': info.get('averageRating'),
            'ratings_count': info.get('ratingsCount'),
            'precio': venta.get('listPrice', {}).get('amount'),
            'moneda': venta.get('listPrice', {}).get('currencyCode'),
            'comprable': venta.get('saleability') == 'FOR_SALE',
            'link_compra': venta.get('buyLink')
        }
        
        return jsonify(detalle)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/libros/categorias')
def categorias_populares():
    categorias = [
        'Fiction', 'Science', 'History', 'Biography',
        'Technology', 'Business', 'Self-Help', 'Poetry',
        'Mystery', 'Romance', 'Fantasy', 'Science Fiction',
        'Programming', 'Education', 'Health', 'Art'
    ]
    return jsonify(categorias)

if __name__ == '__main__':
    print("📚 Buscador de Libros - Google Books API")
    app.run(debug=True)