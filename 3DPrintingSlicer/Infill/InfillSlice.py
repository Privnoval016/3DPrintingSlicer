import numpy as np
from shapely.geometry import LineString, MultiLineString, Polygon

class InfillSlice:
    def __init__(self, z0, polygons, infill_vertices, infill_edges):
        self.z0 = z0
        self.polygons = polygons # List of shapely polygons representing perimeters
        self.infill_vertices = infill_vertices # List of (x, y, z) tuples for infill vertices
        self.infill_edges = infill_edges # List of (start_idx, end_idx) tuples for infill edges
        self.all_vertices = [] # Combined list of all vertices (perimeter + infill)
        self.all_edges = [] # Combined list of all edges (perimeter + infill)
        self.generate_all_vertices()


    def generate_all_vertices(self):
        """
        Merge existing vertices/edges with polygons (2D) lifted into 3D at z=z0.
        Works even if vertices/edges are empty.
        """
        # --- Normalize input arrays ---
        vertices = np.asarray(self.infill_vertices, dtype=float).copy()
        if vertices.ndim == 1:
            if vertices.size == 0:
                vertices = vertices.reshape(0, 3)
            else:
                vertices = vertices.reshape(-1, 3)

        # If vertices are 2D, pad z=z0
        if vertices.shape[1] == 2:
            vertices = np.column_stack(
                [vertices, np.full(len(vertices), self.z0)])

        # --- Normalize edges ---
        edges = np.asarray(self.infill_edges, dtype=int).copy()
        if edges.ndim == 1 or edges.size == 0:
            edges = edges.reshape(0, 2)

        poly_coords = np.empty((0, 3), dtype=float)
        poly_edges = np.empty((0, 2), dtype=int)

        # --- Process polygons ---
        for poly in self.polygons:
            if isinstance(poly, Polygon):
                coords_2d = np.asarray(poly.exterior.coords, dtype=float)
            else:
                coords_2d = np.asarray(poly, dtype=float)

            # Force 2D → 3D
            if coords_2d.shape[1] == 2:
                coords = np.column_stack(
                    [coords_2d, np.full(len(coords_2d), self.z0)])
            else:
                coords = coords_2d

            start_idx = len(poly_coords)
            poly_coords = np.append(poly_coords, coords, axis=0)

            # closed polygon edges
            idxs = np.arange(start_idx, start_idx + len(coords))
            edges_new = np.column_stack([idxs, np.roll(idxs, -1)])
            poly_edges = np.append(poly_edges, edges_new, axis=0)

        # --- Merge ---
        all_coords = np.append(vertices, poly_coords, axis=0)
        offset = len(vertices)
        all_edges = np.append(edges, poly_edges + offset, axis=0)

        # --- Deduplicate + remap edges ---
        uniq_coords, inv = np.unique(all_coords, axis=0, return_inverse=True)
        all_edges = inv[all_edges]

        self.all_vertices = uniq_coords
        self.all_edges = all_edges
