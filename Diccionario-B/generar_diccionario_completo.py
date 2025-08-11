#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar automáticamente el diccionario completo de capas de medición
basado en el Dataset CSV del proyecto Lignum System.
"""

import pandas as pd
import re

def determinar_logica_medicion(tipo_entidad, lógica_texto, unidad):
    """
    Determina la lógica de medición basándose en el tipo de entidad y la descripción.
    """
    tipo_entidad = str(tipo_entidad).upper()
    lógica_texto = str(lógica_texto).upper()
    unidad = str(unidad).upper()
    
    # Lógica basada en el tipo de entidad
    if tipo_entidad == "CIRCLE":
        return "unidad"
    
    # Lógica basada en la descripción de la lógica
    if "PERIMETRO" in lógica_texto and "ALTURA" in lógica_texto:
        return "perimetro_altura"
    elif "AREAS" in lógica_texto or "AREA" in lógica_texto:
        return "areas"
    elif "LONGITUD" in lógica_texto or "PERIMETRO" in lógica_texto:
        return "longitud"
    elif "UNIDAD" in lógica_texto or "CIRCULO" in lógica_texto:
        return "unidad"
    elif "VOLUMEN" in lógica_texto or "ALTURA" in lógica_texto:
        return "volumen"
    elif "PESO" in lógica_texto or "KG" in unidad:
        return "peso"
    
    # Lógica basada en la unidad de medida
    if unidad in ["UD", "UNIDAD", "UNIDADES"]:
        return "unidad"
    elif unidad in ["M²", "M2", "M2"]:
        return "areas"
    elif unidad in ["ML", "METROS LINEALES"]:
        return "longitud"
    elif unidad in ["M³", "M3", "VOLUMEN"]:
        return "volumen"
    elif unidad in ["KG", "PESO"]:
        return "peso"
    
    # Por defecto, intentar inferir del tipo de entidad
    if tipo_entidad in ["LWPOLYLINE", "POLYLINE"]:
        return "areas"  # Por defecto para polilíneas
    elif tipo_entidad in ["LINE"]:
        return "longitud"  # Por defecto para líneas
    
    return "unidad"  # Por defecto

def limpiar_precio(precio_str):
    """
    Limpia y convierte el precio a float.
    """
    if pd.isna(precio_str):
        return 0.0
    
    precio_str = str(precio_str).replace(',', '.').replace('€', '').strip()
    
    # Buscar números en el string
    match = re.search(r'[\d.,]+', precio_str)
    if match:
        numero = match.group().replace(',', '.')
        try:
            return float(numero)
        except ValueError:
            return 0.0
    
    return 0.0

def generar_diccionario_capas():
    """
    Genera el diccionario completo de capas basado en el Dataset CSV.
    """
    try:
        # Leer el archivo CSV
        df = pd.read_csv('../Dataset/PLANTILLA PRESUPUESTO - TODAS LAS PARTIDAS.csv', 
                        sep=';', encoding='utf-8')
        
        # Filtrar solo las partidas que empiezan con M_
        partidas = df[df['Plantilla planos'].str.startswith('M_', na=False)].copy()
        
        print(f"Procesando {len(partidas)} partidas del Dataset...")
        
        # Crear el diccionario
        capas_medicion = {}
        
        for idx, row in partidas.iterrows():
            codigo = row['Plantilla planos']
            descripcion = row['Unnamed: 1'] if pd.notna(row['Unnamed: 1']) else ""
            tipo_entidad = row['Unnamed: 6'] if pd.notna(row['Unnamed: 6']) else ""
            logica_texto = row['Unnamed: 7'] if pd.notna(row['Unnamed: 7']) else ""
            unidad = row['Unnamed: 4'] if pd.notna(row['Unnamed: 4']) else ""
            precio = row['Unnamed: 9'] if pd.notna(row['Unnamed: 9']) else 0
            
            # Crear la clave del diccionario
            clave = f"{codigo}_{descripcion}" if descripcion else codigo
            
            # Determinar la lógica de medición
            logica = determinar_logica_medicion(tipo_entidad, logica_texto, unidad)
            
            # Limpiar el precio
            precio_limpio = limpiar_precio(precio)
            
            # Determinar la unidad de medida
            if pd.isna(unidad) or unidad == "":
                if logica == "unidad":
                    unidad_medida = "€/ud"
                elif logica == "areas":
                    unidad_medida = "€/m²"
                elif logica == "longitud":
                    unidad_medida = "€/ml"
                elif logica == "volumen":
                    unidad_medida = "€/m³"
                elif logica == "peso":
                    unidad_medida = "€/kg"
                else:
                    unidad_medida = "€/ud"
            else:
                unidad_upper = str(unidad).upper()
                if unidad_upper in ["UD", "UNIDAD", "UNIDADES"]:
                    unidad_medida = "€/ud"
                elif unidad_upper in ["M²", "M2", "M2"]:
                    unidad_medida = "€/m²"
                elif unidad_upper in ["ML", "METROS LINEALES"]:
                    unidad_medida = "€/ml"
                elif unidad_upper in ["M³", "M3", "VOLUMEN"]:
                    unidad_medida = "€/m³"
                elif unidad_upper in ["KG", "PESO"]:
                    unidad_medida = "€/kg"
                else:
                    unidad_medida = f"€/{unidad_upper.lower()}"
            
            # Agregar al diccionario
            capas_medicion[clave] = {
                "logica": logica,
                "precio_unitario": precio_limpio,
                "unidad": unidad_medida
            }
        
        return capas_medicion
        
    except Exception as e:
        print(f"Error al procesar el Dataset: {e}")
        return {}

def generar_archivo_python(capas_medicion, nombre_archivo="Diccionario_capas_B_completo.py"):
    """
    Genera el archivo Python con el diccionario completo.
    """
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write('# Diccionario completo de capas de medición basado en el Dataset\n')
            f.write('# Estructura: {codigo_capa: {logica, precio_unitario, unidad}}\n')
            f.write('# Generado automáticamente desde el Dataset CSV\n\n')
            
            f.write('capas_medicion = {\n')
            
            for i, (clave, valor) in enumerate(capas_medicion.items()):
                f.write(f'    "{clave}": {{\n')
                f.write(f'        "logica": "{valor["logica"]}",\n')
                f.write(f'        "precio_unitario": {valor["precio_unitario"]},\n')
                f.write(f'        "unidad": "{valor["unidad"]}"\n')
                
                if i < len(capas_medicion) - 1:
                    f.write('    },\n')
                else:
                    f.write('    }\n')
            
            f.write('}\n\n')
            f.write(f'# Total de partidas incluidas: {len(capas_medicion)}\n')
            f.write('# Archivo generado automáticamente desde el Dataset CSV\n')
        
        print(f"Archivo {nombre_archivo} generado exitosamente!")
        return True
        
    except Exception as e:
        print(f"Error al generar el archivo: {e}")
        return False

def main():
    """
    Función principal del script.
    """
    print("Generando diccionario completo de capas de medición...")
    
    # Generar el diccionario
    capas_medicion = generar_diccionario_capas()
    
    if capas_medicion:
        print(f"Se procesaron {len(capas_medicion)} partidas exitosamente.")
        
        # Generar el archivo Python
        if generar_archivo_python(capas_medicion):
            print("Proceso completado exitosamente!")
            
            # Mostrar algunas estadísticas
            logicas = {}
            unidades = {}
            for capa in capas_medicion.values():
                logica = capa['logica']
                unidad = capa['unidad']
                logicas[logica] = logicas.get(logica, 0) + 1
                unidades[unidad] = unidades.get(unidad, 0) + 1
            
            print("\nEstadísticas del diccionario generado:")
            print("Lógicas de medición:")
            for logica, count in sorted(logicas.items()):
                print(f"  {logica}: {count} partidas")
            
            print("\nUnidades de medida:")
            for unidad, count in sorted(unidades.items()):
                print(f"  {unidad}: {count} partidas")
        else:
            print("Error al generar el archivo Python.")
    else:
        print("No se pudo generar el diccionario.")

if __name__ == "__main__":
    main()
