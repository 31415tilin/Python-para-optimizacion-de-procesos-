import pandas as pd
import numpy as np
import os

def procesar_cartera_saras(Libro1:any, cartera_limpia:any):
    if not os.path.exists(Libro1):
        print(f"ERROR: No se encontró el archivo {Libro1}. Verifica la ruta.")
        return
    
    try:
        df = pd.read_csv(Libro1, sep=';', encoding='latin1')
        
        if 'Sector_Economico' in df.columns:
            df['Sector_Economico'] = df['Sector_Economico'].str.strip().str.title()
            df['Sector_Economico'] = df['Sector_Economico'].fillna('No Registrado')
            
        if 'Monto_Credito' in df.columns:
            df['Monto_Credito'] = (df['Monto_Credito']
                                   .astype(str)
                                   .str.replace('$', '', regex=False)
                                   .str.replace(',', '', regex=False)
                                   .astype(float))
            
        if 'Calificacion_SARAS' in df.columns:
            df['Calificacion_SARAS'] = df['Calificacion_SARAS'].fillna('Pendiente Evaluar')
            sectores_riesgo = ['Agricultura', 'Manufactura Pesada', 'Minería', 'Agroindustria', 'Curtiembres']
            
            df['Nivel_Riesgo_Ambiental'] = np.where(
                df['Sector_Economico'].isin(sectores_riesgo), 
                'Alto Riesgo', 
                'Riesgo Normal/Bajo'
            )
            
            df.loc[df['Sector_Economico'] == 'No Registrado', 'Nivel_Riesgo_Ambiental'] = 'Requiere Revisión'
            
        df.to_excel(cartera_limpia, index=False)
        print(f"¡Éxito! El archivo limpio y clasificado se guardó en: {cartera_limpia}")
        
    except Exception as e:
        print(f"Ocurrió un error inesperado durante el procesamiento: {e}")
        
if __name__ == '__main__':
    archivo_crudo = 'Libro1.xlsx.csv'
    archivo_salida = 'cartera_limpia_saras.xlsx'
    
    procesar_cartera_saras(archivo_crudo, archivo_salida)