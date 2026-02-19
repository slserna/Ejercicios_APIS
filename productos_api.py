from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'productos.db'

def init_db():
    """Inicializar base de datos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            categoria TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insertar datos de ejemplo si la tabla está vacía
    cursor.execute('SELECT COUNT(*) FROM productos')
    if cursor.fetchone()[0] == 0:
        productos_ejemplo = [
            ('Laptop HP', 'Laptop HP 15.6" Core i5', 15999.99, 10, 'Electrónica'),
            ('Mouse Logitech', 'Mouse inalámbrico Logitech M185', 299.99, 50, 'Accesorios'),
            ('Teclado Mecánico', 'Teclado mecánico RGB', 1299.99, 25, 'Accesorios'),
            ('Monitor Samsung', 'Monitor 24" Full HD', 3499.99, 15, 'Electrónica'),
            ('Webcam', 'Webcam 1080p con micrófono', 899.99, 30, 'Accesorios')
        ]
        cursor.executemany('''
            INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
            VALUES (?, ?, ?, ?, ?)
        ''', productos_ejemplo)
    
    conn.commit()
    conn.close()

def get_db():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    return conn

@app.route('/')
def index():
    return render_template('productos.html')

# CREATE - Crear producto
@app.route('/api/productos', methods=['POST'])
def crear_producto():
    data = request.json
    
    # Validar datos requeridos
    if not data.get('nombre') or not data.get('precio'):
        return jsonify({'error': 'Nombre y precio son requeridos'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['nombre'],
            data.get('descripcion', ''),
            float(data['precio']),
            int(data.get('stock', 0)),
            data.get('categoria', 'General')
        ))
        
        conn.commit()
        producto_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'id': producto_id,
            'mensaje': 'Producto creado exitosamente'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# READ - Obtener todos los productos
@app.route('/api/productos', methods=['GET'])
def obtener_productos():
    # Parámetros de filtrado y ordenamiento
    categoria = request.args.get('categoria')
    orden = request.args.get('orden', 'nombre')
    orden_dir = request.args.get('dir', 'ASC')
    
    # Validar orden
    if orden not in ['nombre', 'precio', 'stock', 'fecha_creacion']:
        orden = 'nombre'
    
    if orden_dir.upper() not in ['ASC', 'DESC']:
        orden_dir = 'ASC'
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM productos'
        params = []
        
        if categoria:
            query += ' WHERE categoria = ?'
            params.append(categoria)
        
        query += f' ORDER BY {orden} {orden_dir}'
        
        cursor.execute(query, params)
        productos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(productos)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# READ - Obtener un producto específico
@app.route('/api/productos/<int:id>', methods=['GET'])
def obtener_producto(id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM productos WHERE id = ?', (id,))
        producto = cursor.fetchone()
        conn.close()
        
        if producto is None:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        return jsonify(dict(producto))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# UPDATE - Actualizar producto
@app.route('/api/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    data = request.json
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute('SELECT * FROM productos WHERE id = ?', (id,))
        if cursor.fetchone() is None:
            conn.close()
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Actualizar
        cursor.execute('''
            UPDATE productos 
            SET nombre = ?, descripcion = ?, precio = ?, stock = ?, 
                categoria = ?, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('nombre'),
            data.get('descripcion'),
            float(data.get('precio')),
            int(data.get('stock')),
            data.get('categoria'),
            id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'mensaje': 'Producto actualizado exitosamente'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DELETE - Eliminar producto
@app.route('/api/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM productos WHERE id = ?', (id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'mensaje': 'Producto eliminado exitosamente'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ESTADÍSTICAS
@app.route('/api/productos/stats', methods=['GET'])
def estadisticas():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(precio) as precio_promedio,
                SUM(stock) as stock_total,
                MIN(precio) as precio_min,
                MAX(precio) as precio_max
            FROM productos
        ''')
        stats_generales = dict(cursor.fetchone())
        
        # Estadísticas por categoría
        cursor.execute('''
            SELECT 
                categoria,
                COUNT(*) as cantidad,
                AVG(precio) as precio_promedio,
                SUM(stock) as stock_total
            FROM productos
            GROUP BY categoria
        ''')
        stats_categoria = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'generales': stats_generales,
            'por_categoria': stats_categoria
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Obtener categorías únicas
@app.route('/api/categorias', methods=['GET'])
def obtener_categorias():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT categoria FROM productos ORDER BY categoria')
        categorias = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(categorias)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    print("✅ Base de datos inicializada")
    print("📊 Ejecutando API en http://127.0.0.1:5000")
    app.run(debug=True)