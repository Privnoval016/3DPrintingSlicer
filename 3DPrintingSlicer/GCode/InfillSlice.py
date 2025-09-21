
class InfillSlice:
    def __init__(self, z0, polygons, infill_vertices, infill_edges):
        self.z0 = z0
        self.polygons = polygons # List of shapely polygons representing perimeters
        self.infill_vertices = infill_vertices # List of (x, y, z) tuples for infill vertices
        self.infill_edges = infill_edges # List of (start_idx, end_idx) tuples for infill edges