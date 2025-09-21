from shapely import Polygon
import numpy as np
from collections import defaultdict
import shapely
from LayerSlicing.ZSlice import ZSlice


class PerimeterGenerator:
    def create_polygons(self, z_slice):

        adjacency = defaultdict(list)
        for a, b in z_slice.edges:
            adjacency[a].append(b)
            adjacency[b].append(a)

        visited_edges = set()
        polygon_indices = []

        while adjacency:
            start = next(iter(adjacency))
            current = start
            prev = None
            polygon = [start]

            while True:
                neighbors = adjacency[current]
                # pick the next neighbor not equal to prev
                nxt = None
                for n in neighbors:
                    edge = tuple(sorted((current, n)))
                    if edge not in visited_edges:
                        nxt = n
                        break

                if nxt is None:
                    # dead end (should not happen if fully connected)
                    break

                # mark edge visited
                visited_edges.add(tuple(sorted((current, nxt))))
                polygon.append(nxt)

                prev, current = current, nxt

                if current == start:
                    break  # closed loop

            # Only keep valid polygons
            if len(set(polygon)) >= 3:
                polygon_indices.append(polygon)

            # Cleanup: remove all used edges from adjacency
            for a, b in zip(polygon, polygon[1:]):
                if b in adjacency[a]:
                    adjacency[a].remove(b)
                if a in adjacency[b]:
                    adjacency[b].remove(a)
                if not adjacency[a]:
                    del adjacency[a]
                if not adjacency[b]:
                    del adjacency[b]

        # Now process all loops to polygons
        all_polygons = []
        for vertex_indices in polygon_indices:
            vertices = [z_slice.vertices[v] for v in vertex_indices]
            all_polygons.append(Polygon(vertices))

        # Determine depth for holes
        depth = []
        for polygon in all_polygons:
            point = polygon.representative_point()
            depth.append(sum(1 for other in all_polygons if
                             other != polygon and other.contains(
                                 point)))

        # Outer polygons
        polygons = []
        polygon_depths = []
        for i, polygon in enumerate(all_polygons):
            if depth[i] % 2 == 0:
                polygons.append(polygon)
                polygon_depths.append(depth[i])

        # Merge holes into outer polygons
        for i, polygon in enumerate(all_polygons):
            if depth[i] % 2 == 1:
                for j, outer in enumerate(polygons):
                    if outer.contains(
                            polygon.representative_point()):
                        polygons[j] = shapely.union_all(
                            [outer, polygon])
                        break

        return polygons

    def __init__(self, z_slice):
        self.z_slice = z_slice
        self.polygons = self.create_polygons(
            z_slice)  # Set of polygons: Outer Contour, and hole with Inner Contour

    def split_to_polygons(self, geom):
        if geom.is_empty:
            return []
        if geom.geom_type == "Polygon":
            return [geom]
        else:
            return list(geom.geoms)

    def createPerimeters(self, line_width, wall_count):
        perimeters = []
        if (self.polygons is None):
            return []
        for polygon in self.polygons:
            for i in range(wall_count):
                perimeters.append(
                    shapely.buffer(polygon, (-1) * line_width * (i + 1 / 2)))
        return [poly for perimeter in perimeters for poly in
                self.split_to_polygons(perimeter)]
