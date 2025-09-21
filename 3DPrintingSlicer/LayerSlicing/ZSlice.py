import numpy as np
from collections import defaultdict

class ZSlice:
    def __init__(self, z):
        self.vertices = np.empty(0) # list of vertices (x, y, z)
        self.edges = np.empty((0, 2), dtype=int) # list of (index1, index2) of vertices
        self.normals = np.empty((0, 3)) # list of normals (n_x, n_y, 0) for each edge
        self.z0 = z # z value of the slicing plane


    def slice_mesh(self, vertices, faces, normals, eps=1e-9):

        sliced_vertices = [] # list of vertices (x, y, z0)
        vertex_map = {} # maps (x, y, z0) to index in sliced_vertices
        edge_count = defaultdict(int) # to count occurrences of each edge
        sliced_edges = [] # list of (index1, index2) of vertices in sliced_vertices
        sliced_normals = [] # list of normals (n_x, n_y, 0) for each edge

        print("Starting slice at z =", self.z0)

        def add_vertex(p):
            key = (round(p[0], 9), round(p[1], 9), round(p[2], 9))
            if key not in vertex_map:
                i = len(sliced_vertices)
                sliced_vertices.append(p)
                vertex_map[key] = i
            return vertex_map[key]

        for face, normal in zip(faces, normals):
            i1, i2, i3 = face

            tri = [vertices[i1], vertices[i2], vertices[i3]]
            if all(abs(v[2] - self.z0) < eps for v in tri):
                edges_tri = [(i1, i2), (i2, i3), (i3, i1)]
                for a, b in edges_tri:
                    v_a, v_b = vertices[a], vertices[b]
                    vertex1 = add_vertex((v_a[0], v_a[1], self.z0))
                    vertex2 = add_vertex((v_b[0], v_b[1], self.z0))
                    edge = tuple(sorted((vertex1, vertex2)))
                    edge_count[edge] += 1

        for edge, count in edge_count.items(): # only keep edges that appear once
            if count == 1:
                sliced_edges.append(edge)

        for i1, i2, i3 in faces:
            tri = np.array([vertices[i1], vertices[i2], vertices[i3]])
            z_vals = np.array([v[2] for v in tri])

            if all(abs(z - self.z0) < eps for z in z_vals): # skip coplanar triangles
                continue

            points = face_slicing(tri, z_vals, self.z0, eps)

            unique = []
            for p in points:
                if p not in unique:
                    unique.append(p)

            if len(unique) == 2: # only add edge if we have exactly two intersection points
                iA = add_vertex(unique[0])
                iB = add_vertex(unique[1])
                edge = tuple(sorted((iA, iB)))
                if edge not in sliced_edges:
                    sliced_edges.append(edge)
            elif len(unique) == 3: # triangle lies in the plane
                iA = add_vertex(unique[0])
                iB = add_vertex(unique[1])
                iC = add_vertex(unique[2])
                for a, b in [(iA, iB), (iB, iC), (iC, iA)]:
                    edge = tuple(sorted((a, b)))
                    if edge not in sliced_edges:
                        sliced_edges.append(edge)

        self.vertices = np.array(sliced_vertices)
        self.edges = np.array(sliced_edges)
        self.normals = np.array(sliced_normals)

        print(self.vertices)


def face_slicing(tri, z_vals, z0, eps=1e-9):
    points = []

    for v, z in zip(tri, z_vals):  # Check vertices on the plane
        if abs(z - z0) < eps:
            points.append((v[0], v[1], z0))

    edges_tri = [(0, 1), (1, 2), (2, 0)]
    for a, b in edges_tri:  # Check edges crossing the plane
        v1, v2 = tri[a], tri[b]
        z1, z2 = v1[2], v2[2]
        if (z1 - z0) * (z2 - z0) < -eps:
            t = (z0 - z1) / (z2 - z1)
            x = v1[0] + t * (v2[0] - v1[0])
            y = v1[1] + t * (v2[1] - v1[1])
            points.append((x, y, z0))

    return points




