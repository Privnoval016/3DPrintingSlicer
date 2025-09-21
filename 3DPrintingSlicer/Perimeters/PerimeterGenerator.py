from shapely import Polygon
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from shapely import plotting
import shapely
from LayerSlicing.ZSlice import ZSlice


class PerimeterGenerator:
    def create_polygons(self, z_slice):

        adjacency = defaultdict(list)
        for a, b in z_slice.edges:
            adjacency[a].append(b)
            adjacency[b].append(a)

        polygon_indices = []
        visited_edges = set()

        while adjacency:
            # Start from any remaining vertex
            start = next(iter(adjacency))
            current = start
            prev = None
            polygon = [start]

            while True:
                neighbors = adjacency[current]
                # pick the next neighbor
                if prev is None:
                    nxt = neighbors[0]
                else:
                    nxt = neighbors[0] if neighbors[0] != prev else neighbors[1]

                edge = tuple(sorted((current, nxt)))
                if edge in visited_edges:
                    break
                visited_edges.add(edge)

                polygon.append(nxt)

                # advance
                prev, current = current, nxt

                if current == start:
                    break

            polygon_indices.append(polygon)

            # cleanup: remove used vertices (no remaining neighbors)
            for a, b in zip(polygon, polygon[1:]):
                adjacency[a].remove(b)
                adjacency[b].remove(a)
                if not adjacency[a]:
                    del adjacency[a]
                if not adjacency[b]:
                    del adjacency[b]

        all_polygons = []
        for vertex_indices in polygon_indices:
            vertices = []
            for vertex in vertex_indices:
                vertices.append(z_slice.vertices[vertex])
            all_polygons.append(Polygon(vertices))

        depth = []
        for polygon in all_polygons:
            point = polygon.representative_point()
            depth.append(sum(1 for other in all_polygons if
                             other != polygon and other.contains(point)))

        polygons = []
        polygon_depths = []
        for i, polygon in enumerate(all_polygons):
            if depth[i] % 2 == 0:
                polygon_depths.append(depth[i])
                polygons.append(polygon)

        for i, polygon in enumerate(all_polygons):
            if depth[i] % 2 == 1:
                for j, other in enumerate(polygons):
                    if depth[i] + 1 == polygon_depths[j] and other.contains(
                            polygon.reprsentative_point()):
                        other = shapely.union_all((other, polygon))

        return polygons

    def __init__(self, z_slice):
        self.z_slice = z_slice
        self.polygons = self.create_polygons(
            z_slice)  # Set of polygons: Outer Contour, and hole with Inner Contour

    def createPerimeters(self, line_width, wall_count):
        perimeters = []
        for polygon in self.polygons:
            for i in range(wall_count):
                perimeters.append(
                    shapely.buffer(polygon, (-1) * line_width * (i + 1)))
        return perimeters