"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-08-30
Last Modified: ?

License: MIT

Reference:
"""

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.sparse.linalg import lsqr

from scipy.optimize import nnls
from scipy.optimize import lsq_linear
from scipy.spatial import cKDTree
from scipy.sparse import csc_matrix, lil_matrix, csr_matrix, block_diag, tril
import matplotlib.pyplot as plt
import cvxpy as cp


from src.engine.util import start_time, end_time

############################################################################
# Static feasibility
############################################################################
def compute_contact_pressure(assembly, info):

    # compute solutions
    lam_full = compute_lam(assembly, info)
    solutions = {
        'lam': lam_full,
    }
    split_solutions_by_blocks(solutions, assembly)

    # compute contact pressure: p_c = F/A
    compute_pc(assembly)

    return


def split_solutions_by_blocks(solutions, assembly):

    for sol_name, sol in solutions.items():

        offset_contact_faces = 0

        for bl in assembly:
            
            cells_idx = bl.face_groups['contact_faces']
            n_surf = len(cells_idx)

            bl.solutions[sol_name] = sol[offset_contact_faces:offset_contact_faces+n_surf]
            
            offset_contact_faces += n_surf
            
    return


def compute_pc(assembly):
    '''computes contact pressure. lam has to be computed first'''
    for bl in assembly:
        lam = bl.solutions['lam']
        
        A = bl.face_areas[bl.face_groups['contact_faces']]
        bl.solutions['Contact pressure'] = lam / A
    
    return


def compute_lam( assembly, info, tol_res=1e-6 ):

    t = info['t_cpu']
    
    # assemble matrices
    G, f_ext, to_keep, rows, cols, n_all_cols = assemble_J_fext(assembly, t, show_J=False)        
        
    # solve
    start_time(t, 'solving')
    #lam, residual, res_norm, status = solve_mbs_active(G, f_ext)
    lam, residual, res_norm, status = find_exact_lambda_cvxpy(G, f_ext)
    #lam, residual, res_norm, status = find_exact_lambda_gpu(G, -f_ext)
    end_time(t, 'solving')

    res_rel = res_norm / np.linalg.norm(f_ext)
    info['res_norm'] = res_norm
    info['res_rel'] = res_rel
    info['status'] = status

    # print solver info
    print(f"solving: {t['dt_real']['solving']}")
    print("Residual norm:", res_norm)
    print("Residual relativ:", res_rel)
    print("Solver status:", status)
    if res_rel < tol_res and status == "optimal":
        print("Equilibrium achieved!")
    else:
        print("No equilibrium found (residual too large or solver failed)")
    
    lam_full = expand_solution(lam, to_keep, rows, cols, n_all_cols)

    return lam_full

############################################################################
# Kinematic feasibility
############################################################################
def check_kinematic_feasibility( assembly, info, lp_method='dof', n_fixed=8 ):
    '''
    n_fixed: number of fixed bodies at the end of 'assembly' (frame blocks).
             Use 0 if the assembly contains no frame blocks (e.g. planar
             assemblies, where unpaired contact faces act as the frame).
    '''

    t = info['t_cpu']

    ### build contact Jacobian ###
    G, f_ext, _, _, _, _ = assemble_J_fext(assembly, t, show_J=False)

    return kinematic_feasibility(G, f_ext, lp_method, n_fixed)


def kinematic_feasibility(G, f_ext, lp_method='dof', n_fixed=8):
    '''
    Kinematic feasibility for a given contact Jacobian G and load vector f_ext.
    The last n_fixed bodies are fixed.

    Returns a dict with 'motion' (bool or None), 'dq' and, for
    'mechanism_test', 'gamma' (min, max) of the mechanism test.
    '''

    result = {'lp_method': lp_method, 'n_fixed': n_fixed, 'gamma': None}

    ### check mobility ###
    if lp_method == 'dof':
        motion, dq = solve_lp_dof(G.T, n_fixed)
    elif lp_method == 'wang2018':
        motion, dq, s, status = wang_interlocking_test(G.T, n_fixed)
    elif lp_method == 'norm2':
        motion, dq, status = solve_lp_norm2(G.T, n_fixed)
    elif lp_method in ('cone', 'cone_mechanism'):
        motion, dq, cone_info, status = cone_interlocking_test(G.T, n_fixed)
        result.update(cone_info)
        if dq is None:
            print(f"Interlocking test failed (solver status: {status})")
        elif not motion:
            print("No mechanism (interlocked system)")
        elif lp_method == 'cone_mechanism':
            result['gamma'] = mechanism_test(G, f_ext, n_fixed)
    elif lp_method == 'mechanism_test':
        motion, dq, s, status = wang_interlocking_test(G.T, n_fixed)
        if dq is None:
            print(f"Interlocking test failed (solver status: {status})")
        elif np.linalg.norm(dq) < 1e-9:
            print("No mechanism (interlocked system)")
        else:
            result['gamma'] = mechanism_test(G, f_ext, n_fixed)
    else:
        raise ValueError(f"Unknown lp_method: {lp_method}")

    if lp_method in ('dof', 'cone', 'cone_mechanism'):
        result['motion'] = bool(motion)  # dq is None if there is no motion (dof)
    else:
        result['motion'] = None if dq is None else bool(np.linalg.norm(dq) >= 1e-9)
    result['dq'] = dq

    return result

############################################################################
# solver
############################################################################

def solve_mbs_active(J, f_ext, tol=1e-9, max_iter=10, solver=cp.OSQP): # OSQP
    """
    Active-set solver for massless multi-body contact dynamics:
        J @ λ + f_ext ≈ 0
        λ >= 0
        automatically selects active contacts
    
    Args:
        J (ndarray): Contact Jacobian (m x n), maps contact forces to generalized forces
        f_ext (ndarray): External generalized forces (length m)
        tol (float): Threshold for treating λ or residual as zero
        max_iter (int): Maximum number of active-set iterations
        solver: cvxpy solver
    
    Returns:
        lam_full (ndarray): Contact forces (length n)
        residual (ndarray): Residual vector r = J @ λ + f_ext
        res_norm (float): Norm of the residual ||r||
        status (str): Solver status
    """
    n = J.shape[1]
    active_set = np.ones(n, dtype=bool)  # start with all contacts active
    lam_full = np.zeros(n)
    
    for it in range(max_iter):
        if not np.any(active_set):
            break  # no active contacts left
        
        J_active = J[:, active_set]
        n_active = J_active.shape[1]
        lam_var = cp.Variable(n_active, nonneg=True)
        
        # Correct residual: map contact forces to generalized forces
        residual_expr = J_active @ lam_var + f_ext
        objective = cp.Minimize(cp.sum_squares(residual_expr))
        # eps, alpha = 1e-8, 1e-6
        # objective = cp.Minimize(cp.sum_squares(J_active @ lam_var + f_ext) +
        #                         eps * cp.sum_squares(lam_var) +
        #                         alpha * cp.norm1(lam_var))
        
        prob = cp.Problem(objective)
        #prob.solve(solver=solver)
        prob.solve(solver=solver, max_iter=20000, eps_abs=1e-9, eps_rel=1e-9, verbose=True)
        
        lam_active = lam_var.value
        # Treat very small or negative λ as inactive
        lam_active[lam_active < tol] = 0.0
        
        # Update full λ
        lam_full[active_set] = lam_active
        
        # Determine new active set
        new_active_set = lam_full > tol
        
        # Check for convergence
        if np.array_equal(new_active_set, active_set):
            break
        
        active_set = new_active_set
    
    # Final residual using correct mapping
    residual = J @ lam_full + f_ext
    res_norm = np.linalg.norm(residual)
    
    return lam_full, residual, res_norm, prob.status


def solve_mbs(J, f_ext, phi=None, tol=1e-9):
    """
    Solve a massless multi-body contact problem:
        J.T @ λ + f_ext = 0
        λ >= 0
        optional: λ_i * φ_i = 0  (complementarity)
    
    Args:
        J (ndarray): Contact Jacobian (m x n)
        f_ext (ndarray): External forces (length m)
        phi (ndarray or None): Gap values (length n), optional
        tol (float): Threshold to treat small values as zero
    
    Returns:
        lam (ndarray): Contact forces (length n)
        status (str): Problem status ('optimal', etc.)
    """
    n = J.shape[1]  # number of contact forces
    lam = cp.Variable(n, nonneg=True)
    
    # Objective: minimize residual of force balance
    #objective = cp.Minimize(cp.sum_squares(J.T @ lam + f_ext))
    objective = cp.Minimize(cp.sum_squares(J @ lam + f_ext))
    
    constraints = [lam >= 0]
    
    # Optional complementarity with gap values
    if phi is not None:
        phi = np.asarray(phi).flatten()
        constraints += [cp.multiply(lam, phi) == 0]
    
    prob = cp.Problem(objective, constraints)
    prob.solve(solver=cp.OSQP) # SCS, ECOS, OSQP can work
    
    lam_val = lam.value
    # Clean up small numerical noise
    lam_val[np.abs(lam_val) < tol] = 0.0

    print(lam_val)
    print(prob.status)

    # Compute residual
    residual = J @ lam_val + f_ext   # shape (2,)
    print("Residual norm:", np.linalg.norm(residual))
    
    return lam_val


def find_exact_lambda_gpu(J, f_ext, solver=cp.SCS):
    
    k = J.shape[1]
    lam = cp.Variable(k, nonneg=True)
    constraints = [J @ lam == -f_ext]
    obj = cp.Minimize(cp.sum_squares(lam))
    prob = cp.Problem(obj, constraints)
    
    # Solve the problem with the GPU direct solver
    prob.solve(solver=cp.SCS, gpu=True, use_indirect=False, cudss=True)
    
    residual = J @ lam.value + f_ext
    res_norm = np.linalg.norm(residual)
    
    return lam.value, residual, res_norm, prob.status


def find_exact_lambda_cvxpy(J, f_ext, solver=cp.OSQP):
    # J_active: m x k (scipy.sparse or dense), f_ext: length m
    k = J.shape[1]
    lam = cp.Variable(k, nonneg=True)
    constraints = [J @ lam == -f_ext]   # exact equality
    obj = cp.Minimize(cp.sum_squares(lam))    # choose minimum-norm solution
    prob = cp.Problem(obj, constraints)
    prob.solve(solver=solver, max_iter=80000, eps_abs=1e-9, eps_rel=1e-9, verbose=True)

    # Final residual using correct mapping
    residual = J @ lam.value + f_ext
    res_norm = np.linalg.norm(residual)
    
    return lam.value, residual, res_norm,  prob.status


############################################################################
# Searching
############################################################################

def find_neighbors(system_centroids):

    '''system_centroids = face centers'''
    
    tree = cKDTree(system_centroids)

    # Small radius where some points may have no neighbors
    radius = 0.01
    
    # Find neighbors (centroids) within radius
    neighbors = tree.query_ball_point(system_centroids, r=radius)
    
    # Remove self from each list
    for i, indices in enumerate(neighbors):
        neighbors[i] = [j for j in indices if j != i]
        
    return neighbors


def get_edges(assembly, show_C=False):
    
    #contact_face_centers = np.vstack([bl.face_centers[6:,:] for bl in assembly])
    contact_face_centers = np.vstack([
        bl.face_centers[
         bl.face_groups['contact_faces'],:] for bl in assembly
    ])
    
    neighbors = find_neighbors(contact_face_centers).tolist()
    
    # contact pairs matrix
    n_faces = contact_face_centers.shape[0]
    C = lil_matrix((n_faces, n_faces))
    for surf_id, pair in enumerate(neighbors):
        C[surf_id, pair] = 1

    # convert to CSR (or any sparse format)
    C_csr = C.tocsr()
    
    # Lower triangular excluding diagonal
    C_lower = tril(C_csr, k=-1)
    
    # plot contact pairs matrix
    if show_C:
        plt.spy(C_lower, markersize=10)
        plt.title("Sparse matrix pattern")
        plt.show()

    return C_lower


############################################################################
# Assembler
############################################################################

def assemble_J_fext(assembly, t=None, show_J=False):

    C_lower = get_edges(assembly)
    all_cols = range(C_lower.shape[0])
    
    # Extract mapping from lower-triangular contacts
    rows, cols = C_lower.nonzero()

    to_keep = [x for x in all_cols if x not in rows]
    
    f_ext = np.concatenate([bl.p_b for bl in assembly])
    
    J = block_diag([bl.A_b for bl in assembly], format='lil' )

    start_time(t, 'assembly')    
    # for i, j in zip(rows, cols):
    #     J[:, j] += J[:, i]   # accumulate i into j

    # J = J[:, to_keep]
    
    n = J.shape[1]
    M = sp.eye(n, format="lil")  # identity
    
    # For each (i → j), add column i's contribution into column j
    for i, j in zip(rows, cols):
        M[i, j] = 1
        
    # Now apply transformation once
    J = J @ M
    J = J[:, to_keep]

    end_time(t, 'assembly')
    print(f"assembly: {t['dt_real']['assembly']}")

    if show_J:
        plt.spy(J, markersize=5)
        plt.title("Sparse matrix pattern")
        plt.show()

    return J, f_ext, to_keep, rows, cols, len(all_cols)


############################################################################
# Full soulution
############################################################################

def expand_solution(x_reduced, to_keep, rows, cols, n_all):
    """
    Expand reduced solution back to full size.
    
    x_reduced : np.ndarray
        Solution in reduced space.
    to_keep : list[int]
        Original column indices kept.
    rows, cols : np.ndarray
        Contact pairs (i,j), where i merged into j.
    n_all : int
        Total number of original columns.
    """
    # start with zeros
    x_full = np.zeros(n_all)

    # put back kept entries
    for new_idx, old_idx in enumerate(to_keep):
        x_full[old_idx] = x_reduced[new_idx]

    # assign merged entries
    for i, j in zip(rows, cols):
        x_full[i] = x_full[j]

    return x_full


############################################################################
# rank, nullity, nullspace
############################################################################

def matrix_analysis(G, tol=1e-16):
    A = G.toarray()   # convert sparse → dense

    U, S, Vt = np.linalg.svd(A.T, full_matrices=False)
    print(U.shape, Vt.shape)
    rank = np.sum(S > tol)
    nullity = A.shape[1] - rank
    nullspace = Vt.T[:,rank:]

    print(f"rank: {rank}, m: {A.shape[0]}")
    print("nullity:", nullity)
    print("nullspace basis:\n", nullspace)
    
    print("verification:\n", G @ nullspace)

    return rank, nullity, nullspace


def sparse_matrix_analysis(G, tol=1e-10, max_sv=None):
    """
    Compute rank, nullity, and nullspace basis of a sparse matrix G.

    Parameters
    ----------
    G : scipy.sparse matrix (m x n)
    tol : float
        Singular value tolerance for determining rank.
    max_sv : int or None
        Number of singular values to compute. If None, compute min(m,n)-1.

    Returns
    -------
    rank : int
    nullity : int
    nullspace : ndarray (n x nullity)
        Columns form a basis of the nullspace.
    """

    if not sp.issparse(G):
        raise ValueError("G must be a scipy sparse matrix")

    m, n = G.shape

    # number of singular values to compute
    if max_sv is None:
        k = min(m, n) - 1
    else:
        k = min(max_sv, min(m, n) - 1)

    # compute smallest singular values/vectors
    U, S, Vt = spla.svds(G, k=k)

    # sort singular values
    idx = np.argsort(S)
    S = S[idx]
    Vt = Vt[idx]

    # determine rank
    rank = np.sum(S > tol)

    # nullity
    nullity = n - rank

    # nullspace basis
    null_mask = S <= tol
    nullspace = Vt[null_mask].T

    print(f"rank: {rank}, m: {m}")
    print("nullity:", nullity)
    print("nullspace basis:\n", nullspace)
    
    print("verification:\n", G @ nullspace)

    return rank, nullity, nullspace

############################################################################
# Mobility / Kinematic Feasibility
############################################################################

def fixed_dofs_zero(Y, n_fixed, dof_per_body=6):
    '''
    Constraints fixing the DOFs of the last n_fixed bodies.
    Returns an empty list for n_fixed = 0 (note: Y[-0:] would be all of Y).
    '''
    if n_fixed <= 0:
        return []
    return [Y[-dof_per_body*n_fixed:] == 0]


def solve_lp_norm2(B, n_fixed, dof_per_body=6, solver="SCS"):
    """
    Detect feasible motion with the last n_fixed bodies fixed (Y_n = 0).
    """
    # Variables
    n = B.shape[1]
    Y = cp.Variable(n)
    
    # Constraints
    constraints = [
        *fixed_dofs_zero(Y, n_fixed, dof_per_body),  # fixed bodies
        B @ Y >= 0.,                        # non-penetration
        cp.norm2(Y) <= 1.0,  # bound to prevent unbounded solution
    ]
    
    # Objective: maximize sum of some entries in Y to push away from zero
    # Here we just maximize the sum of all free DOFs
    free_idx = np.arange(n - dof_per_body*n_fixed)
    objective = cp.Maximize(cp.sum(Y[free_idx]))
    
    # Problem
    prob = cp.Problem(objective, constraints)
    prob.solve(solver=solver, eps=1e-12, max_iters=100000, verbose=True)

    tol = 1e-9
    if np.linalg.norm(Y.value) < tol:
        motion = False
    else:
        motion = True
        
    return motion, Y.value, prob.status


def solve_lp_dof(B, n_fixed, dof_per_body=6):

    n = B.shape[1]
    fixed = dof_per_body * n_fixed
    free = n - fixed
    
    for i in range(free):
        
        Y = cp.Variable(n)

        constraints = [
            B @ Y >= 0,
            *fixed_dofs_zero(Y, n_fixed, dof_per_body),
            Y[i] == 1
        ]

        prob = cp.Problem(cp.Minimize(0), constraints)

        prob.solve(solver=cp.ECOS)

        if prob.status == cp.OPTIMAL:

            return True, Y.value

        # try negative direction
        constraints[-1] = (Y[i] == -1)

        prob = cp.Problem(cp.Minimize(0), constraints)
        prob.solve(solver=cp.ECOS)

        if prob.status == cp.OPTIMAL:
            return True, Y.value
                
    return False, None



def wang_interlocking_test(B, n_fixed=1, dof_per_body=6, solver="CLARABEL", tol=1e-15):
    """
    Interlocking detection using Wang et al. 2018 LP formulation.

    maximize     s
    subject to   B Y >= s
                 Y_fixed = 0
                 -1 <= Y <= 1

    Parameters
    ----------
    B : ndarray (m, n)
        Contact constraint matrix
    n_fixed : int
        Number of bodies fixed (at end of vector)
    dof_per_body : int
        DOFs per body
    solver : str
        CVXPY solver

    Returns
    -------
    motion_exists : bool
    Y : ndarray
        velocity vector
    s : float
        separation margin
    status : str
    """

    m, n = B.shape
    
    fixed_dofs = n_fixed * dof_per_body

    Y = cp.Variable(n)
    s = cp.Variable()

    constraints = [
        B @ Y >= s,
        *fixed_dofs_zero(Y, n_fixed, dof_per_body),
        Y <= 1,
        Y >= -1
    ]

    prob = cp.Problem(cp.Maximize(s), constraints)
    prob.solve(solver=solver, tol_gap_abs=tol, tol_gap_rel=tol)

    if prob.status not in ["optimal", "optimal_inaccurate"]:
        return False, None, None, prob.status

    norm_Y = np.linalg.norm(Y.value)
    tol_val = 1e-9
    motion_exists = (
        s.value is not None
        and s.value >= -tol_val
        and np.linalg.norm(Y.value) > tol_val
    )
    print(f"motion exists: {motion_exists}")
    print(f"||dq||: {norm_Y}")
    print(f"s: {s.value}")
    
    return motion_exists, Y.value, s.value, prob.status


def cone_interlocking_test(B, n_fixed=1, dof_per_body=6, tol=1e-8):
    """
    Complete first-order interlocking test for the cone of admissible motions

        K = { dq : B dq >= 0, dq_fixed = 0 },   B = G^T.

    K = {0} (interlocked to first order) if and only if
      1. B restricted to the free DOFs has a trivial nullspace (no motion with
         zero normal velocity at all contacts, e.g. bidirectional sliding), and
      2. the LP  max 1^T (B dq)  s.t.  0 <= B dq <= 1, -1 <= dq <= 1
         has the optimal value 0 (no motion that opens a contact).

    Note: the margin formulation (wang_interlocking_test) misses motions
    without separation, and the LP max 1^T s, -s <= dq <= s, 0 <= s <= 1 is
    degenerate (s = 1 is feasible for dq = 0).

    Returns motion_exists, dq, info (dict: nullity, lp_value), status
    """
    B = sp.csr_matrix(B)
    m, n = B.shape
    n_free = n - dof_per_body * max(n_fixed, 0)
    Bf = B[:, :n_free]

    # 1. nullspace of the free part (via the small Gram matrix)
    gram = (Bf.T @ Bf).toarray()
    w, V = np.linalg.eigh(gram)
    sv = np.sqrt(np.clip(w, 0., None))
    null = sv <= tol * max(sv.max(), 1.)
    nullity = int(null.sum())

    # 2. motions that open contacts
    x = cp.Variable(n_free)
    g = Bf @ x
    prob = cp.Problem(cp.Maximize(cp.sum(g)), [g >= 0, g <= 1, x <= 1, x >= -1])
    # CLARABEL fails for some degenerate LPs (e.g. starfish with d = 0): then
    # the LP is solved with HiGHS (SCIPY), which is a simplex/IPM LP solver
    for solver in (cp.CLARABEL, cp.SCIPY):
        try:
            prob.solve(solver=solver)
            break
        except cp.error.SolverError as exc:
            print(f"cone test: solver {solver} failed ({exc}), trying the next one")
    if prob.status not in ["optimal", "optimal_inaccurate"]:
        return False, None, {'nullity': nullity, 'lp_value': None}, prob.status
    lp_value = float(prob.value)

    scale = max(np.abs(Bf).max(), 1.)
    opening = lp_value > tol * scale * m

    dq = np.zeros(n)
    if opening:
        dq[:n_free] = x.value
    elif nullity:
        dq[:n_free] = V[:, np.argmax(null)]

    motion_exists = bool(nullity > 0 or opening)
    print(f"motion exists: {motion_exists}")
    print(f"sliding modes (nullity): {nullity}, opening motion LP value: {lp_value}")

    return motion_exists, dq, {'nullity': nullity, 'lp_value': lp_value}, prob.status


def mechanism_test(G, f_ext, n_fixed=1, dof_per_body=6, tol=1e-6):
    """
    Determines whether a contact system admits a mechanism and whether it is
    activated, suppressed, or neutral under external forces.

    Parameters
    ----------
    G : ndarray (m, nc)
        Contact Jacobian
    f_ext : ndarray (m,)
        External generalized forces
    n_fixed : int
        Number of fixed bodies
    dof_per_body : int
        Degrees of freedom per body
    tol : float
        Numerical tolerance

    Returns
    -------
    None
    """

    m, n = G.shape

    fixed_dofs = n_fixed * dof_per_body

    dq = cp.Variable(m)

    constraints = [
        G.T @ dq >= 0,             # kinematic admissibility (motion cone)
        cp.norm1(dq) <= 1,         # bounded set (keeps problem convex)
        *fixed_dofs_zero(dq, n_fixed, dof_per_body),  # fixed bodies
    ]

    # --- MAX problem ---
    prob_max = cp.Problem(cp.Maximize(f_ext @ dq), constraints)
    prob_max.solve(
        solver=cp.ECOS,
        abstol=1e-6, reltol=1e-6, feastol=1e-4,
        max_iters=10000,
        verbose=False
    )
    # prob_max.solve(
    #     solver=cp.SCS,
    #     eps=1e-6,          # accuracy (similar to abstol/reltol)
    #     max_iters=10000,
    #     verbose=True
    # )
    
    if prob_max.status not in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
        print("Numerical issue in max problem")
        return

    gamma_max = prob_max.value
    print(f"gamma max: {gamma_max}")

    # --- MIN problem ---
    prob_min = cp.Problem(cp.Minimize(f_ext @ dq), constraints)
    prob_min.solve(
        solver=cp.ECOS,
        abstol=1e-6, reltol=1e-6, feastol=1e-4,
        max_iters=10000,
        verbose=False
    )
    # prob_min.solve(
    #     solver=cp.SCS,
    #     eps=1e-6,          # accuracy (similar to abstol/reltol)
    #     max_iters=10000,
    #     verbose=True
    # )

    if prob_min.status not in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
        print("Numerical issue in min problem")
        return

    gamma_min = prob_min.value
    print(f"gamma min: {gamma_min}")

    # --- Classification ---
    if gamma_max > tol and gamma_min < -tol:
        print("Free mechanism (bidirectional, force does not constrain motion)")
    elif gamma_max > tol:
        print("Activated mechanism (force can drive motion)")
    elif gamma_min < -tol:
        print("Suppressed mechanism (force opposes all motions)")
    else:
        print("Neutral mechanism (force does no work)")

    # Optional: return values for further analysis
    return gamma_min, gamma_max
