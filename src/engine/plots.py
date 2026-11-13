"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: ?

License: MIT

Reference:
"""

import numpy as np
import pyvista as pv
from pathlib import Path

########################################################################
# Plots
########################################################################

def plot_point_cloud(points):

    # Create a PolyData object with the points
    point_cloud = pv.PolyData(points)
    
    # Optional: set a point size for better visibility
    plotter = pv.Plotter()
    plotter.add_mesh(point_cloud, color='red', point_size=10, render_points_as_spheres=True)
    plotter.show_grid()
    plotter.add_axes()  # adds the interactive 3D coordinate axes widget
    plotter.show()

    # Clean up
    plotter.close()   # Important: closes rendering window and releases buffers
    del plotter

    return


def plot_mesh(plotter, mesh, all_points, plt_conf):
    
    # Plot
    plotter.add_mesh(
        mesh,
        show_edges=plt_conf['show_edges'],
        color=plt_conf['color'],
        opacity=plt_conf['opacity'],
        ambient=plt_conf['ambient'],
        line_width=plt_conf['line_width'],
    )
    
    if plt_conf['show_nodes'] == True:
        plotter.add_points(
            all_points,
            color='black',
            point_size=plt_conf['point_size'],
            render_points_as_spheres=True,
        )

    if plt_conf['node_ids'] == True:
        # Add point labels (IDs)
        point_ids = np.arange(len(points))
        plotter.add_point_labels(
            points, point_ids,
            font_size=12,
            point_color='red',
            text_color='black'
        )

    return



def plot_tri3_cells(plotter, all_points, n_cells, cells_arr, plt_conf):

    # Define all cells as tetrahedra
    cell_types = np.full(n_cells, pv.CellType.TRIANGLE)

    # Build mesh
    mesh = pv.UnstructuredGrid(cells_arr, cell_types, all_points)
    
    plot_mesh(plotter, mesh, all_points, plt_conf)
    
    return


def plot_quad4_cells(plotter, all_points, n_quad4, cells_arr, plt_conf):

    # Define all cells as tetrahedra
    cell_types = np.full(n_quad4, pv.CellType.QUAD)

    # Build mesh
    mesh = pv.UnstructuredGrid(cells_arr, cell_types, all_points)

    plot_mesh(plotter, mesh, all_points, plt_conf)
    
    return
    

def plot_tet4_cells(plotter, all_points, n_tet4, cells_arr, plt_conf):

    # Define all cells as tetrahedra
    cell_types = np.full(n_tet4, pv.CellType.TETRA)

    # Build mesh
    mesh = pv.UnstructuredGrid(cells_arr, cell_types, all_points)
    
    # Plot mesh
    plot_mesh(plotter, mesh, all_points, plt_conf)
    
    return


def plot_prism6_cells(plotter, all_points, n_prisms, cells_arr, plt_conf):

    cell_types = np.full(n_prisms, pv.CellType.WEDGE)

    # Build mesh
    mesh = pv.UnstructuredGrid(cells_arr, cell_types, all_points)
    
    # Plot
    plot_mesh(plotter, mesh, all_points, plt_conf)
    
    return


def plot_hex8_cells(plotter, all_points, n_hex8, cells_arr, plt_conf):

    cell_types = np.full(n_hex8, pv.CellType.HEXAHEDRON)

    # Build mesh
    mesh = pv.UnstructuredGrid(cells_arr, cell_types, all_points)
    
    # Plot
    plot_mesh(plotter, mesh, all_points, plt_conf)
    
    return

#################################################################################
# general plots
#################################################################################
def set_plotter(plotter, plt_conf):

    # Add a headlight (light attached to the camera)
    headlight = pv.Light(light_type='headlight', intensity=plt_conf['intensity'])
    plotter.add_light(headlight)
    
    # Enable parallel (orthographic) projection
    if plt_conf['parallel']:
        plotter.enable_parallel_projection()
    
    # camera position and show or save
    if plt_conf['views'] is not None:
        for v in plt_conf['views']:

            if v == 'pers':
                pass
            else:
                plotter.camera_position = v

            # Automatically zoom/fit the scene
            plotter.reset_camera()
            plotter.camera.zoom(plt_conf['zoom'])

            if plt_conf['show']:
                plotter.show()
            # else:
            #     plotter.show(auto_close=False)  # render scene without displaying

            # save the plot
            if plt_conf['save']:
                # After interacting, save current view
                plotter.show(auto_close=False)  # render scene without displaying
                plotter.screenshot(f"{plt_conf['out_dir']}{plt_conf['result_name']}_{v}.png", scale=1)    

    if plt_conf['html']:
        plotter.export_html(f"{plt_conf['out_dir']}{plt_conf['result_name']}.html")
        
    return


def plot_faces( all_points, n_cells, cells_arr, plt_conf ):

    import vtk

    vtk.vtkLogger.SetStderrVerbosity(vtk.vtkLogger.VERBOSITY_OFF)
    vtk.vtkObject.GlobalWarningDisplayOff()
    
    # Create VTK axes actor
    vtk_axes = vtk.vtkAxesActor()
    vtk_axes.SetTotalLength(5.0, 5.0, 5.0)  # make triad bigger
    #vtk_axes.SetShaftTypeToLine()            # simple lines
    vtk_axes.SetShaftTypeToCylinder()        # use cylinders instead of lines
    vtk_axes.SetCylinderRadius(0.05)          # shaft thickness
    #vtk_axes.SetTipTypeToNone()              # no arrow tips
    vtk_axes.SetTipTypeToCone()              # enable arrow tips
    vtk_axes.SetConeRadius(0.5)              # arrow tip width
    vtk_axes.SetAxisLabels(False)             # disable labels

    # build the scene
    plotter = pv.Plotter(off_screen=not plt_conf['show'],
                         window_size=plt_conf['window_size'],
                         lighting='light_kit')

    if cells_arr[0] == 3:
        plot_tri3_cells(plotter, all_points, n_cells, cells_arr, plt_conf)
        
    elif cells_arr[0] == 4:
        plot_quad4_cells(plotter, all_points, n_cells, cells_arr, plt_conf)

    #plotter.add_axes()  # adds the interactive 3D coordinate axes widget
    plotter.add_actor(vtk_axes)  # add the triad at the origin

    set_plotter(plotter, plt_conf)
    
    # Clean up
    plotter.close()   # Important: closes rendering window and releases buffers
    del plotter
    
    return


def plot_cells(all_points, n_cells, cells_arr, plt_conf ):

    plotter = pv.Plotter(off_screen=not plt_conf['show'],
                         window_size=plt_conf['window_size'],
                         lighting='light_kit' # multiple lights, softer shadows
                         )

    if cells_arr[0] == 4:
        plot_tet4_cells(plotter, all_points, n_cells, cells_arr, plt_conf)

    elif cells_arr[0] == 6:
        plot_prism6_cells(plotter, all_points, n_cells, cells_arr, plt_conf)
        
    elif cells_arr[0] == 8:
        plot_hex8_cells(plotter, all_points, n_cells, cells_arr, plt_conf)
        
    plotter.add_axes()  # adds the interactive 3D coordinate axes widget

    set_plotter(plotter, plt_conf)
    
    # Clean up
    plotter.close()   # Important: closes rendering window and releases buffers
    del plotter
    
    return


def plot_block(plotter, all_points, n_cells, cells_arr, color='skyblue', line_width=3.):

    if cells_arr[0] == 4:
        cell_types = np.full(n_cells, pv.CellType.TETRA)

    elif cells_arr[0] == 6:
        cell_types = np.full(n_cells, pv.CellType.WEDGE)
        
    elif cells_arr[0] == 8:
        cell_types = np.full(n_cells, pv.CellType.HEXAHEDRON)


    # Build mesh
    mesh = pv.UnstructuredGrid(cells_arr, cell_types, all_points)

    # Extract feature edges
    feature_edges = mesh.extract_feature_edges(
        boundary_edges=True,
        feature_edges=True,
        manifold_edges=False,
        non_manifold_edges=False,
        feature_angle=30  # in degrees
    )
    
    ##### Plot #####
    
    # Add the solid mesh, (color='skyblue', lightgray)
    plotter.add_mesh(
        mesh,
        color=color,
        show_edges=False,
        opacity=1.0,
    )

    # Add the feature edges as overlay
    # color='#8B0000'
    plotter.add_mesh(feature_edges, color='black', line_width=line_width)
    

    return


def plot_assembly(assembly, plt_conf):

    # Plot all the blocks
    plotter = pv.Plotter(off_screen=not plt_conf['show'],
                         window_size=plt_conf['window_size'],
                         lighting='light_kit')

    for bl in assembly:
        
        plot_block(
            plotter,
            bl.nodes,
            len(bl.cells), bl.cells_arr,
            color=plt_conf['color'],
            line_width=plt_conf['line_width'],
        )

    plotter.add_axes()  # adds the interactive 3D coordinate axes widget

    set_plotter(plotter, plt_conf)
    
    # Clean up
    plotter.close()   # Important: closes rendering window and releases buffers
    del plotter

    return


def plot_assembly_and_frame(assembly, assembly_frame, plt_conf):

    # Plot all the blocks
    plotter = pv.Plotter(off_screen=not plt_conf['show'],
                         window_size=plt_conf['window_size'],
                         lighting='light_kit')

    for bl in assembly:
        
        plot_block(
            plotter,
            bl.nodes,
            len(bl.cells), bl.cells_arr,
            color=plt_conf['color'], #'orange'
            line_width=plt_conf['line_width'],
        )

    for bl in assembly_frame:
        
        plot_block(
            plotter,
            bl.nodes,
            len(bl.cells), bl.cells_arr,
            color=plt_conf['color_frame'], # 'skyblue'
            line_width=plt_conf['line_width'],
        )

    plotter.add_axes()  # adds the interactive 3D coordinate axes widget

    set_plotter(plotter, plt_conf)

    # Clean up
    plotter.close()   # Important: closes rendering window and releases buffers
    del plotter

    return


########################################################################
# .stl
########################################################################

def output_stl(all_points, n_cells, cells_arr, stl_path="output.stl"):

    cell_types = np.full(n_cells, pv.CellType.HEXAHEDRON)

    # Build mesh
    grid = pv.UnstructuredGrid(cells_arr, cell_types, all_points)

    # Extract surface (triangles)
    surface = grid.extract_surface().triangulate()

    # Export to STL, path="output.stl"
    surface.save(stl_path)

    return

########################################################################
# forces, normal vectors
########################################################################

def plot_block_surfaces(points, n_cells, cells,
                        centroid, face_centers,
                        face_normals, r, M,
                        ids=False,
                        save=False, path='test.png'):

    # Create PyVista mesh
    #mesh = pv.UnstructuredGrid(cells, np.full(n_cells, pv.CellType.TRIANGLE), points)
    mesh = pv.UnstructuredGrid(cells, np.full(n_cells, pv.CellType.QUAD), points)

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
        plotter.add_mesh(pv.Sphere(radius=0.5, center=center), color="black")

    # Plot normals as arrows starting from centroids
    scale = 10.
    for center, normal in zip(face_centers, face_normals):
        if not np.allclose(normal, 0):   # skip zero rows

            # normalize
            normal = normal / np.linalg.norm(normal)
            
            # define start so arrow ends at the centroid
            start = center - normal * scale
            arrow = pv.Arrow(start=start, direction=normal, scale=scale)
            
            plotter.add_mesh(arrow, color="blue")
            
    # Add the center of mass as a sphere
    plotter.add_mesh(pv.Sphere(radius=1.0, center=centroid), color="red", name="center_of_mass")

    # add the interactive 3D coordinate axes widget
    plotter.add_axes()
    
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

    # Clean up
    plotter.close()   # Important: closes rendering window and releases buffers
    del plotter
        
    return


def plot_points_with_directions(points, directions, scale=1.0, arrow_color='red', point_color='blue', point_size=1):
    """
    Plots a set of points with associated direction vectors using PyVista.

    Parameters:
    - points: (N, 3) array-like of point coordinates.
    - directions: (N, 3) array-like of direction vectors at each point.
    - scale: float, scaling factor for the arrows.
    - arrow_color: str or tuple, color of the arrows.
    - point_color: str or tuple, color of the points.
    - point_size: int, size of the points.
    """

    import pyvista as pv


    points = np.array(points)
    directions = np.array(directions)

    # Create a PyVista point cloud
    cloud = pv.PolyData(points)
    
    # Create arrows for each point
    arrows = pv.Arrow(start=np.zeros(3), direction=np.array([1,0,0]))  # template arrow
    arrow_actors = []
    
    # Initialize plotter
    plotter = pv.Plotter()
    
    # Add points
    plotter.add_points(points, color=point_color, point_size=point_size)
    
    # Add arrows for directions
    for pt, dir_vec in zip(points, directions):
        arrow = pv.Arrow(start=pt, direction=dir_vec, scale=scale)
        plotter.add_mesh(arrow, color=arrow_color)
    
    # Show plot
    plotter.show()


# def plot_assembly_lam(assembly,
#                       lam,
#                       save=False,
#                       path='test.png',
#                       cpos=None,
#                       clim=None,
#                       ):

#     import matplotlib.colors as mcolors
    
#     # Define colors
#     #colors = ["white", "yellow", "orange", "red"]
#     colors = ["white", "#40E0D0", "lightgreen", "yellow",  "red"]
#     #colors = [ "#40E0D0", "lightgreen","white", "yellow",  "red"]
    
#     # Create colormap
#     cmap = mcolors.LinearSegmentedColormap.from_list("custom_map", colors)

#     # Plot
#     plotter = pv.Plotter()

#     offset_contact_faces = 0
#     for bl in assembly:

#         cells_idx = bl.data['face_groups']['contact_faces']
#         n_surf = len(cells_idx)
#         nodes_idx = [j for i in cells_idx for j in range(i*5, i*5 + 5)]
#         cells_2D_arr = bl.data['surface'].faces[nodes_idx]
        
#         plot_lam_surfaces(
#             plotter,
#             bl.surface_nodes,
#             n_surf,
#             cells_2D_arr,
#             lam[offset_contact_faces:offset_contact_faces+n_surf],
#             cmap,
#             clim,
#         )

#         offset_contact_faces += n_surf
    
#     # Add small coordinate axes in corner
#     plotter.show_axes()

#     # camaera position
#     if cpos is not None:
#         plotter.camera_position = cpos

#     # Enable parallel (orthographic) projection
#     plotter.enable_parallel_projection()

#     if save:
#         ext = Path(path).suffix.lower()

#         if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
#             plotter.show()
#             plotter.screenshot(path)

#         elif ext == ".html":
#             plotter.export_html(path)
#             plotter.show()
            
#         else:
#             raise ValueError(f"Unsupported extension {ext}. "
#                              "Use an image format or .html")

#     else:
#         plotter.show()

#     # Clean up
#     plotter.close()   # Important: closes rendering window and releases buffers
#     del plotter
    
#     return


# def plot_lam_surfaces(plotter,
#                       points, n_cells, cells_arr,
#                       lam, # 'contact pressure' (lambda)
#                       cmap,
#                       clim,
#                       ):
    
#     # Create PyVista mesh
#     mesh = pv.UnstructuredGrid(cells_arr, np.full(n_cells, pv.CellType.QUAD), points)
    
#     mesh.cell_data['contact force'] = lam
    
#     plotter.add_mesh(
#         mesh,
#         scalars='contact force',
#         cmap=cmap,
#         clim=clim,  # set your colormap limits here
#         show_edges=False,
#         color='skyblue',
#         opacity=1.0,
#         lighting=False
#     )

#     # Extract feature edges (sharp edges, boundaries, non-manifold edges)
#     feature_edges = mesh.extract_feature_edges(
#         boundary_edges=True,      # extract boundary edges
#         feature_edges=True,       # extract sharp edges
#         manifold_edges=False,     # extract manifold edges
#         feature_angle=40          # angle threshold in degrees
#     )

#     plotter.add_mesh(feature_edges, color="black", line_width=2)
    
#     return


def plot_assembly_quantity(assembly, quantity_name, plt_conf):

    '''plots quantity distribution in each block of the assembly'''
    
    import matplotlib.colors as mcolors
    
    # Define colors
    #colors = ["white", "yellow", "orange", "red"]
    colors = ["white", "#40E0D0", "lightgreen", "yellow",  "red"]
    #colors = [ "#40E0D0", "lightgreen","white", "yellow",  "red"]

    # ABAQUS-like color map
    abaqus_colors = [
        "#D90000",   # Red
        "#FF7F00",   # Orange
        "#FFD200",   # Yellow
        "#B4FF00",   # Yellow-Green
        "#00FF00",   # Green
        "#00FFC8",   # Turquoise
        "#00C8FF",   # Light Blue
        "#0064FF",   # Blue
        "#0000FF",   # Deep Blue / Violet
        "#FFFFFF"    # White (max)
    ]

    abaqus_colors_inverted = [
        "#FFFFFF",   # White (max)
        "#0000FF",   # Deep Blue / Violet
        "#0064FF",   # Blue
        "#00C8FF",   # Light Blue
        "#00FFC8",   # Turquoise
        "#00FF00",   # Green
        "#B4FF00",   # Yellow-Green
        "#FFD200",   # Yellow
        "#FF7F00",   # Orange
        "#D90000"    # Red (min)
    ]

    # Create colormap
    #cmap = mcolors.LinearSegmentedColormap.from_list("custom_map", colors)
    cmap = mcolors.LinearSegmentedColormap.from_list("abaqus", abaqus_colors_inverted)

    # Make it discrete with exactly 14 colors
    cmap_n = cmap.resampled(14)

    # colour scale: limits from the config, or (planar config) from a percentile
    # of the values, so that a few peaks do not compress all other colours;
    # values above the limit get the colour of the maximum
    # planar assemblies: plot the contact regions (polygons of the contact
    # elements with their own pressure) instead of the faces, if available
    use_regions = (plt_conf.get('contact_regions', False) and quantity_name == 'Contact pressure'
                   and all('contact_regions' in bl.solutions for bl in assembly))

    clim, above_color = plt_conf['clim'], None
    if clim is None and plt_conf.get('clim_percentile'):
        if use_regions:
            vals = np.concatenate([bl.solutions['contact_regions'][1] for bl in assembly] or [np.zeros(1)])
            vals = vals if len(vals) else np.zeros(1)
        else:
            vals = np.concatenate([np.asarray(bl.solutions[quantity_name], dtype=float).ravel()
                                   for bl in assembly if len(bl.face_groups['contact_faces'])]
                                  or [np.zeros(1)])
        vmax = float(np.percentile(vals, plt_conf['clim_percentile']))
        if vmax > 0 and vmax < vals.max():
            # values above the limit are clamped to the colour of the maximum
            # (no extra colour, no "above" entry in the scalar bar)
            clim = [0., vmax]

    # Plot
    plotter = pv.Plotter(off_screen=not plt_conf['show'], window_size=plt_conf['window_size'])

    offset_contact_faces = 0
    for bl in assembly:
        cells_idx = bl.face_groups['contact_faces']
        n_surf = len(cells_idx)

        # optional: faces without contact (grey, frame blocks in color_frame)
        # and the edges of the block, so that the blocks and the gaps between
        # them stay visible when only parts of the faces are in contact
        if plt_conf.get('show_free_faces', False):
            plot_block_free_faces(plotter, bl, plt_conf)

        if use_regions:
            plot_contact_regions(plotter, bl.solutions['contact_regions'], quantity_name, cmap, clim, above_color)
            continue

        if n_surf == 0:
            # e.g. frame blocks of planar assemblies without contact to the analysed blocks
            continue
        # surface faces are stored as [n, id_1, ..., id_n]: quads (sine,
        # hexagon blocks) or triangles (planar blocks)
        faces = bl.data['surface'].faces
        stride = faces[0] + 1
        nodes_idx = [j for i in cells_idx for j in range(i*stride, i*stride + stride)]
        cells_2D_arr = faces[nodes_idx]
        
        plot_quantity_distr(
            plotter,
            bl.surface_nodes,
            n_surf,
            cells_2D_arr,
            bl.solutions[quantity_name],
            quantity_name,
            cmap,
            clim,
            above_color,
        )

        offset_contact_faces += n_surf
    
    # Add small coordinate axes in corner
    plotter.show_axes()

    set_plotter(plotter, plt_conf)
    
    # Clean up
    plotter.close()   # Important: closes rendering window and releases buffers
    del plotter
    
    return


def sharp_edges(mesh, feature_angle):
    '''
    Boundary and sharp edges of a surface mesh. The triangles of the planar
    block geometries are not consistently ordered (the outward normals of the
    computation are determined separately); without reordering, the seams
    between oppositely ordered coplanar triangles would appear as edges.
    '''
    surf = mesh if isinstance(mesh, pv.PolyData) else mesh.extract_surface()
    surf = surf.compute_normals(consistent_normals=True, auto_orient_normals=False,
                                split_vertices=False, cell_normals=True, point_normals=False)
    return surf.extract_feature_edges(boundary_edges=True, feature_edges=True,
                                      manifold_edges=False, non_manifold_edges=False,
                                      feature_angle=feature_angle)


def plot_contact_regions(plotter, regions, quantity_name, cmap, clim, above_color=None):
    '''
    Contact regions of a block: every polygon (convex, from the intersection of
    two contact faces) coloured with its own pressure. Faces that are only
    partially in contact are not drawn, so the colour does not depend on how
    the triangulation cuts the contact region.
    '''
    polys, values = regions
    if not len(polys):
        return
    pts, cells, vals = [], [], []
    n = 0
    for poly, v in zip(polys, values):
        poly = np.asarray(poly, dtype=float)
        k = len(poly)
        pts.append(poly)
        for t in range(1, k - 1):          # fan triangulation of the convex polygon
            cells.append([3, n, n + t, n + t + 1])
            vals.append(v)
        n += k
    mesh = pv.PolyData(np.vstack(pts), np.hstack(cells).astype(np.int64))
    mesh.cell_data[quantity_name] = np.asarray(vals)
    plotter.add_mesh(mesh, scalars=quantity_name, cmap=cmap, clim=clim, above_color=above_color,
                     show_edges=False, opacity=1.0, lighting=False)


def plot_block_free_faces(plotter, bl, plt_conf):
    '''faces of a block without contact and the edges of the block'''

    faces = np.asarray(bl.data['surface'].faces)
    stride = faces[0] + 1
    n_faces = len(faces) // stride
    contact = set(np.asarray(bl.face_groups['contact_faces']).tolist())
    free = [i for i in range(n_faces) if i not in contact]

    is_frame = getattr(bl, 'is_frame', False)
    color = plt_conf.get('color_frame', 'lightgrey') if is_frame else plt_conf.get('color_free', 'lightgrey')

    if free:
        idx = [j for i in free for j in range(i*stride, i*stride + stride)]
        mesh = pv.PolyData(bl.surface_nodes, faces[idx])
        plotter.add_mesh(mesh, color=color, opacity=plt_conf.get('opacity_free', 1.0),
                         show_edges=False, lighting=True)

    # edges of the block (sharp edges of the whole surface)
    full = pv.PolyData(bl.surface_nodes, faces)
    edges = sharp_edges(full, feature_angle=20)
    plotter.add_mesh(edges, color='black', line_width=plt_conf.get('line_width', 2))

    return


def plot_quantity_distr(plotter,
                        points, n_cells, cells_arr,
                        quantity, # 'contact pressure' (lambda)
                        quantity_name,
                        cmap,
                        clim,
                        above_color=None,
                        ):
    
    # Create PyVista mesh
    if cells_arr[0] == 4:
        mesh = pv.UnstructuredGrid(cells_arr, np.full(n_cells, pv.CellType.QUAD), points)
    elif cells_arr[0] == 3: 
        mesh = pv.UnstructuredGrid(cells_arr, np.full(n_cells, pv.CellType.TRIANGLE), points)
    else:
        raise ValueError(f"Unsupported cell type with {cells_arr[0]} nodes. "
                         "Expected 3 (triangles) or 4 (quads).")
    
    mesh.cell_data[quantity_name] = quantity
    
    plotter.add_mesh(
        mesh,
        scalars=quantity_name,
        cmap=cmap,
        clim=clim,  # set your colormap limits here
        above_color=above_color,  # values above clim (only with clim_percentile)
        show_edges=False,
        color='skyblue',
        opacity=1.0,
        lighting=False
    )

    # Extract feature edges (sharp edges, boundaries, non-manifold edges)
    feature_edges = sharp_edges(mesh, feature_angle=40)

    plotter.add_mesh(feature_edges, color="black", line_width=2)
    
    return
