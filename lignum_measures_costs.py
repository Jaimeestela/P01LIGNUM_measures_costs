import streamlit as st
import ezdxf
import pandas as pd
import tempfile
import os
import unicodedata
import re
from math import dist
from capas_medicion import capas_medicion

# Función de normalización de nombres
def normalizar_nombre(nombre):
    nombre = nombre.upper()
    nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('ASCII')
    nombre = re.sub(r'[^A-Z0-9 ]+', '', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    return nombre

# Mapeo de claves normalizadas
claves_normalizadas = {normalizar_nombre(k): k for k in capas_medicion}
capas_descartadas = set()

def calcular_area(puntos):
    if len(puntos) < 3:
        return 0.0
    n = len(puntos)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += puntos[i][0] * puntos[j][1]
        area -= puntos[j][0] * puntos[i][1]
    return abs(area) / (2 * 1_000_000)

def procesar_entidad(e, mediciones):
    tipo = e.dxftype()
    capa_completa = e.dxf.layer.strip().upper()
    es_suma = capa_completa.endswith('+')
    es_resta = capa_completa.endswith('-')
    capa_base = capa_completa[:-1].strip() if (es_suma or es_resta) else capa_completa

    clave_normalizada = normalizar_nombre(capa_base)
    if clave_normalizada not in claves_normalizadas:
        capas_descartadas.add(capa_base)
        return None

    config = capas_medicion[claves_normalizadas[clave_normalizada]]
    factor = 1 if es_suma else (-1 if es_resta else 1)

    # Elevación real sin valor por defecto
    elevacion_raw = getattr(e.dxf, 'elevation', None)
    elevacion = elevacion_raw / 1000 if elevacion_raw not in [None, 0] else 0.0

    datos_entidad = {
        "Tipo": tipo,
        "Capa": capa_completa,
        "Base": capa_base,
        "Descripción": config.get('texto', 'Sin descripción'),
        "Operación": "+" if es_suma else ("-" if es_resta else " "),
        "Longitud (m)": 0.0,
        "Superficie (m²)": 0.0,
        "Unidades": 0,
        "Elevación (m)": elevacion
    }

    try:
        if tipo in ["LWPOLYLINE", "POLYLINE"]:
            if tipo == "LWPOLYLINE":
                puntos = [(p[0], p[1]) for p in e.get_points()]
                cerrada = e.closed
            else:
                puntos = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
                cerrada = e.is_closed

            if len(puntos) < 2:
                return None

            perimetro = sum(dist(p, q) for p, q in zip(puntos, puntos[1:] + ([puntos[0]] if cerrada else []))) / 1000
            area_poligono = calcular_area(puntos) if cerrada else 0.0

            if config['logica'] == 'perimetro_altura':
                sup = perimetro * elevacion * factor
                mediciones[clave_normalizada]['superficie_m2'] += sup
                datos_entidad.update({
                    "Superficie (m²)": sup,
                    "Longitud (m)": perimetro
                })

            elif config['logica'] == 'areas':
                sup = area_poligono * factor
                mediciones[clave_normalizada]['superficie_m2'] += sup
                datos_entidad.update({
                    "Superficie (m²)": sup,
                    "Longitud (m)": perimetro
                })

            elif config['logica'] == 'longitud':
                mediciones[clave_normalizada]['longitud_m'] += perimetro * factor
                datos_entidad["Longitud (m)"] = perimetro * factor

        elif tipo == "LINE":
            longitud = e.dxf.start.distance(e.dxf.end) / 1000

            if config['logica'] == 'longitud':
                mediciones[clave_normalizada]['longitud_m'] += longitud * factor
                datos_entidad["Longitud (m)"] = longitud * factor

            elif config['logica'] == 'perimetro_altura':
                sup = longitud * elevacion * factor
                mediciones[clave_normalizada]['superficie_m2'] += sup
                datos_entidad.update({
                    "Superficie (m²)": sup,
                    "Longitud (m)": longitud
                })

        elif tipo in ["CIRCLE", "ARC"]:
            if config['logica'] == 'unidad':
                mediciones[clave_normalizada]['unidades'] += 1 * factor
                datos_entidad["Unidades"] = 1 * factor

        return datos_entidad

    except Exception as ex:
        st.warning(f"Error procesando entidad en capa {capa_completa}: {str(ex)}")
        return None

def main():
    st.set_page_config(page_title="📐 Lignum System - Mediciones", layout="wide")
    st.title("📐 Lignum System - Cálculo Completo de Mediciones")
    uploaded_file = st.file_uploader("Subir archivo DXF", type=["dxf"])

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as temp_dxf:
            temp_dxf.write(uploaded_file.read())
            temp_dxf_path = temp_dxf.name

        if st.button("Calcular Mediciones y Costes"):
            try:
                doc = ezdxf.readfile(temp_dxf_path)
                msp = doc.modelspace()

                mediciones = {
                    normalizar_nombre(capa): {
                        'superficie_m2': 0.0,
                        'longitud_m': 0.0,
                        'unidades': 0,
                        'coste': 0.0
                    } for capa in capas_medicion
                }
                detalle_entidades = []

                for e in msp:
                    if datos := procesar_entidad(e, mediciones):
                        detalle_entidades.append(datos)

                resumen_coste = {}
                for capa_norm, valores in mediciones.items():
                    capa_original = claves_normalizadas[capa_norm]
                    config = capas_medicion[capa_original]
                    precio = float(config['precio_unitario'])
                    texto = config.get('texto', 'Sin descripción')

                    if config['logica'] in ['perimetro_altura', 'areas']:
                        m2 = max(0.0, valores['superficie_m2'])
                        coste = m2 * precio
                        resumen_coste[capa_original] = {
                            'Descripción': texto,
                            'Cantidad': round(m2, 2),
                            'Unidad': 'm²',
                            'Precio Unitario': f"€ {precio:,.2f}",
                            'Coste': f"€ {coste:,.2f}"
                        }

                    elif config['logica'] == 'longitud':
                        ml = max(0.0, valores['longitud_m'])
                        coste = ml * precio
                        resumen_coste[capa_original] = {
                            'Descripción': texto,
                            'Cantidad': round(ml, 2),
                            'Unidad': 'ml',
                            'Precio Unitario': f"€ {precio:,.2f}",
                            'Coste': f"€ {coste:,.2f}"
                        }

                    elif config['logica'] == 'unidad':
                        ud = max(0, valores['unidades'])
                        coste = ud * precio
                        resumen_coste[capa_original] = {
                            'Descripción': texto,
                            'Cantidad': ud,
                            'Unidad': 'ud',
                            'Precio Unitario': f"€ {precio:,.2f}",
                            'Coste': f"€ {coste:,.2f}"
                        }

                st.subheader("Resumen de Costes")
                
                # Mostrar estadísticas del resumen
                capas_con_costes = len(resumen_coste)
                capas_total = len(capas_medicion)
                st.info(f"📊 Se procesaron {capas_con_costes} de {capas_total} capas disponibles ({capas_con_costes/capas_total*100:.1f}%)")
                
                df_resumen = pd.DataFrame.from_dict(resumen_coste, orient='index')
                st.dataframe(df_resumen)

                # Calcular coste total correctamente
                coste_total = 0.0
                for item in resumen_coste.values():
                    coste_str = item['Coste']
                    # Extraer solo el número del string "€ 1,723.76"
                    coste_limpio = coste_str.replace('€', '').replace(',', '').strip()
                    try:
                        coste_total += float(coste_limpio)
                    except ValueError as e:
                        st.error(f"Error convirtiendo coste '{coste_str}': {e}")
                        coste_total += 0.0
                st.success(f"💰 COSTE TOTAL ESTIMADO: € {coste_total:,.2f}")

                if detalle_entidades:
                    st.subheader("Detalle de Entidades")
                    df_detalle = pd.DataFrame(detalle_entidades)
                    st.dataframe(df_detalle)

                    csv = df_detalle.to_csv(index=False, sep=';').encode('utf-8')
                    st.download_button(
                        label="📥 Descargar Detalle Completo",
                        data=csv,
                        file_name="detalle_mediciones_completo.csv",
                        mime="text/csv"
                    )

                if capas_descartadas:
                    st.subheader("⚠️ Capas ignoradas (no presentes en el diccionario de mediciones)")
                    for capa in sorted(capas_descartadas):
                        st.text(f"- {capa}")
                
                # Mostrar capas con precio 0 que no se incluyen en el resumen
                capas_precio_cero = []
                for capa, config in capas_medicion.items():
                    if config.get('precio_unitario', 0) == 0:
                        capas_precio_cero.append(capa)
                
                if capas_precio_cero:
                    st.subheader("💰 Capas con precio 0.00 (no incluidas en costes)")
                    st.info(f"Se encontraron {len(capas_precio_cero)} capas con precio 0.00")
                    # Mostrar solo las primeras 10 para no saturar la interfaz
                    for capa in sorted(capas_precio_cero)[:10]:
                        st.text(f"- {capa}")
                    if len(capas_precio_cero) > 10:
                        st.text(f"... y {len(capas_precio_cero) - 10} capas más")

            except Exception as e:
                st.error(f"❌ Error crítico al procesar el archivo: {str(e)}")

if __name__ == "__main__":
    main()
