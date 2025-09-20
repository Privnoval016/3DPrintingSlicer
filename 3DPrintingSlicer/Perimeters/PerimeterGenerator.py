from shapely import Polygon
import numpy as np
from collections import defaultdict

import shapely

from LayerSlicing.ZSlice import ZSlice

class PerimeterGenerator:
    def create_polygons(self, z_slice):
        adjacency = defaultdict(list)
        for edge in z_slice.edges:
            adjacency[edge[0]].append(edge[1])
            adjacency[edge[1]].append(edge[0])
        
        polygon_indices = []    
        current_polygon = []

        edge = adjacency[0]
        while len(adjacency) > 0:
            next = 0
            if adjacency.get(edge[0]) is not None:
                next = edge[0]
            elif adjacency.get(edge[1]) is not None:
                next = edge[1]
            else :
                next = list(adjacency.keys())[0]
                polygon_indices.append(current_polygon)
            current_polygon.append(edge[1])
            edge = adjacency[next]
            del adjacency[next]

        if len(current_polygon) > 0:
            polygon_indices.append(current_polygon)
        
        all_polygons = []
        for vertex_indices in polygon_indices:
            vertices = []
            for vertex in vertex_indices:
                vertices.append(z_slice.vertices[vertex])
            all_polygons.append(Polygon(vertices))
            
        depth = []
        for polygon in all_polygons:
            point = polygon.representative_point()
            depth.append(sum(1 for other in all_polygons if other != polygon and other.contains(point)))
        
        polygons = []
        polygon_depths = []
        for i, polygon in enumerate(all_polygons):
            if depth[i] % 2 == 0 :
                polygon_depths.append(depth[i])
                polygons.append(polygon)
        
        for i, polygon in enumerate(all_polygons):
            if depth[i] % 2 == 1 :
                for j, other in enumerate(polygons):
                    if depth[i] + 1 == polygon_depths[j] and other.contains(polygon.reprsentative_point()):
                        other = shapely.union_all((other,polygon))
        
        return polygons
    
    def __init__(self, z_slice):
        self.z_slice = z_slice
        self.polygons = self.create_polygons(z_slice) # Set of polygons: Outer Contour, and hole with Inner Contour

        
    def createPerimeters(self, line_width, wall_count):
        perimeters = []
        for polygon in self.polygons:
            for i in range(wall_count):
                perimeters.append(shapely.buffer(polygon, (-1) * line_width * i))
        return perimeters