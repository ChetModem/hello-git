import numpy as np, trimesh
def split_nonmanifold_edges(m):
    """Give each sheet meeting at an over-shared edge its own copy of the edge's two vertices.
    Geometry is not moved; only connectivity changes. Returns (mesh, edges_split)."""
    F = m.faces.copy(); V = m.vertices.copy(); done = 0
    for _ in range(10):
        es = np.sort(np.stack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1).reshape(-1, 2), axis=1)
        u, inv, cnt = np.unique(es, axis=0, return_inverse=True, return_counts=True)
        bad = np.where(cnt > 2)[0]
        if not len(bad): break
        e = u[bad[0]]; badset = {tuple(u[b]) for b in bad}
        for vtx in e:
            fan = np.where((F == vtx).any(1))[0]
            # connect faces of the fan that share an edge through vtx, but not across over-shared edges
            parent = {f: f for f in fan}
            def find(x):
                while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
                return x
            for i, a in enumerate(fan):
                for b in fan[i + 1:]:
                    sh = set(F[a]) & set(F[b])
                    if len(sh) == 2 and tuple(sorted(sh)) not in badset: parent[find(a)] = find(b)
            groups = {}
            for f in fan: groups.setdefault(find(f), []).append(f)
            for g in list(groups.values())[1:]:
                V = np.vstack([V, V[vtx]]); nv = len(V) - 1
                for f in g: F[f][F[f] == vtx] = nv
        done += 1
    return trimesh.Trimesh(V, F, process=False), done
