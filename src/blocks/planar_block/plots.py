import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
from pathlib import Path

def plot_assembly_fc(assembly, lam, contact_faces,
                     save=False, path='test.png',
                     cpos=None):

    import matplotlib.colors as mcolors
    
    # Define colors
    #colors = ["white", "yellow", "orange", "red"]
    colors = ["white", "#40E0D0", "lightgreen", "yellow",  "red"]
    
    # Create colormap
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_map", colors)

    # Plot
    plotter = pv.Plotter()
    
    for bl in assembly:
        n_contact = len(contact_faces)
        plot_fc_surfaces(plotter, bl.nodes, bl.cells_2D, bl.cells_2D_arr,
                         lam[bl.ID*n_contact:bl.ID*n_contact+n_contact], contact_faces,cmap)


    # Add small coordinate axes in corner
    plotter.show_axes()

    # camaera position
    if cpos is not None:
        plotter.camera_position = cpos

    # Enable parallel (orthographic) projection
    plotter.enable_parallel_projection()

    if save:
        ext = Path(path).suffix.lower()

        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
            plotter.show()
            plotter.screenshot(path)

        elif ext == ".html":
            plotter.export_html(path)
            plotter.show()
            
        else:
            raise ValueError(f"Unsupported extension {ext}. "
                             "Use an image format or .html")

    else:
        plotter.show()

    return


def plot_fc_surfaces(plotter,
                     points, triangles, cells,
                     fc, # 'contact pressure' (lambda)
                     contact_faces,
                     cmap,
                     ):
    
    # Create PyVista mesh
    mesh = pv.PolyData(points, cells)
    # mesh = pv.UnstructuredGrid(cells[6*4:], np.full(len(triangles[6:]), pv.CellType.TRIANGLE), points)

    fc_full = np.zeros(mesh.n_cells)
    fc_full[contact_faces] = fc

    mesh.cell_data['contact force'] = fc_full
    
    plotter.add_mesh(mesh, scalars='contact force', cmap=cmap,
                     show_edges=False, color='skyblue',
                     opacity=1.0, lighting=False)

    # Extract feature edges (sharp edges, boundaries, non-manifold edges)
    feature_edges = mesh.extract_feature_edges(
        boundary_edges=True,      # extract boundary edges
        feature_edges=True,       # extract sharp edges
        manifold_edges=False,     # extract manifold edges
        feature_angle=40          # angle threshold in degrees
    )

    plotter.add_mesh(feature_edges, color="black", line_width=2)
    
    return


def plot_block_fc(plotter,
                  points, triangles, cells,
                  fc, # 'contact pressure' (lambda)
                  cmap,
                  ):

    # Create PyVista mesh
    mesh = pv.UnstructuredGrid(cells, np.full(len(triangles), pv.CellType.TRIANGLE), points)

    mesh.cell_data['fc'] = fc
    
    plotter.add_mesh(mesh, scalars='fc', cmap=cmap, show_edges=False, color='skyblue', opacity=1.0)
    #plotter.add_points(points, color='black', point_size=6)

    return


def plot_block_Fc(points, triangles, cells,
                  centroid, face_centers,
                  Fc,
                  ids=False):

    # Create PyVista mesh
    mesh = pv.UnstructuredGrid(cells, np.full(len(triangles), pv.CellType.TRIANGLE), points)

    # Plot
    plotter = pv.Plotter()
    plotter.add_mesh(mesh, show_edges=True, color='skyblue', opacity=0.8)
    plotter.add_points(points, color='black', point_size=6)
    
    if ids == True:
        # Add point labels (IDs)
        point_ids = np.arange(len(points))
        plotter.add_point_labels(points, point_ids, font_size=12,
                                 point_color='red', text_color='black')

    # Plot face centroids as small spheres
    for center in face_centers:
        plotter.add_mesh(pv.Sphere(radius=0.02, center=center), color="black")

    # Plot normals as arrows starting from centroids
    for center, Fc in zip(face_centers, Fc):
        if not np.allclose(Fc, 0):   # skip zero rows
            length = np.linalg.norm(Fc)  # original vector length
            direction = Fc / length      # normalize for PyVista
            arrow = pv.Arrow(start=center, direction=direction, scale=2*length)
            plotter.add_mesh(arrow, color="blue")
            
    # Add the center of mass as a sphere
    plotter.add_mesh(pv.Sphere(radius=0.05, center=centroid), color="red", name="center_of_mass")
    
    
    plotter.show()


    return


def plot_block_surfaces(points, triangles, cells,
                        centroid, face_centers,
                        face_normals,
                        ids=False,
                        save=False, path='test.png'):

    # Create PyVista mesh
    mesh = pv.UnstructuredGrid(cells, np.full(len(triangles), pv.CellType.TRIANGLE), points)

    # Plot
    plotter = pv.Plotter()
    plotter.add_mesh(mesh, show_edges=True, color='lightyellow', opacity=0.8)
    plotter.add_points(points, color='black', point_size=6)

    if ids == True:
        # Add point labels (IDs)
        point_ids = np.arange(len(points))
        plotter.add_point_labels(points, point_ids, font_size=12,
                                 point_color='red', text_color='black')

    # Plot face centroids as small spheres
    for center in face_centers:
        plotter.add_mesh(pv.Sphere(radius=0.02, center=center), color="black")

    # Plot normals as arrows starting from centroids
    scale = 0.3
    for center, normal in zip(face_centers, face_normals):
        if not np.allclose(normal, 0):   # skip zero rows

            # normalize
            normal = normal / np.linalg.norm(normal)
            
            # define start so arrow ends at the centroid
            start = center - normal * scale
            arrow = pv.Arrow(start=start, direction=normal, scale=scale)
            
            plotter.add_mesh(arrow, color="blue")
            
    # Add the center of mass as a sphere
    plotter.add_mesh(pv.Sphere(radius=0.05, center=centroid), color="red", name="center_of_mass")
    
    # # Plot all cross product vectors as arrows starting from C
    # for vec in M:
    #     arrow = pv.Arrow(start=centroid, direction=vec, scale=0.5)  # scale adjusts length
    #     plotter.add_mesh(arrow, color="blue")

    # # (optional) also plot lever vectors
    # for vec in r:
    #     arrow = pv.Arrow(start=centroid, direction=vec, scale=0.5)
    #     plotter.add_mesh(arrow, color="green")
    
    if save:
        ext = Path(path).suffix.lower()

        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
            plotter.show()
            plotter.screenshot(path)

        elif ext == ".html":
            plotter.export_html(path)
            plotter.show()
            
        else:
            raise ValueError(f"Unsupported extension {ext}. "
                             "Use an image format or .html")

    else:
        plotter.show()
        
    return


#################### matrix as a table ##########################


def plot_matrix_as_table(matrix):

    # Format numbers into scientific notation with 6 decimals
    formatted_matrix = [[f"{val:.3e}" if val != 0 else "" for val in row] for row in matrix]

    fig, ax = plt.subplots()
    ax.axis("off")  # Hide axes

    # Create a table with formatted text
    table = ax.table(
        cellText=formatted_matrix,
        loc="center",
        cellLoc="center"
    )

    # Make table look nice
    table.scale(1, 1.5)
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    plt.show()
    return
