from flask import Flask, render_template, request, jsonify
import pyodbc

app = Flask(__name__)

def conectar_bd():
    servidor = '200.91.92.132,9933'
    nombre_bd = 'CODEAS'
    nombre_usu = 'sa'
    password = 'Spill$184'
    try:
        conn = pyodbc.connect(
            'DRIVER={FreeTDS};'
            'SERVER=200.91.92.132;'
            'PORT=9933;'
            'DATABASE=CODEAS;'
            'UID=sa;'
            'PWD=Spill$184;'
            'TDS_VERSION=7.4;'
        )
        return conn
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validar_socio', methods=['POST'])
def validar_socio():
    try:
        codigo_empleado = request.form['codigo_empleado']
        
        conn = conectar_bd()
        if conn is None:
            return jsonify({
                'success': False, 
                'message': 'Error al conectar con la base de datos'
            })
        
        cursor = conn.cursor()
        
        # Verificar si es socio en ASOCIADOS_LINEA
        query_socio = """
            SELECT CondAsoc 
            FROM dbo.ASOCIADOS_LINEA 
            WHERE CodAsoc = ?
        """
        cursor.execute(query_socio, (codigo_empleado,))
        resultado_socio = cursor.fetchone()
        
        if not resultado_socio:
            # No existe en la vista, puede registrar
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'es_socio': True,
                'message': 'Código de empleado válido. Por favor complete los datos'
            })
        
        cond_asoc = resultado_socio[0].strip() if resultado_socio[0] else ''
        
        # Verificar si está activo
        if cond_asoc.upper() == 'ACTIVO':
            # Está activo, NO puede registrar
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'es_socio': False,
                'activo': True,
                'message': 'El socio está ACTIVO y no puede registrarse en el sistema de premios'
            })
        else:
            # Está inactivo, puede registrar
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'es_socio': True,
                'activo': False,
                'message': 'Código de empleado válido. Por favor complete los datos'
            })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error al validar: {str(e)}'
        })

@app.route('/guardar_empleado', methods=['POST'])
def guardar_empleado():
    try:
        codigo_empleado = request.form['codigo_empleado']
        nombre_completo = request.form['nombre_completo'].strip()
        numero_cedula = request.form['numero_cedula'].strip()
        cuenta_iban = request.form['cuenta_iban'].strip().upper()
        
        # Validar IBAN (22 dígitos incluyendo CR)
        if not cuenta_iban.startswith('CR') or len(cuenta_iban) != 22:
            return jsonify({
                'success': False, 
                'message': 'La cuenta IBAN debe tener 22 caracteres incluyendo CR'
            })
        
        conn = conectar_bd()
        if conn is None:
            return jsonify({
                'success': False, 
                'message': 'Error al conectar con la base de datos'
            })
        
        cursor = conn.cursor()
        
        # Verificar nuevamente si ya está registrado
        query_check = "SELECT COUNT(*) FROM dbo.PREMIOS_DATOS WHERE CodigoEmpleado = ?"
        cursor.execute(query_check, (codigo_empleado,))
        existe = cursor.fetchone()[0] > 0
        
        if existe:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Esta cuenta ya se encuentra registrada'
            })
        
        # Insertar datos
        query = """
            INSERT INTO dbo.PREMIOS_DATOS (CodigoEmpleado, Nombre, CuentaBancaria, Cedula)
            VALUES (?, ?, ?, ?)
        """
        cursor.execute(query, (codigo_empleado, nombre_completo, cuenta_iban, numero_cedula))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Empleado registrado exitosamente'
        })
        
    except pyodbc.IntegrityError:
        return jsonify({
            'success': False, 
            'message': 'El código de empleado ya existe en la base de datos'
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error al guardar: {str(e)}'
        })


