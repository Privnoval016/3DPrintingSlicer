import numpy as np
import struct

from LayerSlicing.ZSlice import ZSlice

def get_min_max_z(vertices):
    max_z = np.max(vertices[:, 2])
    min_z = np.min(vertices[:, 2])
    return min_z, max_z


class ZSlicer:
    def __init__(self):
        self.z_slices = []
        self.vertices = np.empty((0, 3)) # list of vertices (x, y, z)
        self.edges = np.empty((0, 2), dtype=int) # list of (index1, index2) of vertices
        self.faces = np.empty((0, 3), dtype=int) # list of (index1, index2, index3) of vertices
        self.normals = np.empty((0, 3)) # list of normals (n_x, n_y, n_z) for each face
        self.min_z = 0
        self.max_z = 0
        self.file_name = ""

    def get_slices(self):
        return self.z_slices

    def compute_slices_from_stl(self, file_name, specify_height=False, num=50):
        self.file_name = file_name

        is_ascii = False

        with open(file_name, "rb") as f:
            header = f.read(80)
            is_ascii = b"solid" in header[:5].lower()

        self.load_ascii_stl(file_name) if is_ascii else self.read_binary_stl(file_name)
        self.min_z, self.max_z = get_min_max_z(self.vertices)

        if specify_height:
            if num >= (self.max_z - self.min_z) / 2 or num <= 0:
                print("Layer height too large for model height.")
                return
            z_range = np.arange(self.min_z, self.max_z + num, num)
        else:
            if num <= 1:
                print("Number of layers must be greater than 1.")
                return
            z_range = np.linspace(self.min_z, self.max_z, num)

        z_range[-1] = self.max_z - 1e-5

        self.z_slices = []

        for z in z_range:
            z_slice = ZSlice(z)
            z_slice.slice_mesh(self.vertices, self.faces, self.normals)

            self.z_slices.append(z_slice)

    def load_ascii_stl(self, filename):
        vertices = []
        vertex_map = {}
        faces = []
        normals = [] # corresponding normals for each face

        def add_vertex(v):
            key = (round(v[0], 9), round(v[1], 9),
                   round(v[2], 9))
            if key not in vertex_map:
                idx = len(vertices)
                vertices.append(v)
                vertex_map[key] = idx
            return vertex_map[key]

        with open(filename, "r") as f:
            tri = []
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                if parts[0].lower() == "vertex":
                    v = tuple(float(x) for x in parts[1:4])
                    tri.append(add_vertex(v))
                elif parts[0].lower() == "endloop":
                    if len(tri) == 3:
                        faces.append(tuple(tri))
                    tri = []
                elif parts[0].lower() == "facet" and parts[1].lower() == "normal":
                    n = tuple(float(x) for x in parts[2:5])
                    normals.append(n)

        edges = set()
        for (i1, i2, i3) in faces:
            edges.add(tuple(sorted((i1, i2))))
            edges.add(tuple(sorted((i2, i3))))
            edges.add(tuple(sorted((i3, i1))))

        self.vertices = np.array(vertices)
        self.edges = np.array(list(edges), dtype=int)
        self.faces = np.array(faces, dtype=int)
        self.normals = np.array(normals)


    def read_binary_stl(self, filename):
        vertices = []
        faces = []
        normals = []

        vertex_map = {}

        def add_vertex(v):
            key = tuple(round(x, 9) for x in v)
            if key not in vertex_map:
                idx = len(vertices)
                vertices.append(v)
                vertex_map[key] = idx
            return vertex_map[key]

        with open(filename, "rb") as f:
            f.read(80)  # header
            num_triangles = struct.unpack("<I", f.read(4))[0]

            for _ in range(num_triangles):
                data = f.read(50)
                # Unpack normal
                n = struct.unpack("<3f", data[0:12])
                normals.append(n)

                # Unpack vertices
                v1 = struct.unpack("<3f", data[12:24])
                v2 = struct.unpack("<3f", data[24:36])
                v3 = struct.unpack("<3f", data[36:48])

                i1 = add_vertex(v1)
                i2 = add_vertex(v2)
                i3 = add_vertex(v3)

                faces.append((i1, i2, i3))

        self.vertices = np.array(vertices)
        self.faces = np.array(faces, dtype=int)
        self.normals = np.array(normals)





