import pandas as pd
import numpy as np
import os

# Intentamos importar SciPy para la prueba estadística. Si no está, el código sigue funcionando.
try:
    from scipy.stats import mannwhitneyu
    SCIPY_DISPONIBLE = True
except ImportError:
    SCIPY_DISPONIBLE = False

# --- CONSTANTES DE NEGOCIO (Umbrales BGR) ---
SECTORES_RIESGO = ['Agricultura', 'Manufactura Pesada', 'Minería', 'Agroindustria', 'Curtiembres']
UMBRAL_ALERTA_PORCENTAJE = 0.40  # 40% de límite para cartera de alto riesgo
CALIFICACIONES_CRITICAS = ['C', 'D'] # Forzan automáticamente al cliente a Alto Riesgo

def procesar_cartera_saras(ruta_entrada, ruta_salida):
    if not os.path.exists(ruta_entrada):
        print(f"ERROR: No se encontró el archivo {ruta_entrada}. Verifica la ruta.")
        return
    
    try:
        print("Iniciando procesamiento y limpieza de datos...")
        
        # 1. LECTURA Y CORRECCIÓN DE FORMATO (Punto y coma, UTF-8)
        df = pd.read_csv(ruta_entrada, sep=';', encoding='utf-8')
        
        # Limpiamos los nombres de las columnas por si tienen espacios invisibles
        df.columns = df.columns.str.strip()
        
        # 2. LIMPIEZA GLOBAL Y TRATAMIENTO DE "NULOS"
        df.replace('Nulo', np.nan, inplace=True)
        
        if 'Sector_Economico' in df.columns:
            # NUEVA LÍNEA: Corta el texto en la coma y se queda solo con el primer pedazo
            df['Sector_Economico'] = df['Sector_Economico'].astype(str).str.split(',').str[0]
            
            # Limpieza estándar (quitar espacios y poner mayúsculas iniciales)
            df['Sector_Economico'] = df['Sector_Economico'].str.strip().str.title()
            
            # Por si al cortar quedó la palabra "Nulo", la volvemos a detectar
            df['Sector_Economico'] = df['Sector_Economico'].replace('Nulo', np.nan)
            df['Sector_Economico'] = df['Sector_Economico'].fillna('No Registrado')
            
        if 'Monto_Credito_USD' in df.columns:
            df['Monto_Credito_USD'] = (df['Monto_Credito_USD']
                                   .astype(str)
                                   .str.replace('$', '', regex=False)
                                   .str.replace(',', '', regex=False)
                                   .astype(float))
            
        if 'Calificacion_SARAS' in df.columns:
            df['Calificacion_SARAS'] = df['Calificacion_SARAS'].fillna('Pendiente Evaluar')
            
            # Columna de auditoría para detectar datos incompletos
            df['Dato_Incompleto'] = np.where(
                (df['Sector_Economico'] == 'No Registrado') | 
                (df['Calificacion_SARAS'] == 'Pendiente Evaluar'), 
                'Sí', 'No'
            )
            
            # 3. LÓGICA SARAS DE RIESGO
            df['Nivel_Riesgo_Ambiental'] = 'Riesgo Normal/Bajo'
            df.loc[df['Sector_Economico'].isin(SECTORES_RIESGO), 'Nivel_Riesgo_Ambiental'] = 'Alto Riesgo'
            df.loc[df['Calificacion_SARAS'].isin(CALIFICACIONES_CRITICAS), 'Nivel_Riesgo_Ambiental'] = 'Alto Riesgo'
            df.loc[df['Dato_Incompleto'] == 'Sí', 'Nivel_Riesgo_Ambiental'] = 'Requiere Revisión'

        print("Calculando indicadores estadísticos y de concentración (HHI)...")
        
        # 4. CÁLCULOS Y MODELADO ESTADÍSTICO
        resumen_sectores = df.groupby('Sector_Economico')['Monto_Credito_USD'].sum().reset_index()
        total_cartera = resumen_sectores['Monto_Credito_USD'].sum()
        
        resumen_sectores['Participacion_%'] = (resumen_sectores['Monto_Credito_USD'] / total_cartera) * 100
        resumen_sectores['Cuota_Cuadrado'] = resumen_sectores['Participacion_%'] ** 2
        hhi_index = resumen_sectores['Cuota_Cuadrado'].sum()
        
        monto_alto_riesgo = df.loc[df['Nivel_Riesgo_Ambiental'] == 'Alto Riesgo', 'Monto_Credito_USD'].sum()
        pct_alto_riesgo = (monto_alto_riesgo / total_cartera) * 100 if total_cartera > 0 else 0
        alerta_activa = 'SÍ (Exceso de Riesgo)' if (pct_alto_riesgo/100) > UMBRAL_ALERTA_PORCENTAJE else 'NO (Dentro del límite)'

        p_value_str = "No calculado (Requiere SciPy o más datos)"
        if SCIPY_DISPONIBLE:
            grupo_alto = df[df['Nivel_Riesgo_Ambiental'] == 'Alto Riesgo']['Monto_Credito_USD'].dropna()
            grupo_resto = df[df['Nivel_Riesgo_Ambiental'] != 'Alto Riesgo']['Monto_Credito_USD'].dropna()
            
            if len(grupo_alto) > 0 and len(grupo_resto) > 0:
                stat, p_valor = mannwhitneyu(grupo_alto, grupo_resto, alternative='two-sided')
                p_value_str = f"{p_valor:.4f}"
                
        indicadores = pd.DataFrame({
            'Metrica_Clave': ['% Cartera en Alto Riesgo', 'Umbral Máximo Permitido', 'Alerta de Límite Activa', 'Índice de Concentración (HHI)', 'Significancia Estadística (P-Value)'],
            'Valor': [f"{pct_alto_riesgo:.2f}%", f"{UMBRAL_ALERTA_PORCENTAJE*100}%", alerta_activa, f"{hhi_index:.2f}", p_value_str]
        })

        # 5. EXPORTACIÓN A MÚLTIPLES HOJAS DE EXCEL
        with pd.ExcelWriter(ruta_salida, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False) 
            indicadores.to_excel(writer, sheet_name='Indicadores_Estadisticos', index=False)
            resumen_sectores.to_excel(writer, sheet_name='Resumen_Sectores', index=False)
            
        print(f"\n¡Proceso Finalizado! Archivo guardado en: {ruta_salida}")
        print("-" * 40)
        print(f"Resultados Rápidos:")
        print(f" -> Riesgo de Cartera: {pct_alto_riesgo:.2f}% (Alerta: {alerta_activa})")
        print(f" -> Índice HHI: {hhi_index:.2f}")
        print("-" * 40)
        
    except Exception as e:
        print(f"Ocurrió un error inesperado durante el procesamiento: {e}")

# --- BLOQUE DE EJECUCIÓN PRINCIPAL ---
if __name__ == '__main__':
    archivo_crudo = 'ruta_entrada.csv'
    archivo_salida = 'ruta_salida.xlsx'
    
    procesar_cartera_saras(archivo_crudo, archivo_salida)