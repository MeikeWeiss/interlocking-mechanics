"""
Driver for the MBD analysis of planar assemblies.

In contrast to the tubular assemblies (src/blocks/run_mbd.py) the face groups
of a planar block depend on its position in the assembly (e.g. only the top
row of a wall is loaded). Therefore the blocks are prepared *after* they are
assembled, block by block.

Boundary conditions (bvp_type):
    'ceiling':    load q on the top faces (highest z), bottom faces free
    'wall_left':  load q from above on the top row and on the left end face
                  of the top row
    'wall_right': load q from above on the top row and on the right end face
                  of the top row

Options in assembly_config:
    'contact_method': 'intersection' (default) contact regions from the exact
                      intersection of the surface triangles (works for
                      non-matching triangulations, see contacts.py), or
                      'matching' (original method: faces with coinciding
                      centres, results identical to earlier versions)
    'support':        'implicit' (default): faces without any contact act as
                      rigid supports (frame); 'frame': the frame blocks are
                      fixed, faces are supported only where they touch a
                      frame block, all other faces without contact are free.
                      Only with contact_method 'intersection'.
    'frame_blocks':   'boundary' (default, blocks with fewer neighbours than
                      the interior blocks) or a list of block indices
    'objective':      'force' (default, min sum lambda^2 as in the paper) or
                      'pressure' (min sum lambda^2/A = integral of p^2,
                      independent of the size of the contact elements)
"""

import numpy as np
import scipy.sparse as sp
import cvxpy as cp

from src.engine.mbd import (compute_contact_pressure, check_kinematic_feasibility,
                            kinematic_feasibility)
from src.engine.util import start_time, end_time
from src.blocks.block_mbd import get_block_matrices
from src.blocks.run_mbd import categorize_face_groups, plot_and_save_pc
from src.blocks.planar_block.block import get_blocks, group_faces, group_faces_wall
from src.blocks.planar_block.assembly import get_assembly
from src.blocks.planar_block.contacts import (find_contact_elements, contact_coverage,
                                              coverage_report, assemble_contact_jacobian)

WALL_BVPS = ('wall_left', 'wall_right')

DEFAULT_OPTIONS = {
    'contact_method': 'intersection',
    'support': 'implicit',
    'frame_blocks': 'boundary',
    'objective': 'force',
}


def get_options(assembly_config):
    opts = {k: assembly_config.get(k, v) for k, v in DEFAULT_OPTIONS.items()}
    if opts['contact_method'] not in ('intersection', 'matching'):
        raise ValueError(f"Unknown contact_method: {opts['contact_method']}")
    if opts['support'] not in ('implicit', 'frame'):
        raise ValueError(f"Unknown support: {opts['support']}")
    if opts['objective'] not in ('force', 'pressure'):
        raise ValueError(f"Unknown objective: {opts['objective']}")
    if opts['contact_method'] == 'matching' and (opts['support'] != 'implicit' or opts['objective'] != 'force'):
        raise ValueError("contact_method 'matching' supports only support='implicit' and objective='force'")
    return opts


def build_assembly(block_config, assembly_config, bvp_config, bvp_type):
    '''
    Creates the reference block, the assembly and prepares all blocks
    for the MBD computation.

    bvp_config: configuration of the boundary value problem, e.g.
                blocks_bvp_config['ceiling'] from scripts/planar/config.py
    '''
    blocks = get_blocks(block_config, assembly_config)
    assembly_all = get_assembly(blocks, assembly_config, block_config)
    setup_blocks_planar(assembly_all['together'], bvp_config, bvp_type)

    return assembly_all


def setup_blocks_planar(assembly, bvp_config, bvp_type):
    '''
    Groups the faces of the placed blocks and computes the block matrices.
    '''
    block_config = bvp_config['block']

    if bvp_type in WALL_BVPS:
        extent = assembly_extent(assembly)

    for block in assembly:

        if bvp_type in WALL_BVPS:
            group_faces_wall(block, extent)
        else:
            group_faces(block)

        block.face_groups = categorize_face_groups(
            block.surf_filter,
            n_faces=len(block.cells_2D),
            f_ext_surf=block_config['f_ext_surf'],
            free_surf=block_config['free_surf'],
        )

        get_block_matrices(block, block_config['q'])

    return assembly


def assembly_extent(assembly):
    '''bounding box of the assembly in the x-y plane'''
    nodes = np.vstack([bl.nodes for bl in assembly])
    return {
        'x_min': nodes[:, 0].min(),
        'x_max': nodes[:, 0].max(),
        'y_min': nodes[:, 1].min(),
        'y_max': nodes[:, 1].max(),
    }


