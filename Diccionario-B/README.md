# Diccionario-B - Sistema de Capas de Medición Completo

## Descripción

Este directorio contiene el **diccionario completo de capas de medición** basado en el Dataset del proyecto Lignum System. Incluye todas las 794 partidas de construcción con sus precios, lógicas de medición y unidades de medida.

## Archivos Contenidos

### 1. `Diccionario_capas_B.py`
- **Contenido**: Diccionario manual con las primeras 50 partidas del Dataset
- **Tamaño**: 12 KB, 380 líneas
- **Propósito**: Archivo de ejemplo y referencia rápida

### 2. `Diccionario_capas_B_completo.py`
- **Contenido**: Diccionario completo con todas las 794 partidas del Dataset
- **Tamaño**: 131 KB, 3,980 líneas
- **Propósito**: Archivo principal para uso en producción

### 3. `generar_diccionario_completo.py`
- **Contenido**: Script Python para regenerar automáticamente el diccionario
- **Tamaño**: 8.4 KB, 227 líneas
- **Propósito**: Herramienta de mantenimiento y actualización

## Estructura del Diccionario

Cada partida tiene la siguiente estructura:

```python
"CODIGO_PARTIDA_DESCRIPCION": {
    "logica": "tipo_logica",
    "precio_unitario": precio_en_euros,
    "unidad": "unidad_medida"
}
```

### Tipos de Lógica de Medición

1. **`unidad`**: Elementos puntuales (CIRCLE en DXF)
   - Ejemplo: Lámparas, interruptores, aparatos sanitarios
   - Unidad: €/ud

2. **`areas`**: Superficies planas (LWPOLYLINE cerrada en DXF)
   - Ejemplo: Pavimentos, soleras, cubiertas
   - Unidad: €/m²

3. **`perimetro_altura`**: Muros y paramentos (LWPOLYLINE abierta en DXF)
   - Ejemplo: Tabiques, fachadas, muros
   - Unidad: €/m²

4. **`longitud`**: Elementos lineales (LWPOLYLINE o LINE en DXF)
   - Ejemplo: Molduras, zócalos, tuberías
   - Unidad: €/ml

5. **`volumen`**: Elementos tridimensionales
   - Ejemplo: Hormigones, excavaciones, rellenos
   - Unidad: €/m³

6. **`peso`**: Elementos medidos por peso
   - Ejemplo: Acero estructural
   - Unidad: €/kg

## Estadísticas del Diccionario Completo

- **Total de partidas**: 794
- **Lógicas de medición**:
  - `unidad`: 458 partidas (57.7%)
  - `perimetro_altura`: 126 partidas (15.9%)
  - `areas`: 114 partidas (14.4%)
  - `longitud`: 95 partidas (12.0%)

- **Unidades de medida**:
  - `€/ud`: 455 partidas (57.3%)
  - `€/m²`: 219 partidas (27.6%)
  - `€/ml`: 95 partidas (12.0%)
  - `€/m³`: 21 partidas (2.6%)
  - `€/kg`: 1 partida (0.1%)
  - Otros: 3 partidas (0.4%)

## Cómo Usar

### Importación Básica

```python
from Diccionario_capas_B_completo import capas_medicion

# Acceder a una partida específica
partida = capas_medicion["M_01.01.01_LEVANTADO PARA CONSERVAR DE LAMPARAS DE TECHO"]
print(f"Lógica: {partida['logica']}")
print(f"Precio: {partida['precio_unitario']} {partida['unidad']}")
```

### Integración con el Sistema Lignum

```python
# Reemplazar el import en lignum_measures_costs.py
# from capas_medicion import capas_medicion
from Diccionario_capas_B_completo import capas_medicion
```

### Búsqueda de Partidas

```python
# Buscar partidas por tipo de lógica
partidas_areas = {k: v for k, v in capas_medicion.items() 
                  if v['logica'] == 'areas'}

# Buscar partidas por unidad de medida
partidas_m2 = {k: v for k, v in capas_medicion.items() 
               if v['unidad'] == '€/m²'}
```

## Mantenimiento y Actualización

### Regenerar el Diccionario

Si se actualiza el Dataset CSV, ejecutar:

```bash
cd Diccionario-B
python generar_diccionario_completo.py
```

### Personalización

El script `generar_diccionario_completo.py` se puede modificar para:

- Ajustar la lógica de determinación de tipos de medición
- Agregar nuevas unidades de medida
- Modificar el formato de las claves del diccionario
- Incluir información adicional de cada partida

## Compatibilidad

- **Python**: 3.7+
- **Dependencias**: pandas, re
- **Sistema**: Compatible con el sistema Lignum existente
- **Formato**: Misma estructura que `capas_medicion.py` original

## Notas Importantes

1. **Precios**: Los precios están en euros y se extraen directamente del Dataset
2. **Lógica de medición**: Se infiere automáticamente del tipo de entidad y descripción
3. **Unidades**: Se normalizan según estándares del sistema
4. **Actualizaciones**: El diccionario se puede regenerar automáticamente cuando cambie el Dataset

## Autor

Generado automáticamente desde el Dataset del proyecto Lignum System.
