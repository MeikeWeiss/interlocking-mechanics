import os
from scripts.planar.config import *
from src.blocks.planar_block.post_mbd import compute_eff_area, measure_pc
from scripts.planar.mbd_planar import get_run_name
import numpy as np
import pandas as pd

def get_snaps_file_path(type, group, refinement, n, m, h, out_config, bvp='ceiling',
                        support='implicit', objective='force'):

    # same folder name as in scripts/planar/mbd_planar.py
    out_config['name'] = get_run_name(type, group, bvp, refinement, n, m, h, support, objective)
    return f"{out_config['out_dir']}{out_config['name']}/snaps.txt"



def save_results(df, output_file, show=True):

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        df.to_excel(output_file, index=False)
        if show:
            print(f"Gespeichert als Excel: {output_file}")
        return True
    except ModuleNotFoundError:
        csv_file = output_file.replace('.xlsx', '.csv')
        df.to_csv(csv_file, index=False)
        if show:
            print(f"openpyxl nicht gefunden. Gespeichert als CSV: {csv_file}")
        return True
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")
        return False


def save_results_with_charts(df, output_file, show=True):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Ergebnisse', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Ergebnisse']
        
        max_row = len(df) + 1
        

        col_indices = {col: idx for idx, col in enumerate(df.columns)}
        
        chart1_main = workbook.add_chart({'type': 'line'})
        chart1_secondary = workbook.add_chart({'type': 'line'})
        
        col_idx = col_indices['Max pressure']
        chart1_main.add_series({
            'name': ['Ergebnisse', 0, col_idx],
            'categories': ['Ergebnisse', 1, 0, max_row, 0],
            'values': ['Ergebnisse', 1, col_idx, max_row, col_idx],
            'line': {'width': 2, 'color': '#4472C4'},  # Blau
            'marker': {'type': 'circle', 'size': 6},
        })
        
        col_idx = col_indices['Average pressure masked']
        chart1_secondary.add_series({
            'name': ['Ergebnisse', 0, col_idx],
            'categories': ['Ergebnisse', 1, 0, max_row, 0],
            'values': ['Ergebnisse', 1, col_idx, max_row, col_idx],
            'y2_axis': True,
            'line': {'width': 2, 'color': '#ED7D31'},  # Orange
            'marker': {'type': 'diamond', 'size': 6},
        })
        
        chart1_main.set_title({'name': 'Druck-Spitzenwerte'})
        chart1_main.set_x_axis({'name': 'h-Wert'})
        chart1_main.set_y_axis({'name': 'Max pressure', 'major_gridlines': {'visible': True}})
        chart1_secondary.set_y_axis({'name': 'Average of max pressure', 'major_gridlines': {'visible': False}})
        chart1_main.combine(chart1_secondary)
        
        chart2_main = workbook.add_chart({'type': 'line'})
        chart2_secondary = workbook.add_chart({'type': 'line'})
        
        col_idx = col_indices['Average effective area']
        chart2_main.add_series({
            'name': ['Ergebnisse', 0, col_idx],
            'categories': ['Ergebnisse', 1, 0, max_row, 0],
            'values': ['Ergebnisse', 1, col_idx, max_row, col_idx],
            'line': {'width': 2, 'color': '#2E8B57'},  # Grün
            'marker': {'type': 'square', 'size': 6},
        })
        
        col_idx = col_indices['Average of max pressure']
        chart2_secondary.add_series({
            'name': ['Ergebnisse', 0, col_idx],
            'categories': ['Ergebnisse', 1, 0, max_row, 0],
            'values': ['Ergebnisse', 1, col_idx, max_row, col_idx],
            'y2_axis': True,
            'line': {'width': 2, 'color': '#A5A5A5'},  # Grau
            'marker': {'type': 'triangle', 'size': 6},
        })
        
        chart2_main.set_title({'name': 'Effektive Fläche und gemittelter Druck'})
        chart2_main.set_x_axis({'name': 'h-Wert'})
        chart2_main.set_y_axis({'name': 'Average effective area', 'major_gridlines': {'visible': True}})
        chart2_secondary.set_y_axis({'name': 'Average pressure masked', 'major_gridlines': {'visible': False}})
        chart2_main.combine(chart2_secondary)
        
        worksheet.insert_chart('G2', chart1_main)
        worksheet.insert_chart('G22', chart2_main)
    
    if show:
        print(f"Ergebnisse mit 2 Diagrammen (jeweils 2 Y-Achsen) gespeichert in: {output_file}")


def analyse_results_batch(h_list, 
                          type='irr_octahedron', 
                          group='octa', 
                          refinement=4, 
                          n=6, 
                          m=6, 
                          output_filename='results.xlsx', 
                          out_dir='./outputs/planar/',
                          bvp='ceiling',
                          support='implicit',
                          objective='force',
                          show=True):
    
    out_config['out_dir'] = out_dir
    
    output_file = os.path.join(out_dir, output_filename)
    
    results = []
    
    for h in h_list:
        block_config.update({
            'refinement': refinement,
            'type': type,
            'h': h
        })
        snaps_file = get_snaps_file_path(type, group, refinement, n, m, h, out_config, bvp,
                                         support, objective)
        
        try:
            snaps = np.loadtxt(snaps_file)
        except FileNotFoundError:
            print(f"h={h:.3f}: Datei nicht gefunden: {snaps_file}")
            continue
        
        A_eff = compute_eff_area(snaps, show=False)
        measures = measure_pc(snaps, A_eff['mask'], show=False)
        
        results.append({
            'h': h,
            'Average effective area': A_eff['average'],
            'Average pressure masked': measures['p_eff_bl_avg'],
            'Max pressure': measures['p_max'],
            'Average of max pressure': measures['p_max_bl_avg']
        })
        
        if show:
            print(f"h={h:.3f}: A_eff={A_eff['average']:.4f}, p_avg={measures['p_eff_bl_avg']:.4f}")
    
    if results:
        df = pd.DataFrame(results).sort_values('h').reset_index(drop=True)
        save_results_with_charts(df, output_file, show)
        return df
    else:
        print("Keine Daten gefunden.")
        return None


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':
    h_list = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    # Beispiel 1: Irreguläres Oktaeder
    df1 = analyse_results_batch(
        h_list=h_list,
        type='irr_octahedron',
        group='irr_octa',
        output_filename='results_irr_octahedron.xlsx',
        out_dir='./outputs/planar/',
        show=False
    )

    h_list = [np.sqrt(2)/2, 7*np.sqrt(2)/16, 6*np.sqrt(2)/16, 5*np.sqrt(2)/16, 
              np.sqrt(2)/4, 3*np.sqrt(2)/16, np.sqrt(2)/8, np.sqrt(2)/16]
    
    # Beispiel 2: Versatile
    df2 = analyse_results_batch(
        h_list=h_list,
        type='versatile_param',
        group='p4',
        n=10,
        m=10,
        output_filename='results_versatile.xlsx',
        out_dir='./outputs/planar/',
        show=False
    )