############################################################################
# contacts
############################################################################
def neighbours(n_blocks, elements):
    '''set of contact neighbours of every block'''
    nb = [set() for _ in range(n_blocks)]
    for a, b in zip(elements['a'], elements['b']):
        nb[a].add(b)
        nb[b].add(a)
    return nb


def select_frame(n_blocks, elements, frame_blocks='boundary'):
    '''indices of the frame blocks'''
    if isinstance(frame_blocks, str):
        if frame_blocks != 'boundary':
            raise ValueError(f"Unknown frame_blocks: {frame_blocks}")
        deg = np.array([len(s) for s in neighbours(n_blocks, elements)])
        return sorted(np.where(deg < deg.max())[0].tolist())
    return sorted(int(i) for i in frame_blocks)


def prepare_contacts(blocks, opts):
    '''
    Contact elements, supports and frame of the assembly.

    Returns a dict with the elements, the coverage of the faces, the indices of
    the active (analysed) and frame blocks, the support elements and a report.
    '''
    elements = find_contact_elements(blocks)
    coverage = contact_coverage(blocks, elements)

    if opts['support'] == 'frame':
        frame = select_frame(len(blocks), elements, opts['frame_blocks'])
    else:
        frame = []
    frame_set = set(frame)
    active = [i for i in range(len(blocks)) if i not in frame_set]
    if not active:
        raise ValueError("All blocks are frame blocks: the assembly is too small.")

    # supports: faces of active blocks without any contact (implicit frame)
    supports = []
    if opts['support'] == 'implicit':
        for ib in active:
            bl = blocks[ib]
            cf = np.asarray(bl.face_groups['contact_faces'], dtype=int)
            for f in cf[coverage[ib] <= 1e-9]:
                supports.append((ib, f, bl.face_areas[f], bl.face_centers[f], bl.face_normals[f]))

    report = coverage_report(blocks, elements, coverage, frame)
    report.update({
        'support': opts['support'],
        'n_frame_blocks': len(frame),
        'n_active_blocks': len(active),
        'n_support_faces': len(supports),
    })

    return {
        'elements': elements, 'coverage': coverage, 'frame': frame,
        'active': active, 'supports': supports, 'report': report,
    }


def print_contact_report(report):
    print("Contact report:")
    for k, v in report.items():
        print(f"  {k}: {v}")
    if not report['contact_boundary_resolved']:
        print(f"  -> {report['n_faces_partial']} faces are only partially in contact "
              "(the boundary of a contact region crosses the triangle). The contact "
              "area is exact, but the pressure is averaged over these faces: refine the mesh.")
    if report['n_elements'] > report['n_matched_elements']:
        print("  -> the triangulations of neighbouring blocks do not match; "
              "objective='pressure' gives mesh independent results.")


############################################################################
# force equilibrium with contact elements
############################################################################
def min_norm_solution(J, f_ext, verbose=False):
    '''
    min |x|^2  s.t.  J x + f_ext = 0, x >= 0  (same problem and solver
    settings as find_exact_lambda_cvxpy). Returns (x, status); x is None if
    the problem is infeasible or the solver fails.
    '''
    x = cp.Variable(J.shape[1], nonneg=True)
    prob = cp.Problem(cp.Minimize(cp.sum_squares(x)), [J @ x == -f_ext])
    try:
        prob.solve(solver=cp.OSQP, max_iter=80000, eps_abs=1e-9, eps_rel=1e-9, verbose=verbose)
    except cp.error.SolverError as exc:
        return None, f"solver_error: {exc}"
    if x.value is None:
        return None, prob.status
    return x.value, prob.status


