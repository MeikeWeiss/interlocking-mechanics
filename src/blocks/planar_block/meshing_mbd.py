import numpy as np
import pyvista as pv

def refine_triangulation(vertices, faces, levels=1):
    """
    Uniforme, symmetrische Verfeinerung einer Oberflächen-Triangulierung.

    Parameters
    ----------
    vertices : (N, 3) array
        3D-Koordinaten der Knoten.
    faces : (M, 3) array (int)
        Dreiecke als Indizes in `vertices`.
    levels : int
        Anzahl der Verfeinerungsstufen. Jede Stufe teilt jedes Dreieck in 4.

    Returns
    -------
    new_vertices : (N', 3) array
        Verfeinerte Knotenkoordinaten.
    new_faces : (M', 3) array (int)
        Verfeinerte Dreiecke.
    """
    vertices = np.asarray(vertices, dtype=float)
    faces = np.asarray(faces, dtype=int)

    for _ in range(levels):
        edge_midpoint_index = {}
        new_faces = []

        def get_midpoint(i, j):
            """Gibt Index des Kantenmittelpunkts von (i, j) zurück, mit Caching."""
            if i > j:
                i, j = j, i
            key = (i, j)
            if key in edge_midpoint_index:
                return edge_midpoint_index[key]
            else:
                vi = vertices[i]
                vj = vertices[j]
                vm = 0.5 * (vi + vj)
                idx = len(vertices_list)
                vertices_list.append(vm)
                edge_midpoint_index[key] = idx
                return idx

        vertices_list = list(vertices)

        for tri in faces:
            i, j, k = tri

            # Kantenmittelpunkte
            ij = get_midpoint(i, j)
            jk = get_midpoint(j, k)
            ki = get_midpoint(k, i)

            new_faces.append([i, ij, ki])
            new_faces.append([j, jk, ij])
            new_faces.append([k, ki, jk])
            new_faces.append([ij, jk, ki])

        vertices = np.asarray(vertices_list, dtype=float)
        faces = np.asarray(new_faces, dtype=int)

    return vertices, faces

def plot_mesh_interactive(vertices, faces):
    # PyVista erwartet ein flaches Array für die Dreiecke:
    faces_pv = np.hstack([np.full((faces.shape[0], 1), 3), faces]).astype(np.int32)

    mesh = pv.PolyData(vertices, faces_pv)

    plotter = pv.Plotter()
    plotter.add_mesh(mesh, show_edges=True, color="lightgray")
    plotter.show()   # interaktives Fenster