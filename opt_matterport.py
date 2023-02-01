from datetime import datetime
from tqdm import tqdm
from pathlib import Path
import bpy, mathutils
import numpy as np

class Bbox:

    def __init__(self):
        self.min = mathutils.Vector((float("inf"),float("inf"),float("inf")))
        self.max = mathutils.Vector((float("-inf"),float("-inf"),float("-inf")))

    def merge(self, vertex):
        self.min = mathutils.Vector((min(vertex.x, self.min.x), min(vertex.y, self.min.y), min(vertex.z, self.min.z)))
        self.max = mathutils.Vector((max(vertex.x, self.max.x), max(vertex.y, self.max.y), max(vertex.z, self.max.z)))

    def center(self):
        return (self.min + self.max)/2.0

def fit_to_plane(arg_mesh:bpy.types.Mesh):

    rows, cols = (len(arg_mesh.vertices), 3)
    if rows <= 3:
        return np.array([0.0, 0.0, 0.0])

    XYZ = np.zeros((rows, cols))

    for i, vert in enumerate(arg_mesh.vertices):
        XYZ[i] = np.array([vert.co[0], vert.co[1], vert.co[2]])

    p = np.ones((rows, 1))
    AB = np.hstack([XYZ, p])
    [u, d, v] = np.linalg.svd(AB, 0)
    B = v[3,:];
    nn = np.linalg.norm(B[0:3])
    B = B / nn
    return B[0:3]

def matterport_per_tile_merge(arg_name, arg_distance) -> str :
    """
    Split and Merge the sub component of mesh having crease

    Parameters
    ----------
    arg_name : input obj file name
    arg_distance : knn search parameter to find near object from one object

    Return
    ----------
    written file name

    """
    
    filepath = Path(arg_name)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.obj(filepath=str(filepath), split_mode="ON")

    # seperate
    obj = bpy.context.scene.objects[0]
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT') 
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete_loose()
    bpy.ops.mesh.dissolve_degenerate()
    bpy.ops.mesh.dissolve_limited()

    # divide to other objects
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT') 
    
    # object index to object name map
    index_object_map = {}

    # calculate bbox center position
    def location(object):
        mesh = obj.data

        bbox = Bbox()
        for vert in mesh.vertices:
            bbox.merge(vert.co)
        return bbox.center()

    object_pos = {}
    for i, obj in enumerate(bpy.context.scene.objects):
        bpy.context.view_layer.objects.active = obj

        object_pos[obj.name] = location(obj)
        index_object_map[i] = obj.name

    # searching data structure to find near object
    kdtree = mathutils.kdtree.KDTree(len(object_pos))
    for i, v in enumerate(object_pos):
        kdtree.insert(object_pos[v], i)
    kdtree.balance()

    object_group = {}
    for obj_name in object_pos:
        position = object_pos[obj_name]
        object_group[obj_name] = kdtree.find_range(position, arg_distance)

    # start searching from sorted objects list by object area
    object_area = {}
    for obj in bpy.context.scene.objects:
        bpy.context.view_layer.objects.active = obj
        mesh = obj.data

        area = 0
        for p in mesh.polygons:
            area += p.area
        object_area[obj.name] = area
    object_area = {name:area for name, area in sorted(object_area.items(), key=lambda item: item[1])}

    # start search and merge algorithm
    print("start to merge")
    for obj in tqdm(object_area):
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.active_object.select_set(False)

        objects = bpy.context.scene.objects
        central_obj = objects.get(obj)
        if central_obj:

            bpy.context.view_layer.objects.active = central_obj
            central_obj.select_set(True)

            flag = False
            near_point_group = object_group[obj]
            for near_point in near_point_group:
                near_obj = objects.get(index_object_map[near_point[1]])
                if near_obj:
                    near_obj.select_set(True)
                    flag = True
            
            # merge
            bpy.ops.object.mode_set(mode='OBJECT')
            if flag:
                bpy.ops.object.join()

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.01)
            bpy.ops.object.mode_set(mode='OBJECT')

    # naming output
    outname = datetime.now().strftime("%y%m%d%H%M%S.obj")

    # real write
    bpy.ops.export_scene.obj(filepath=outname)
    return outname


def mattterport_per_tile_smooth(arg_name, arg_smoothing_factor=0.5, arg_applied_axis=[True, True, True]):

    bpy.ops.wm.read_factory_settings(use_empty=True)

    filepath = Path(arg_name)
    bpy.ops.import_scene.obj(filepath=str(filepath), split_mode="ON")
    
    # preprocess
    obj = bpy.context.scene.objects[0]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT') 
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.delete_loose()
    bpy.ops.mesh.dissolve_degenerate()
    bpy.ops.mesh.dissolve_limited()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT') 

    def eval_normal_direction(mesh_normal):
        normal = (mesh_normal[0]*mesh_normal[0], mesh_normal[1]*mesh_normal[1], mesh_normal[2]*mesh_normal[2])
        if normal[0] > normal[1]:
            if normal[0] > normal[2]:
                return "X"
            elif normal[0] < normal[2]:
                return "Z"
        elif normal[0] < normal[1]:
            if normal[1] > normal[2]:
                return "Y"
            elif normal[2] > normal[1]:
                return "Z"

    # optimize per objects
    for obj in tqdm(bpy.context.scene.objects):
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.active_object.select_set(False)

        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')

        mesh = obj.data
        plane_normal = fit_to_plane(mesh)
        flag = eval_normal_direction(plane_normal)

        # bpy.ops.mesh.dissolve_degenerate()
        print(f"{obj}, flag: {flag}")
        if flag == "X" and arg_applied_axis[0]:
            # bpy.ops.mesh.vertices_smooth(factor=0.25, repeat=2, xaxis=True, yaxis=False, zaxis=False)
            bpy.ops.mesh.vertices_smooth_laplacian(lambda_factor=arg_smoothing_factor, lambda_border=1e-8, preserve_volume=True, use_x=True, use_y=False, use_z=False)
        elif flag == "Y" and arg_applied_axis[1]:
            # bpy.ops.mesh.vertices_smooth(factor=0.25, repeat=2, xaxis=False, yaxis=True, zaxis=False)
            bpy.ops.mesh.vertices_smooth_laplacian(lambda_factor=arg_smoothing_factor, lambda_border=1e-8, preserve_volume=True, use_x=False, use_y=True, use_z=False)
        elif flag == "Z" and arg_applied_axis[2]:            
            # bpy.ops.mesh.vertices_smooth(factor=0.25, repeat=2, xaxis=False, yaxis=False, zaxis=True)
            bpy.ops.mesh.vertices_smooth_laplacian(lambda_factor=arg_smoothing_factor, lambda_border=1e-8, preserve_volume=True, use_x=False, use_y=False, use_z=True)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

    # join separated objects
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.join()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.01)
    bpy.ops.mesh.fill_holes(sides=1000)
    bpy.ops.mesh.remove_doubles(threshold=0.01)
    bpy.ops.mesh.select_all(action='DESELECT')

    # naming output
    outname = datetime.now().strftime("%y%m%d%H%M%S.obj")

    # real write
    bpy.ops.export_scene.obj(filepath=outname)
    return outname


#####################################
# run the program
#####################################
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input")
args = parser.parse_args()

if __name__ == "__main__":

    distances = [0.3, 0.5, 0.5, 0.8, 0.8, 1.0]
    outname = args.input
    for dist in distances:
        outname = matterport_per_tile_merge(outname, dist)
    mattterport_per_tile_smooth(outname, 0.5)