############################################################################
############################################################################
def solve_contacts(blocks, contacts, opts, info, tol_res=1e-6):
    '''
    Solves the static problem for the active blocks and stores the contact
    force 'lam' and the contact pressure 'Contact pressure' (force per face
    area) for the faces in contact of every block.
    '''
    t = info['t_cpu']
    el = contacts['elements']

    start_time(t, 'assembly')
    J, f_ext, columns = assemble_contact_jacobian(blocks, contacts['active'], el, contacts['supports'])
    end_time(t, 'assembly')

    area = np.array([el['area'][k] if kind == 'el' else contacts['supports'][k][2]
                     for kind, k in columns])

    # objective: 'force' -> min |lam|^2, 'pressure' -> min sum lam^2/A
    w = np.sqrt(area) if opts['objective'] == 'pressure' else np.ones(len(area))

    start_time(t, 'solving')
    mu, status = min_norm_solution((J @ sp.diags(w)).tocsc(), f_ext)
    end_time(t, 'solving')
    if mu is None:
        # no admissible contact forces (e.g. too few contact points per interface)
        lam = np.zeros(J.shape[1])
    else:
        lam = w * mu
    res_norm = np.linalg.norm(J @ lam + f_ext)

    res_rel = res_norm / np.linalg.norm(f_ext)
    info['res_norm'] = res_norm
    info['res_rel'] = res_rel
    info['status'] = status
    info['equilibrium'] = bool(res_rel < tol_res and status == "optimal")
    info['contacts'] = contacts['report']

    print(f"solving: {t['dt_real']['solving']}")
    print("Residual relativ:", res_rel)
    print("Solver status:", status)
    print("Equilibrium achieved!" if info['equilibrium'] else
          "No equilibrium found (residual too large or solver failed)")

    # forces per face
    force = [dict() for _ in blocks]
    for (kind, k), l in zip(columns, lam):
        if kind == 'el':
            for side, fs in (('a', 'fa'), ('b', 'fb')):
                ib, f = el[side][k], el[fs][k]
                force[ib][f] = force[ib].get(f, 0.) + l
        else:
            ib, f = contacts['supports'][k][:2]
            force[ib][f] = force[ib].get(f, 0.) + l

    # faces in contact (incl. supports); faces without contact become free
    for ib, bl in enumerate(blocks):
        cf = np.asarray(bl.face_groups['contact_faces'], dtype=int)
        in_contact = np.array([f in force[ib] for f in cf], dtype=bool)
        bl.face_groups['free_faces'] = np.concatenate([bl.face_groups['free_faces'], cf[~in_contact]]).astype(int)
        bl.face_groups['contact_faces'] = cf[in_contact]
        lam_f = np.array([force[ib][f] for f in cf[in_contact]])
        bl.solutions['lam'] = lam_f
        bl.solutions['Contact pressure'] = lam_f / bl.face_areas[cf[in_contact]] if len(lam_f) else lam_f

    return lam


############################################################################
# force equilibrium
############################################################################
def analyse_contact_pressure(block_config, assembly_config, bvp_config, bvp_type,
                             plot_config, out_config, info):

    opts = get_options(assembly_config)
    assembly_all = build_assembly(block_config, assembly_config, bvp_config, bvp_type)
    info['options'] = opts

    if opts['contact_method'] == 'matching':
        compute_contact_pressure(assembly_all['assembly'], info)
        info['equilibrium'] = bool(info['res_rel'] < 1e-6 and info['status'] == 'optimal')
    else:
        blocks = assembly_all['together']
        contacts = prepare_contacts(blocks, opts)
        print_contact_report(contacts['report'])
        solve_contacts(blocks, contacts, opts, info)

        # results (snaps) only for the analysed blocks, the frame separately
        assembly_all['assembly'] = [blocks[i] for i in contacts['active']]
        assembly_all['frame'] = [blocks[i] for i in contacts['frame']]
        info['frame_blocks'] = contacts['frame']

    plot_and_save_pc(assembly_all, plot_config, out_config, info)

    return assembly_all


############################################################################
# kinematic feasibility
############################################################################
def test_interlocking(block_config, assembly_config, bvp_config, bvp_type, info):

    opts = get_options(assembly_config)
    assembly_all = build_assembly(block_config, assembly_config, bvp_config, bvp_type)
    info['options'] = opts

    if opts['contact_method'] == 'matching':
        # no frame blocks: the frame is represented by the faces without contact
        result = check_kinematic_feasibility(
            assembly_all['together'], info, assembly_config['lp_method'], n_fixed=0
        )
    else:
        blocks = assembly_all['together']
        contacts = prepare_contacts(blocks, opts)
        print_contact_report(contacts['report'])
        # all blocks, the fixed frame blocks at the end
        order = contacts['active'] + contacts['frame']
        # constraints at the vertices of the contact polygons: exact first-order
        # test, independent of the refinement
        J, f_ext, _ = assemble_contact_jacobian(blocks, order, contacts['elements'],
                                                contacts['supports'], points='vertices')
        result = kinematic_feasibility(J, f_ext, assembly_config['lp_method'],
                                       n_fixed=len(contacts['frame']))
        info['contacts'] = contacts['report']

    info['interlocking'] = {k: v for k, v in result.items() if k != 'dq'}

    return assembly_all, result
