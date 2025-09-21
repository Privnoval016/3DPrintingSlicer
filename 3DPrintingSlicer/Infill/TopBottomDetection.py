from collections import defaultdict
import os
from shapely.geometry import Polygon
from shapely.ops import unary_union
import numpy as np


class TopBottomDetection:
    top_normal = np.array([0,0,1])
    def __init__(self, zslicer):
        self.zslicer = zslicer
        
        self.layer_height =  zslicer.z_slices[1].z0 - zslicer.z_slices[0].z0

    def getSurfaces(self, tolerance=.5):
        top_normals = []
        bottom_normals = []
        for face, normal in zip(self.zslicer.faces, self.zslicer.normals):
            magnitude = np.linalg.norm(normal)
            angle = np.arccos(np.dot(self.top_normal, normal)/ magnitude)
            if np.abs(angle) < tolerance :
                top_normals.append(face)
            elif np.abs(angle - 180) < tolerance:
                bottom_normals.append(face)
        
        return (top_normals, bottom_normals)
    
    def faces_to_polygons(self, vertices, faces, eps_z=1e-5):
 
        # Compute average Z for each face
        face_z = [vertices[face].mean(axis=0)[2] for face in faces]
        
        # Group faces by Z level
        z_groups = defaultdict(list)
        for f, z in zip(faces, face_z):
            z_key = round(z / eps_z) * eps_z
            z_groups[z_key].append(f)
        
        polygons_at_z = []
        
        for z, group in z_groups.items():
            # Convert each face to a 2D polygon (XY only)
            polys = [Polygon(vertices[face, :2]) for face in group]
            # Merge them into one (handles holes automatically)
            merged = unary_union(polys)
            polygons_at_z.append((z, merged))
        
        return polygons_at_z

    
    def getPolygonsfromZ(self, tolerance=.5, eps_z = 0.01):
        top_normals, bottom_normals = self.getSurfaces(tolerance)
        top_polygons = self.faces_to_polygons(self.zslicer.vertices,top_normals)
        bottom_polygons = self.faces_to_polygons(self.zslicer.vertices,bottom_normals)
        return top_polygons, bottom_polygons
    
    

        
        