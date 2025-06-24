import streamlit as st
import ezdxf
import pandas as pd
import tempfile
from math import dist
from capas_medicion import capas_medicion

st.set_page_config(page_title="Lignum Presupuestos", layout="centered")

st.title("📐 Lignum System – Dashboard de mediciones")
st.markdown("Sube un archivo DXF para generar un presupuesto basado en capas normalizadas del sistema.")

uploaded_file = st.file_uploader("📁 Subir archivo DXF", type=["dxf"], accept_multiple_files=False)

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as temp_dxf:
        temp_dxf.write(uploaded_file.read())
        temp_dxf_path = temp_dxf.name

    st.success("✅ Archivo DXF cargado correctamente.")

    if st.button("📤 Procesar archivo y generar presupuesto"):
        try:
            doc = ezdxf.readfile(temp_dxf_path)
            msp = doc.modelspace()

            mediciones = {}
            resumen_coste = {}
            detalle_entidades = []

            # Inicializar mediciones para todas las capas base
            for capa in capas_medicion:
                mediciones[capa] = {
                    'superficie_m2': 0,
                    'longitud_m': 0,
                    'unidades': 0,
                    'coste': 0
                }

            def calcular_area(puntos):
                """Calcula el área de un polígono usando la fórmula del shoelace"""
                n = len(puntos)
                area = 0.0
                for i in range(n):
                    j = (i + 1) % n
                    area += puntos[i][0] * puntos[j][1]
                    area -= puntos[j][0] * puntos[i][1]
                return abs(area) / 2.0

            for e in msp:
                tipo = e.dxftype()
                capa_completa = e.dxf.layer.strip().upper()
                
                # Determinar si es capa de suma (+) o resta (-)
                es_suma = capa_completa.endswith('+')
                es_resta = capa_completa.endswith('-')
                
                # Obtener nombre base de la capa (sin + o -)
                if es_suma or es_resta:
                    capa_base = capa_completa[:-1].strip()
                else:
                    capa_base = capa_completa
                
                # Factor de multiplicación (1 para suma, -1 para resta)
                factor = 1 if es_suma else (-1 if es_resta else 1)

                # Obtener elevación (convertir mm a m)
                elevacion = e.dxf.elevation / 1000 if hasattr(e.dxf, 'elevation') else 0

                datos_entidad = {
                    "Tipo": tipo,
                    "Capa": capa_completa,
                    "Base": capa_base,
                    "Operación": "+" if es_suma else ("-" if es_resta else " "),
                    "Longitud (m)": 0,
                    "Superficie (m²)": 0,
                    "Unidades": 0,
                    "Elevación (m)": elevacion
                }

                if capa_base in capas_medicion:
                    config = capas_medicion[capa_base]

                    if tipo in ["LWPOLYLINE", "POLYLINE"]:
                        if tipo == "LWPOLYLINE":
                            puntos = [(v[0], v[1]) for v in e.get_points()]
                            cerrada = e.closed
                        else:
                            puntos = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
                            cerrada = e.is_closed

                        if len(puntos) < 2:
                            continue

                        # Calcular perímetro/longitud (convertir mm a m)
                        if cerrada:
                            perimetro = sum(dist(p, q) for p, q in zip(puntos, puntos[1:] + [puntos[0]])) / 1000
                            area = calcular_area(puntos) / 1_000_000  # Convertir a m²
                            
                            if config['logica'] == 'perimetro_altura':
                                altura = elevacion if elevacion > 0 else 3.0  # Altura predeterminada 3m
                                sup = perimetro * altura * factor
                                mediciones[capa_base]['superficie_m2'] += sup
                                datos_entidad["Superficie (m²)"] = round(sup, 4)
                            
                            elif config['logica'] == 'areas':
                                mediciones[capa_base]['superficie_m2'] += area * factor
                                datos_entidad["Superficie (m²)"] = round(area * factor, 4)
                            
                            datos_entidad["Longitud (m)"] = round(perimetro, 4)
                            
                        else:
                            longitud = sum(dist(p, q) for p, q in zip(puntos, puntos[1:])) / 1000
                            
                            if config['logica'] == 'longitud':
                                mediciones[capa_base]['longitud_m'] += longitud * factor
                                datos_entidad["Longitud (m)"] = round(longitud * factor, 4)
                            
                            elif config['logica'] == 'perimetro_altura':
                                altura = elevacion if elevacion > 0 else 3.0  # Altura predeterminada 3m
                                sup = longitud * altura * factor
                                mediciones[capa_base]['superficie_m2'] += sup
                                datos_entidad["Superficie (m²)"] = round(sup, 4)

                    elif tipo == "LINE":
                        longitud = e.dxf.start.distance(e.dxf.end) / 1000  # Convertir a m
                        
                        if config['logica'] == 'longitud':
                            mediciones[capa_base]['longitud_m'] += longitud * factor
                            datos_entidad["Longitud (m)"] = round(longitud * factor, 4)
                        
                        elif config['logica'] == 'perimetro_altura':
                            altura = elevacion if elevacion > 0 else 3.0  # Altura predeterminada 3m
                            sup = longitud * altura * factor
                            mediciones[capa_base]['superficie_m2'] += sup
                            datos_entidad["Superficie (m²)"] = round(sup, 4)

                    elif tipo in ["CIRCLE", "ARC"]:
                        if config['logica'] == 'unidad':
                            mediciones[capa_base]['unidades'] += 1 * factor
                            datos_entidad["Unidades"] = 1 * factor

                    detalle_entidades.append(datos_entidad)

            # Calcular costes basados en mediciones netas
            for capa in mediciones:
                config = capas_medicion[capa]

                if config['logica'] in ['perimetro_altura', 'areas']:
                    m2 = max(0, mediciones[capa]['superficie_m2'])
                    coste = m2 * config['precio_unitario']
                    mediciones[capa]['coste'] = round(coste, 2)
                    resumen_coste[capa] = {
                        'Cantidad': round(m2, 2),
                        'Unidad': 'm²',
                        'Precio Unitario': config['precio_unitario'],
                        'Coste': round(coste, 2)
                    }

                elif config['logica'] == 'longitud':
                    ml = max(0, mediciones[capa]['longitud_m'])
                    coste = ml * config['precio_unitario']
                    mediciones[capa]['coste'] = round(coste, 2)
                    resumen_coste[capa] = {
                        'Cantidad': round(ml, 2),
                        'Unidad': 'ml',
                        'Precio Unitario': config['precio_unitario'],
                        'Coste': round(coste, 2)
                    }

                elif config['logica'] == 'unidad':
                    unidades = max(0, mediciones[capa]['unidades'])
                    coste = unidades * config['precio_unitario']
                    mediciones[capa]['coste'] = round(coste, 2)
                    resumen_coste[capa] = {
                        'Cantidad': unidades,
                        'Unidad': 'ud',
                        'Precio Unitario': config['precio_unitario'],
                        'Coste': round(coste, 2)
                    }

            # Mostrar resultados
            st.subheader("📊 Resumen de costes")
            df_resumen = pd.DataFrame.from_dict(resumen_coste, orient='index')
            st.dataframe(df_resumen)

            coste_total = round(sum([v['coste'] for v in mediciones.values()]), 2)
            st.metric("💰 Coste Total Estimado", f"{coste_total} €")

            if detalle_entidades:
                st.subheader("📄 Detalle de entidades")
                df_detalle = pd.DataFrame(detalle_entidades)
                st.dataframe(df_detalle)

                csv = df_detalle.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="⬇️ Descargar detalle en CSV",
                    data=csv,
                    file_name="detalle_mediciones.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ No se encontraron entidades relevantes en el modelo.")

        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {e}")