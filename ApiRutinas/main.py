from flask import Flask, render_template, request, jsonify
import json
import os
from pathlib import Path
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Ruta al archivo de datos
DATA_FILE = Path('rutinas.json')

# Verificar y crear el archivo si no existe
def init_data():
    # Crear directorio de uploads si no existe
    uploads_dir = Path('static/uploads/exercises')
    uploads_dir.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        initial_data = {
            "rutinas_por_musculo": []
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)

# Cargar datos desde el archivo
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'Error al cargar datos: {e}')
        return None

# Guardar datos en el archivo
def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f'Error al guardar datos: {e}')
        return False

# Validar estructura de datos
def validate_rutina(rutina):
    if not isinstance(rutina, dict):
        return False
    if 'musculo' not in rutina or 'ejercicios' not in rutina:
        return False
    if not isinstance(rutina['ejercicios'], list):
        return False
    return True

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint para obtener todas las rutinas
@app.route('/api/rutinas', methods=['GET'])
def get_rutinas():
    try:
        data = load_data()
        if data:
            return jsonify(data)
        return jsonify({'error': 'No se pudo cargar los datos'}), 500
    except Exception as e:
        return jsonify({'error': f'Error al cargar las rutinas: {str(e)}'}), 500



# Endpoint para actualizar una rutina
@app.route('/api/rutinas/<int:index>', methods=['PUT'])
def update_rutina(index):
    try:
        data = request.json
        if not validate_rutina(data):
            return jsonify({'error': 'Estructura de datos inválida'}), 400

        current_data = load_data()
        if not current_data:
            return jsonify({'error': 'No se pudo cargar los datos existentes'}), 500

        if 0 <= index < len(current_data['rutinas_por_musculo']):
            current_data['rutinas_por_musculo'][index] = data
            
            if save_data(current_data):
                return jsonify({'message': 'Rutina actualizada exitosamente'})
            return jsonify({'error': 'No se pudo guardar los cambios'}), 500
        return jsonify({'error': 'Índice de rutina no encontrado'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Datos no válidos JSON'}), 400
    except Exception as e:
        return jsonify({'error': f'Error al actualizar la rutina: {str(e)}'}), 500

# Endpoint para eliminar una rutina
@app.route('/api/rutinas/<int:index>', methods=['DELETE'])
def delete_rutina(index):
    try:
        current_data = load_data()
        if not current_data:
            return jsonify({'error': 'No se pudo cargar los datos existentes'}), 500

        if 0 <= index < len(current_data['rutinas_por_musculo']):
            del current_data['rutinas_por_musculo'][index]
            
            if save_data(current_data):
                return jsonify({'message': 'Rutina eliminada exitosamente'})
            return jsonify({'error': 'No se pudo guardar los cambios'}), 500
        return jsonify({'error': 'Índice de rutina no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': f'Error al eliminar la rutina: {str(e)}'}), 500

# Endpoint para agregar un ejercicio a un músculo existente
@app.route('/api/rutinas/<int:rutina_index>/ejercicios', methods=['POST'])
def add_ejercicio(rutina_index):
    try:
        current_data = load_data()
        if not current_data:
            return jsonify({'error': 'No se pudo cargar los datos existentes'}), 500

        if 0 <= rutina_index < len(current_data['rutinas_por_musculo']):
            # Manejar la imagen subida (si existe)
            imagen = request.files.get('imagen')
            ruta_imagen = None
            
            if imagen:
                # Guardar la nueva imagen
                filename = secure_filename(imagen.filename)
                ruta_imagen = os.path.join('static', 'uploads', 'exercises', filename)
                imagen.save(ruta_imagen)
                ruta_imagen = f'/uploads/exercises/{filename}'
            
            # Obtener los datos del formulario
            ejercicio = {
                'nombre': request.form.get('nombre', ''),
                'series': int(request.form.get('series', 0)),
                'repeticiones': request.form.get('repeticiones', ''),
                'variantes': request.form.get('variantes', ''),
                'imagen': ruta_imagen
            }
            
            # Validar campos requeridos
            if not ejercicio['nombre']:
                return jsonify({'error': 'Nombre del ejercicio es requerido'}), 400
            
            if ejercicio['series'] < 1:
                return jsonify({'error': 'Número de series debe ser mayor a 0'}), 400
            
            # Agregar el ejercicio
            current_data['rutinas_por_musculo'][rutina_index]['ejercicios'].append(ejercicio)
            
            if save_data(current_data):
                return jsonify({'message': 'Ejercicio agregado exitosamente'}), 201
            return jsonify({'error': 'No se pudo guardar los cambios'}), 500
        return jsonify({'error': 'Índice de rutina no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': f'Error al agregar el ejercicio: {str(e)}'}), 500

# Endpoint para editar un ejercicio
@app.route('/api/rutinas/<int:rutina_index>/ejercicios/<int:ejercicio_index>', methods=['PUT'])
def edit_ejercicio(rutina_index, ejercicio_index):
    try:
        current_data = load_data()
        
        if rutina_index < 0 or rutina_index >= len(current_data['rutinas_por_musculo']):
            return jsonify({'error': 'Rutina no encontrada'}), 404
        
        if ejercicio_index < 0 or ejercicio_index >= len(current_data['rutinas_por_musculo'][rutina_index]['ejercicios']):
            return jsonify({'error': 'Ejercicio no encontrado'}), 404

        # Manejar la imagen subida (si existe)
        imagen = request.files.get('imagen')
        ruta_imagen = None
        
        if imagen:
            # Guardar la nueva imagen
            filename = secure_filename(imagen.filename)
            # Crear la ruta completa para guardar la imagen
            ruta_imagen = os.path.join('static', 'images', 'uploads', 'newexercises', filename)
            # Crear la ruta relativa que se guardará en el JSON
            ruta_imagen_rel = f'/static/images/uploads/newexercises/{filename}'
            
            # Asegurarse de que el directorio existe
            os.makedirs(os.path.dirname(ruta_imagen), exist_ok=True)
            imagen.save(ruta_imagen)
            ruta_imagen = ruta_imagen_rel
        
        # Obtener los datos del formulario
        ejercicio = {
            'nombre': request.form.get('nombre', ''),
            'series': int(request.form.get('series', 0)),
            'repeticiones': request.form.get('repeticiones', ''),
            'variantes': request.form.get('variantes', ''),
            'imagen': ruta_imagen if ruta_imagen else current_data['rutinas_por_musculo'][rutina_index]['ejercicios'][ejercicio_index].get('imagen')
        }
        
        current_data['rutinas_por_musculo'][rutina_index]['ejercicios'][ejercicio_index] = ejercicio
        
        if save_data(current_data):
            return jsonify({'message': 'Ejercicio actualizado exitosamente'}), 200
        return jsonify({'error': 'No se pudo guardar los cambios'}), 500
    except Exception as e:
        return jsonify({'error': f'Error al actualizar el ejercicio: {str(e)}'}), 500

# Endpoint para obtener una rutina específica
@app.route('/api/rutinas/<int:rutina_index>', methods=['GET'])
def get_rutina(rutina_index):
    try:
        current_data = load_data()
        if not current_data:
            return jsonify({'error': 'No se pudo cargar los datos existentes'}), 500

        if 0 <= rutina_index < len(current_data['rutinas_por_musculo']):
            return jsonify(current_data['rutinas_por_musculo'][rutina_index])
        return jsonify({'error': 'Índice de rutina no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': f'Error al obtener la rutina: {str(e)}'}), 500

# Endpoint para eliminar un ejercicio
@app.route('/api/rutinas/<int:rutina_index>/ejercicios/<int:ejercicio_index>', methods=['DELETE'])
def delete_ejercicio(rutina_index, ejercicio_index):
    try:
        current_data = load_data()
        if not current_data:
            return jsonify({'error': 'No se pudo cargar los datos existentes'}), 500

        rutina = current_data['rutinas_por_musculo'][rutina_index]
        if 0 <= ejercicio_index < len(rutina['ejercicios']):
            del rutina['ejercicios'][ejercicio_index]
            
            if save_data(current_data):
                return jsonify({'message': 'Ejercicio eliminado exitosamente'})
            return jsonify({'error': 'No se pudo guardar los cambios'}), 500
        return jsonify({'error': 'Índice de ejercicio no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': f'Error al eliminar el ejercicio: {str(e)}'}), 500

if __name__ == '__main__':
    init_data()
    app.run(debug=True)

if __name__ == '__main__':
    init_data()
    app.run(debug=True)

# Endpoint para agregar una nueva rutina
@app.route('/api/rutinas', methods=['POST'])
def add_rutina():
    try:
        data = request.json
        if not validate_rutina(data):
            return jsonify({'error': 'Estructura de datos inválida'}), 400

        with open(DATA_FILE, 'r+', encoding='utf-8') as f:
            rutinas = json.load(f)
            rutinas['rutinas_por_musculo'].append(data)
            f.seek(0)
            json.dump(rutinas, f, ensure_ascii=False, indent=2)
            f.truncate()
        
        return jsonify({'message': 'Rutina agregada exitosamente'}), 201
    except json.JSONDecodeError:
        return jsonify({'error': 'Datos no válidos JSON'}), 400
    except Exception as e:
        return jsonify({'error': f'Error al agregar la rutina: {str(e)}'}), 500

# Endpoint para actualizar una rutina
@app.route('/api/rutinas/<int:index>', methods=['PUT'])
def update_rutina(index):
    try:
        data = request.json
        if not validate_rutina(data):
            return jsonify({'error': 'Estructura de datos inválida'}), 400

        with open(DATA_FILE, 'r+', encoding='utf-8') as f:
            rutinas = json.load(f)
            if 0 <= index < len(rutinas['rutinas_por_musculo']):
                rutinas['rutinas_por_musculo'][index] = data
                f.seek(0)
                json.dump(rutinas, f, ensure_ascii=False, indent=2)
                f.truncate()
                return jsonify({'message': 'Rutina actualizada exitosamente'})
            return jsonify({'error': 'Índice de rutina no encontrado'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Datos no válidos JSON'}), 400
    except Exception as e:
        return jsonify({'error': f'Error al actualizar la rutina: {str(e)}'}), 500

# Endpoint para eliminar una rutina
@app.route('/api/rutinas/<int:index>', methods=['DELETE'])
def delete_rutina(index):
    try:
        with open(DATA_FILE, 'r+', encoding='utf-8') as f:
            rutinas = json.load(f)
            if 0 <= index < len(rutinas['rutinas_por_musculo']):
                del rutinas['rutinas_por_musculo'][index]
                f.seek(0)
                json.dump(rutinas, f, ensure_ascii=False, indent=2)
                f.truncate()
                return jsonify({'message': 'Rutina eliminada exitosamente'})
            return jsonify({'error': 'Índice de rutina no encontrado'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Datos no válidos JSON'}), 400
    except Exception as e:
        return jsonify({'error': f'Error al eliminar la rutina: {str(e)}'}), 500

if __name__ == '__main__':
    init_data()
    app.run(debug=True)