from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text

app = Flask(__name__)

# ---------------------------------------------------------
# 🔌 Conexión a SQL Server (SQLAlchemy + pytds)
# ---------------------------------------------------------
def conectar_bd():
    try:
        engine = create_engine(
            "mssql+pytds://sa:Spill$184@200.91.92.132:9933/CODEAS"
        )
        return engine
    except Exception as e:
        print(f"❌ Error al conectar a SQL Server: {e}")
        return None


@app.route('/')
def index():
    return render_template('index.html')


# ---------------------------------------------------------
# 🔍 VALIDAR SI EL EMPLEADO ES SOCIO
# ---------------------------------------------------------
@app.route('/validar_socio', methods=['POST'])
def validar_socio():
    try:
        codigo_empleado = request.form['codigo_empleado']

        engine = conectar_bd()
        if engine is None:
            return jsonify({
                'success': False,
                'message': 'Error al conectar con la base de datos'
            })

        query = text("""
            SELECT CondAsoc 
            FROM dbo.ASOCIADOS_LINEA 
            WHERE CodAsoc = :codigo
        """)

        with engine.connect() as conn:
            result = conn.execute(query, {"codigo": codigo_empleado}).fetchone()

        if not result:
            return jsonify({
                'success': True,
                'es_socio': True,
                'message': 'Código válido. Complete los datos.'
            })

        cond_asoc = (result[0] or "").strip().upper()

        if cond_asoc == "ACTIVO":
            return jsonify({
                'success': False,
                'es_socio': False,
                'activo': True,
                'message': 'El socio está ACTIVO y no puede registrarse.'
            })
        else:
            return jsonify({
                'success': True,
                'es_socio': True,
                'activo': False,
                'message': 'Código válido. Complete los datos.'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al validar: {str(e)}'
        })


# ---------------------------------------------------------
# 💾 GUARDAR EMPLEADO
# ---------------------------------------------------------
@app.route('/guardar_empleado', methods=['POST'])
def guardar_empleado():
    try:
        codigo_empleado = request.form['codigo_empleado']
        nombre_completo = request.form['nombre_completo'].strip()
        numero_cedula = request.form['numero_cedula'].strip()
        cuenta_iban = request.form['cuenta_iban'].strip().upper()

        # Validación IBAN
        if not cuenta_iban.startswith('CR') or len(cuenta_iban) != 22:
            return jsonify({
                'success': False,
                'message': 'El IBAN debe iniciar con CR y tener 22 caracteres.'
            })

        engine = conectar_bd()
        if engine is None:
            return jsonify({
                'success': False,
                'message': 'Error al conectar con la base de datos'
            })

        # Verificar si ya existe
        query_check = text("""
            SELECT COUNT(*) 
            FROM dbo.PREMIOS_DATOS 
            WHERE CodigoEmpleado = :codigo
        """)

        insert_query = text("""
            INSERT INTO dbo.PREMIOS_DATOS (CodigoEmpleado, Nombre, CuentaBancaria, Cedula)
            VALUES (:codigo, :nombre, :iban, :cedula)
        """)

        with engine.begin() as conn:
            existe = conn.execute(query_check, {"codigo": codigo_empleado}).scalar()

            if existe:
                return jsonify({
                    'success': False,
                    'message': 'Este empleado ya está registrado.'
                })

            conn.execute(insert_query, {
                "codigo": codigo_empleado,
                "nombre": nombre_completo,
                "iban": cuenta_iban,
                "cedula": numero_cedula
            })

        return jsonify({
            'success': True,
            'message': 'Empleado registrado exitosamente.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al guardar: {str(e)}'
        })


# ---------------------------------------------------------
# 🚀 EJECUTAR LOCALMENTE
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)



