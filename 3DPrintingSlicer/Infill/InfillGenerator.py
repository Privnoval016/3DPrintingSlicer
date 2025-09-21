import numpy as np
from shapely.geometry import LineString, MultiLineString, Polygon
from shapely.ops import unary_union, linemerge

class InfillGenerator:
    def __init__(self, line_spacing=1.0, tolerance=0.1, max_iterations=100):
        self.line_spacing = line_spacing
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.multi_line_string = MultiLineString()

    def gyroid_slice(self, x, z, vertical=False):
        z_sin = np.sin(z)
        z_cos = np.cos(z)
        if vertical:
            phase = np.pi if z_cos < 0 else 0
            a = np.sin(x + phase)
            b = -z_cos
            res = z_sin * np.cos(x + phase)
            r = np.sqrt(a**2 + b**2)
            return np.arcsin(np.clip(a/r, -1, 1)) + np.arcsin(np.clip(res/r, -1,1)) + np.pi
        else:
            phase = 0 if z_sin >= 0 else np.pi
            a = np.cos(x + phase)
            b = -z_sin
            res = z_cos * np.sin(x + phase)
            r = np.sqrt(a**2 + b**2)
            return np.arcsin(np.clip(a/r,-1,1)) + np.arcsin(np.clip(res/r,-1,1)) + 0.5*np.pi

    def make_one_period(self, width, height, z, vertical=False):
        dx = np.pi/50
        x_vals = [0.0]
        y_vals = [self.normalize(self.gyroid_slice(0,z,vertical), height)]
        x = dx
        while x < width:
            y = self.normalize(self.gyroid_slice(x,z,vertical), height)
            i = 0
            while abs((y - y_vals[-1]) / max((x - x_vals[-1]),1e-12)) > self.tolerance and i < self.max_iterations:
                i += 1
                xm = (x + x_vals[-1])/2
                ym = self.normalize(self.gyroid_slice(xm,z,vertical), height)
                x_vals.append(xm)
                y_vals.append(ym)
            x_vals.append(x)
            y_vals.append(y)
            x += dx
        return x_vals, y_vals

    def normalize(self, val, height):
        min_val, max_val = -2*np.pi, 2 * np.pi
        norm = (val - min_val)/(max_val - min_val)
        return norm * height

    def tile_wave_grid(self, x_vals, y_vals, minx, miny, width, height, wave_spacing):
        lines = []
        offset_y = 0
        while offset_y < height:
            coords = [((x+minx), y+1.5*miny+offset_y) for x,y in zip(x_vals, y_vals)]
            lines.append(LineString(coords))
            offset_y += wave_spacing
        return lines

    def create_infill(self, polygons, line_width, wall_count, z0):
        if polygons is None:
            return MultiLineString()
        innermost = [p.buffer(-line_width*(wall_count+.5)) for p in polygons]
        innermost = [p for p in innermost if not p.is_empty]
        if not innermost:
            return MultiLineString([])

        minx = min(p.bounds[0] for p in innermost)
        miny = min(p.bounds[1] for p in innermost)
        maxx = max(p.bounds[2] for p in innermost)
        maxy = max(p.bounds[3] for p in innermost)
        width = maxx - minx
        height = maxy - miny

        vertical =  False #abs(np.sin(z0)) <= abs(np.cos(z0))

        x_vals, y_vals = self.make_one_period(width, height, z0, vertical)

        waves = self.tile_wave_grid(x_vals, y_vals, minx, miny, width, height, self.line_spacing*1.5)

        clipped = []
        for wave in waves:
            for poly in innermost:
                c = wave.intersection(poly)
                if c.is_empty:
                    continue
                if isinstance(c, LineString):
                    clipped.append(c)
                elif hasattr(c,"geoms"):
                    clipped.extend([g for g in c.geoms if isinstance(g, LineString)])

        merged = linemerge(unary_union(clipped))
        if isinstance(merged, LineString):
            merged = [merged]
        return MultiLineString(merged)
    
    def get_vertices_edges(self):
        infill_vertices = []
        infill_edges = []
        current_vertex = 0
        for line in self.multi_line_string.geoms():
            verticies = list(line)
            for vertex in verticies:
                if vertex == verticies[0]:
                    continue
                infill_vertices.append(verticies)
                infill_edges.append((current_vertex, current_vertex+1))
                current_vertex +=1
        return (infill_vertices, infill_edges)




