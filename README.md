# 3D Print Slicer & G-Code Generator

A Python-based tool for slicing 3D models and generating G-code for 3D printing. Designed for performance, flexibility, and fine control over slicing and toolpath generation.  

## Usage

With the GitHub repository cloned, simply run 
```
python3 main.py
```
from the root directory to begin the simulation. Users can load .stl or .gcode files and step through their progressions, as well as autoplay the stacking. Additionally, users can tweak parameters for infill generation, as well as write Gcode to a filepath.

## Inspiration

In today's day and age the only relevant 3D model slicing libraries are PrusaSlicer, Cura, and OrcaSlicer, with any meaningful changes created from forks of these repositories. Therefore, we decided to engineer and develop a 3D printing simulator, mesh slicer, and Gcode generator in 24 hours using Python. 

## What it does
Our project is capable of transforming a .stl 3D model into an instruction set written in Gcode, the language utilized by 3D printer software. It slices the mesh into discrete layers, then generates a gyroid infill pattern within the model for optimal printing. Finally, it compiles the generated pattern into systematic Gcode instructions that can be rendered and stepped through within the simulation, which is capable of rendering sliced meshes and infill patterns as well.

## How we built it
Our project's algorithms and features are built completely from scratch, only utilizing numpy arrays for computations, shapely polygons for visualization, and QtGUI for frontend development. By combining mathematical theory in linear algebra, graph theory, and discrete math, we implemented a triangle slicing algorithm, as well as an infill generation algorithm. Finally, we synthesized these features into a real time simulator for rendering the relevant files.

## Challenges we ran into
Generating infill patterns was our hardest challenge, as the geometry needs to be laid out perfectly such that when stacking layers, it prints in a rigid fashion. In this project, we implemented the gyroid infill pattern, which is both structurally sound and impressive to look at.

Additionally, because of the limitations of Python's runtime efficiency, the simulator tends to lag when dealing with high-poly .stl files, though we have taken countermeasures to improve performance where we can. We chose Python primarily because of its ease of use with array manipulation and rendering libraries. Nonetheless, a continuation of this project would consider converting the project to a language like C++, which typical slicers are written in.

## Accomplishments that we're proud of
We are quite proud of the complexity of our rendering engine and the various features it supports, especially the different visualizations between .stl files and their .gcode equivalents. Additionally, our Gcode parser and compiler is very robust and is effective enough that Gcode exported from our renderer can be visualized in commonplace 3D software. Finally, our architecture is set up in a scalable manner, lending itself to further improvement.

## What we learned
Completing this project taught us a lot about the intricacies of graph theory, as well as the different considerations Gcode slicers must take into account (now we know why so few people have attempted to tackle this problem). 

## What's next for the Project
A continuation of this project would add support for generating infill for top and bottom faces, as well as support generation for overhangs. 


