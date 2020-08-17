from enum import Enum
from PIL import Image
import glob
import random
import string
import sys
import os

from pathlib import Path
 
 
import json
from enum import Enum

import shutil
from shutil import Error

input_file_filepath = ""
output_tmp_root_folder = ""

## Variables
class Filetype_3D(Enum):     
    OBJ = 0
    GLTF = 1
    GLB = 2
    USDZ = 3

class ConvertConfig:
	filename_to_convert = ""
	filepath = ""
	texture_folder = ""
	filetypes_to_convert = []
	output_folder = ""
	convert_textures_to_jpeg = False
	jpeg_texture_quality = 80
	remove_shadow_plane = False
	overwrite_glass_transparency = False
	glass_transparency_value = 0.5
	
	def __init__(self, filename_to_convert, filepath, texture_folder, filetypes_to_convert, output_folder, convert_textures_to_jpeg, jpeg_texture_quality, remove_shadow_plane, overwrite_glass_transparency, glass_transparency_value):
		self.filename_to_convert = filename_to_convert
		self.filepath = filepath
		self.texture_folder = texture_folder
		self.filetypes_to_convert = filetypes_to_convert
		self.output_folder = output_folder
		self.convert_textures_to_jpeg = convert_textures_to_jpeg
		self.jpeg_texture_quality = jpeg_texture_quality
		self.remove_shadow_plane = remove_shadow_plane
		self.overwrite_glass_transparency = overwrite_glass_transparency
		self.glass_transparency_value = glass_transparency_value

convertConfig = ConvertConfig("", "", "", [], "", False, 80, False, False, 0.5)

 
class TextureType(Enum):     
    DIFFUSE = 0
    NORMAL = 1
    SPECULAR = 2
    ROUGHNESS = 3
    AMBIENTOCCLUSION = 4
    METALLIC = 5
    HEIGHT = 6

import bpy, math
import sys

import os
import subprocess

# Global vars
model_file = ''
texture_folder = ''
current_exe_folder = ''

glb_file_from_fbx = ''
unpacked_gltf_from_fbx = ''

files_to_delete = []

#file formats to convert
convert_to_gltf = False
convert_to_glb = False
convert_to_usdz = False
convert_to_obj = False

imported_objects = []  # list of objects imported in the 3D scene

# Global flags
NEW_SCENE_NEEDS_RESET = True
RESCALE_VALUE = 1.0	 # canape DOU
# Scale unit used in the scene, METERS or MILLIMETERS
UNIT_USED_IN_SCENE = 'METERS'
RESCALE_XFORM = True
# Prevent Material Names with '.001', '.002', etc...
DEDUPLICATE_MATERIALS = False
# deduce texture folder name from 3D model name
FOLDER_TEXTURE_AUTO_NAMING = True
# apply an inverse Gamma on texture imported in the materials
USE_INVERSE_GAMMA = False
# Use textured backplate
USE_BACKPLATE = True
# Use height/displacement textures
USE_DISPLACEMENT = True
# Use normal map textures
USE_NORMAL = True
# Use height map textures
USE_HEIGHT = True
# Use metal map textures
USE_METAL = True
# Use roughness map textures
USE_ROUGHNESS = True

# ---------------------------------------------------
# ---------------------------------------------------
# Scene Var
# ---------------------------------------------------
# ---------------------------------------------------
model_name = ''
model_folder = ''

folder_shell_textures = ''

imported_objects = []  # list of objects imported in the 3D scene

# ---------------------------------------------------
# ---------------------------------------------------
# Global Blender Var
# ---------------------------------------------------
# ---------------------------------------------------
context = bpy.context
data = bpy.data
scene = bpy.context.scene
world = bpy.context.scene.world
cycles = bpy.context.scene.cycles

# ---------------------------------------------------
# Debug
# ---------------------------------------------------
DEBUG_FLAG = True  # set to TRUE iof you want a verbose output, FALSE unless
SAVE_DEBUG_INFO_TO_TEXT_FILE = True

text_info_str = ''	# to save debug datapyth

###
# Print info in console only if debug flag is set
##
def debug_print(str):
	global text_info_str,DEBUG_FLAG
	if(DEBUG_FLAG):
		print(str + '\n')
		text_info_str += (str + '\n')

# ---------------------------------------------------
# Utils functions
# ---------------------------------------------------
def save_info_text_file():
	global text_info_str, info_errors_file
	"""
	Save informations about the execution of the script in a text file.
	The finale file is saved in the 'text_info_file' file.
	Check if global var 'SAVE_DEBUG_INFO_TO_TEXT_FILE' is TRUE.
	If FALSE, do nothing.
	"""
	if(SAVE_DEBUG_INFO_TO_TEXT_FILE):
		debug_print("Saving informations to textfile")
		# text_info_file = model_folder + model_name + '_infos.txt'
		text_info_file = info_errors_file
		text_info_str_final = model_file + '\n' + text_info_str

		if(not USE_WITH_GUI):
			# Create Dir
			if not os.path.exists(os.path.dirname(text_info_file)):
				# try:
				os.makedirs(os.path.dirname(text_info_file))
				# except OSError as exc: # Guard against race condition
				#	 if exc.errno != errno.EEXIST:
				#		 raise
		if (USE_WITH_GUI):
			text_info_file = test_info_errors_file
		# Force Write File
		with open(text_info_file, "w") as f:
			f.write(text_info_str_final)
# ---------------------------------------------------



def clear_default_scene():
	"""
	When Blender create a new scene, it auto adds a Cube, a Camera and a Lamp. We remove them on start
	"""
	#objs = bpy.data.objects
	#objs.remove(objs["Cube"], True)
	#objs.remove(objs["Camera"], True)
	#objs.remove(objs["Lamp"], True)
	#bpy.data.objects['Cube'].select_set(True)
	#bpy.data.objects['Camera'].select_set(True)
	#bpy.data.objects['Light'].select_set(True)
	#bpy.ops.object.delete()
	#Delete default objects:cube,camera,light
	bpy.ops.object.select_all(action='SELECT')
	bpy.ops.object.delete(use_global=False)

def clear_object_materials(node_name):
	"""
	Clear all material attached to obj & its children, if it's a mesh
	"""
	global text_info_str
	debug_print('--------------------------')
	debug_print(' clear_object_materials()')
	debug_print('----------------------------------------------')
	debug_print('Clearing materials for object: ' + node_name)
	
	# if node_name.material_slots:
	if bpy.data.objects[node_name].type == 'MESH':
		if len(bpy.data.objects[node_name].material_slots) != 0:
			bpy.data.objects[node_name].data.materials.clear()
			debug_print('Clearing mesh: ' + node_name)

	# debug infos
	debug_print('\nClearing materials for object: ' + node_name)

#### TODO : Use custom strings - material_tiling_x, material_tiling_y
def create_object_PBR_material(node_name):
	"""
	Create default PBR material for object
	This function calls the creation of Texture nodes, and 
	correct the material values
	"""
	debug_print('create_object_PBR_material()')
	debug_print('Creating material for: ' + node_name)

	global text_info_str

	if bpy.data.objects[node_name].type == 'MESH':		  
		debug_print('')
		debug_print('.........................................')
		debug_print('Creating BSDF material for: ' + node_name)

		# Get Material name
		mat_name = node_name
		
		# If material name ends with ".001", we remove it.
		mat_name_ending = mat_name[-4:]
		if mat_name_ending[-3:].isdigit() and mat_name_ending[0] == ".": 
			mat_name = mat_name[:-4]
		
		# Set name of mat		
		mat_name = mat_name + '_PBSDF'
		debug_print('Name of the material: ' + mat_name)
		
		# prevent overly long names, 63 characters seems blender limit for material names on osx
		mat_name_60 = mat_name[:60]

		# Create new name
		principled_mat = data.materials.new(mat_name_60)
		principled_mat.use_nodes = True

		# Cache aliases to node and node tree.
		mat_node_tree = principled_mat.node_tree
		mat_nodes = mat_node_tree.nodes

		# Remove default Diffuse BSDF shader.
		#mat_nodes.remove(mat_nodes['Diffuse BSDF'])

		# nodes = principled.node_tree.nodes
		principled_nodes = mat_nodes.new('ShaderNodeBsdfPrincipled')
		# Choose multiscatter
		principled_nodes.distribution = "MULTI_GGX"

		# attach material to object
		bpy.data.objects[node_name].active_material = bpy.data.materials[mat_name_60]

		# get active object's active material
		selected_obj_node_tree = bpy.data.objects[node_name].active_material.node_tree
		selected_obj_node_tree.links.new(principled_nodes.outputs['BSDF'], selected_obj_node_tree.nodes['Material Output'].inputs['Surface'])
		selected_obj_node_tree.nodes['Material Output'].location = selected_obj_node_tree.nodes['Material Output'].location.x, 0

		#######################################
		# Set some default values
		principled_nodes.inputs['IOR'].default_value = 1.5
		#principled_nodes.inputs['Specular'].default_value = 0.01
		principled_nodes.inputs['Specular'].default_value = get_specular_ior_from_mat(node_name.lower())

		#######################################
		# Find textures and apply them to the material through Cycles node system
		createNodeAndTexture(principled_mat, principled_nodes, selected_obj_node_tree, node_name)
		########################################
		debug_print("> Textures: Folder is " + texture_folder)
		# Depending on the name of the object, we will apply different properties to make it PBR ready
		#### autosetMaterialsPBRProperties(principled_nodes, selected_obj_node_tree, node_name)

"""
Return IOR value for a given parameter
The parameter is a string.
The string gives an IOR value
The IOR value is used in a formula, explained in the Blender Principled BSDF doc to return a Specular Value
IOR values: https://pixelandpoly.com/ior.html
PBSDF doc: https://docs.blender.org/manual/fr/dev/render/shader_nodes/shader/principled.html
"""
def get_specular_ior_from_mat(mat_name):
	ior = 1.0
	ior_dictionary = {
	  "air": 1.0,
	  #"bronze" : 1.18, 
	  "fabric": 1.3,
	  "water": 1.33,
	  "wood": 1.35,
	  "leather": 1.4,
	  "velvet": 1.4,
	  "plaster": 1.4,
	  "rugs": 1.4,
	  "tile": 1.4,
	  "brick": 1.4,
	  "linen": 1.4,
	  "cotton": 1.4,
	  "stone": 1.4,
	  "concrete": 1.4,
	  "wood": 1.4,
	  "bark": 1.4,
	  "pebbles": 1.4,
	  "plastic": 1.46,
	  "glass": 1.52,
	  "nylon": 1.53,
	  "ivory": 1.54,
	  "pearl": 1.6,
	  "metal" : 1.6, # aluminium
	  "brass" : 1.6, 
	  "aluminum" : 1.6, 
	  "aluminium" : 1.6, 
	  "bronze" : 1.6, 
	  "copper" : 1.6, 
	  "gold" : 1.6, 
	  "silver" : 1.6, 
	  "steel" : 1.6, 
	  "zinc" : 1.6, 
	  "chrome" : 1.6, 
	  "lead" : 1.6, 
	  "iron" : 1.6, 
	  "asphalt": 1.63,
	  "crystal": 2,
	  "diamond": 2.4
	}
	
	ior = ior_dictionary.get(mat_name,1.5)
	
	specular_value = ((ior - 1)/(ior + 1))**2 / 0.08
	return specular_value


"""
Create the nodes in the shader nodegraph
Assign textures
Uses global var 'USE_INVERSE_GAMMA' to correct inverse gamma on textures
Uses global var 'FOLDER_TEXTURE_AUTO_NAMING' to automatically extract the textures folder
from the model name

We split each node name (ex: '00228606-IKEA-PENDANT_LAMP_STOCKHOLM-metal'), to keep only
'IKEA-PENDANT_LAMP_STOCKHOLM-metal', and search for it in textures.
"""
def createNodeAndTexture(principled_node, principled_nodes, selected_obj_node_tree, node_name):

	debug_print('------------------------')
	debug_print(' createNodeAndTexture()')
	debug_print('------------------------')
	debug_print('> for node : ' + node_name + '\n\n')

	# Vars for that function
	global text_info_str, folder_shell_textures
	global model_folder
	# Success / Fails
	number_of_errors = 0
	number_of_matches = 0
	# Found elements
	diffuse_texture_found = False
	normal_texture_found = False
	specular_texture_found = False
	roughness_texture_found = False
	#ambientOcclusion_texture_found = False				# TODO TODO TODO
	metal_texture_found = False
	heightmap_texture_found = False
	# List of filepaths found
	texture_filepath_str = ''

	# Unity Custom String variables
	material_tiling_x = 1.0
	material_tiling_y = 1.0
	material_color_albedo = (1.0, 1.0, 1.0, 1.0)

	# Unity Custom String handling	
	if "UnityCustomString" in bpy.data.objects[node_name]:
		# Parse Unity Custom string
		customStringDictionary = parseToDictionary(bpy.data.objects[node_name]["UnityCustomString"])
		#debug_print("> Dictionary found : " + bpy.data.objects[node_name]["UnityCustomString"])
		
		# Get variables from it
		if 'material_tiling_x' in customStringDictionary: 
			material_tiling_x = float(customStringDictionary['material_tiling_x'].replace(',','.'))
			debug_print("> material_tiling_x : " + str(material_tiling_x))

		if 'material_tiling_y' in customStringDictionary: 
			material_tiling_y = float(customStringDictionary['material_tiling_y'].replace(',','.'))
			debug_print("> material_tiling_y : " + str(material_tiling_y))

		if 'material_color_albedo' in customStringDictionary: 
			# Get Str
			### Expected: material_color_albedo=RGBA(0,016, 0,545, 0,604, 1,000)
			material_color_albedo_str = customStringDictionary['material_color_albedo']
			# Log
			debug_print("> material_color_albedo : " + str(material_color_albedo_str))
			
			# Remove unnecessary parts
			#### RGBA(0,016, 0,545, 0,604, 1,000) >> (0,016, 0,545, 0,604, 1,000)
			material_color_albedo_str = material_color_albedo_str.replace('RGBA','')
			#### (0,016, 0,545, 0,604, 1,000) >> 0,016, 0,545, 0,604, 1,000)
			material_color_albedo_str = material_color_albedo_str.replace('(','')
			#### 0,016, 0,545, 0,604, 1,000) >> 0,016, 0,545, 0,604, 1,000
			material_color_albedo_str = material_color_albedo_str.replace(')','')
			#### 0,016, 0,545, 0,604, 1,000 >> 0.016. 0.545. 0.604. 1.000
			material_color_albedo_str = material_color_albedo_str.replace(',','.')

			# Parse
			#### 0.016, 0.545, 0.604, 1.000 > ["0.016" , "0.545" , "0.604" , "1.000"]
			material_color_albedo_str_parts = material_color_albedo_str.split('. ')
			if len(material_color_albedo_str_parts) > 3:
				# Get RGB
				r = float(material_color_albedo_str_parts[0])
				g = float(material_color_albedo_str_parts[1])
				b = float(material_color_albedo_str_parts[2])
				# a = float(material_color_albedo_str_parts[3])

				# Convert it from Linear to Gamma
				r = pow(r, 2.2)
				g = pow(g, 2.2)
				b = pow(b, 2.2)

				# Apply Color
				material_color_albedo = (r, g, b, 1.0)

			# Log
			debug_print("> Cleaned = " + str(material_color_albedo_str))
			debug_print("> Parsed = " + str(material_color_albedo))

			# Apply to Principled BSDF node
			mat_node_tree = principled_node.node_tree
			mat_nodes = mat_node_tree.nodes
			principled_nodes.inputs['Base Color'].default_value = material_color_albedo
				

	# Root Texture possible paths
	root_texture_path = node_name
	
	# Check ending and if material name ends with ".001", we remove it.
	root_texture_path_ending = root_texture_path[-4:]
	if root_texture_path_ending[-3:].isdigit() and root_texture_path_ending[0] == ".": 
		root_texture_path = root_texture_path[:-4]
		
	# Complete with Texture base path
	root_texture_path = model_folder + '/textures/' + root_texture_path
	debug_print("> Complete with Texture base path: " + root_texture_path)
	print("> Complete with Texture base path: " + root_texture_path)
	
	##################################################
	# Set Diffuse
	##################################################
	for suffixes in ('_D', '_d', '-D', '-d','_diffuse','_Diffuse','_map_diffuse','_map_Diffuse'):
		#for extension in ('.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'):
		for extension in ('.jpg', '.jpeg','.JPG', '.JPEG'):		
			# Do while texture wasn't found		 
			if (diffuse_texture_found == False):
				filepath =	root_texture_path + suffixes + extension 
				#debug_print('> Checking file: ' + filepath)

				# If file exists
				if(os.path.isfile(filepath)):
					# Attribute it to this object's material
					diffuse_texture_found = setMaterialTexture(principled_node, principled_nodes, selected_obj_node_tree, node_name, filepath, TextureType.DIFFUSE, material_tiling_x, material_tiling_y)

					# If success, log
					if (diffuse_texture_found == True):
						debug_print('> Diffuse	is set - Filename: ' + filepath)
						texture_filepath_str += '\n'+ filepath
						number_of_matches += 1
						break
	
	##################################################
	# Set Normal
	##################################################
	if(USE_NORMAL):
		for suffixes in ('_N', '_n', '-N', '-n','_normal','_Normal','_map_normal','_map_Normal'):
			#for extension in ('.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'):	 
			for extension in ('.jpg', '.jpeg','.JPG', '.JPEG'):					
				# Do while texture wasn't found		 
				if (normal_texture_found == False):
					filepath =	root_texture_path + suffixes + extension 
					#debug_print('> Checking file: ' + filepath)

					# If file exists
					if(os.path.isfile(filepath)):
						# Attribute it to this object's material
						normal_texture_found = setMaterialTexture(principled_node, principled_nodes, selected_obj_node_tree, node_name, filepath, TextureType.NORMAL, material_tiling_x, material_tiling_y)

						# If success, log
						if (normal_texture_found == True):
							debug_print('> Normal  is set - Filename: ' + filepath)
							texture_filepath_str += '\n'+ filepath
							number_of_matches += 1
							break
						
	##################################################
	# Set Specular
	##################################################
	for suffixes in ('_S', '_s', '-S', '-s','_specular','_Specular','_map_specular','_map_Specular'):
		#for extension in ('.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'):	 
		for extension in ('.jpg', '.jpeg','.JPG', '.JPEG'):				
			# Do while texture wasn't found		 
			if (specular_texture_found == False):
				filepath =	root_texture_path + suffixes + extension 
				#debug_print('> Checking file: ' + filepath)

				# If file exists
				if(os.path.isfile(filepath)):
					# Attribute it to this object's material
					specular_texture_found = setMaterialTexture(principled_node, principled_nodes, selected_obj_node_tree, node_name, filepath, TextureType.SPECULAR, material_tiling_x, material_tiling_y)

					# If success, log
					if (specular_texture_found == True):
						debug_print('> Specular	 is set - Filename: ' + filepath)
						texture_filepath_str += '\n'+ filepath
						number_of_matches += 1
						break
	
	##################################################
	# Set Roughness
	##################################################
	if(USE_ROUGHNESS):
		for suffixes in ('_R', '_r', '-R', '-r','_roughness','_Roughness','_map_roughness','_map_Roughness'):
			#for extension in ('.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'):	
			for extension in ('.jpg', '.jpeg','.JPG', '.JPEG'):					
				# Do while texture wasn't found		 
				if (roughness_texture_found == False):
					filepath =	root_texture_path + suffixes + extension 
					#debug_print('> Checking file: ' + filepath)

					# If file exists
					if(os.path.isfile(filepath)):
						# Attribute it to this object's material
						roughness_texture_found = setMaterialTexture(principled_node, principled_nodes, selected_obj_node_tree, node_name, filepath, TextureType.ROUGHNESS, material_tiling_x, material_tiling_y)

						# If success, log
						if (roughness_texture_found == True):
							debug_print('> Roughness  is set - Filename: ' + filepath)
							texture_filepath_str += '\n'+ filepath
							number_of_matches += 1
							break
	
	##################################################
	# Set Metallic
	##################################################
	if(USE_METAL):
		for suffixes in ('_M', '_m', '-M', '-m','_metal','_Metal','_metalness','_Metalness','_map_metal','_map_Metal'):
			#for extension in ('.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'):	  
			for extension in ('.jpg', '.jpeg','.JPG', '.JPEG'):		
				# Do while texture wasn't found		 
				if (metal_texture_found == False):
					filepath =	root_texture_path + suffixes + extension 
					#debug_print('> Checking file: ' + filepath)

					# If file exists
					if(os.path.isfile(filepath)):
						# Attribute it to this object's material
						metal_texture_found = setMaterialTexture(principled_node, principled_nodes, selected_obj_node_tree, node_name, filepath, TextureType.METALLIC, material_tiling_x, material_tiling_y)

						# If success, log
						if (metal_texture_found == True):
							debug_print('> Metallic	 is set - Filename: ' + filepath)
							texture_filepath_str += '\n'+ filepath
							number_of_matches += 1
							break
	
	##################################################
	# Set Height
	##################################################
	if(USE_DISPLACEMENT):
		for suffixes in ('_H', '_h', '-H', '-h','_height','_Height','_map_height','_map_Height'):
			#for extension in ('.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'):	  
			for extension in ('.jpg', '.jpeg','.JPG', '.JPEG'):		
				# Do while texture wasn't found		 
				if (heightmap_texture_found == False):
					filepath =	root_texture_path + suffixes + extension 
					#debug_print('> Checking file: ' + filepath)

					# If file exists
					if(os.path.isfile(filepath)):
						# Attribute it to this object's material
						heightmap_texture_found = setMaterialTexture(principled_node, principled_nodes, selected_obj_node_tree, node_name, filepath, TextureType.HEIGHT, material_tiling_x, material_tiling_y)

						# If success, log
						if (heightmap_texture_found == True):
							debug_print('> Heightmap  is set - Filename: ' + filepath)
							texture_filepath_str += '\n'+ filepath
							number_of_matches += 1
							break

	
	# errors output to file, help to check all the datas
	debug_print('----------------------------------------------------------------------')
	debug_print('For element: ' + node_name + ' - List of textures:')
	debug_print('> Found textures: ' + texture_filepath_str)
	debug_print('----------------------------------------------------------------------')
	#
	if(number_of_errors > 0):
		debug_print('Textures are missing, here\'s the list:')
		debug_print('----------------------------------------------------------------------')
		if(metal_texture_found == False):
			debug_print(node_name+'_D is missing')
		if(normal_texture_found == False):
			debug_print(node_name+'_N is missing')
		if(specular_texture_found == False):
			debug_print(node_name+'_S is missing')
		if(roughness_texture_found == False):
			debug_print(node_name+'_R is missing')
		if(metal_texture_found == False):
			debug_print(node_name+'_M is missing')
		#if(ambientOcclusion_texture_found == False):
		#	 debug_print(node_name+'_AO is missing')
		if(heightmap_texture_found == False):
			debug_print(node_name+'_H is missing')

'''
Set Material node texture and map everything automatically
'''
def setMaterialTexture(principled_node, principled_nodes, selected_obj_node_tree, node_name, textureFilepath, textureType, material_tiling_x, material_tiling_y):
	try:
		# Load image
		img = bpy.data.images.load(filepath=textureFilepath, check_existing=False)

	except NameError:
		debug_print('ERROR : Cannot load image %s' % textureFilepath)
		# Feedback
		return False

	# Reload image
	img.reload()
	
	# Cache aliases to node and node tree.
	mat_node_tree = principled_node.node_tree
	mat_nodes = mat_node_tree.nodes

	# Texture coordinates in material
	X_coord = -500
	Y_coord = 0
	Y_stride = 300

	# Load image into node
	shaderImg = mat_nodes.new('ShaderNodeTexImage')
	shaderImg.extension = 'REPEAT' #'CLIP' if tiling is 1x1
	#shaderImg.color_space = 'NONE'
	#shaderImg.image.colorspace_settings.name='Non-Color' #from
	#shaderImg.image.colorspace_settings.is_data = True	   #https://blender.stackexchange.com/questions/143427/change-color-space-of-image-texture-node-using-python
	shaderImg.image = img
	shaderImg.location = X_coord, Y_coord
	Y_coord = Y_coord-Y_stride

	# Diffuse ?
	###########
	if textureType == TextureType.DIFFUSE:
		# Set node parameter
		selected_obj_node_tree.links.new(shaderImg.outputs['Color'], principled_nodes.inputs['Base Color'])
		#shaderImg.color_space = 'COLOR'
		#shaderImg.image.colorspace_settings.name='sRGB'
		shaderImg.image.colorspace_settings.is_data = False	  

		# set inverse gamma
		if(USE_INVERSE_GAMMA):
			gammaNode = mat_nodes.new('ShaderNodeGamma')
			gammaNode.inputs['Gamma'].default_value = 2.2
			gammaNode.location = X_coord+150, Y_coord
			selected_obj_node_tree.links.new(shaderImg.outputs['Color'], gammaNode.inputs['Color'])
			selected_obj_node_tree.links.new(gammaNode.outputs['Color'], principled_nodes.inputs['Base Color'])

		# Backplate ?
		#############
		if (USE_BACKPLATE):
			if 'backplate' in node_name.lower():				
				#Backplate Gamma
				gammaNode = mat_nodes.new('ShaderNodeGamma')
				gammaNode.inputs['Gamma'].default_value = 1.3
				
				# Backplate saturation
				saturationNode = mat_nodes.new('ShaderNodeHueSaturation')
				saturationNode.inputs['Hue'].default_value = 0.5
				saturationNode.inputs['Saturation'].default_value = 1.0
				saturationNode.inputs['Value'].default_value = 2.0
	 
				# Backplate Emission
				emissionNode = mat_nodes.new('ShaderNodeEmission')
				emissionNode.inputs['Strength'].default_value = 10.0
				
				# Node Links
				selected_obj_node_tree.links.new(shaderImg.outputs['Color'], gammaNode.inputs['Color'])
				selected_obj_node_tree.links.new(gammaNode.outputs['Color'], saturationNode.inputs['Color'])
				selected_obj_node_tree.links.new(saturationNode.outputs['Color'], emissionNode.inputs['Color'])
				selected_obj_node_tree.links.new(emissionNode.outputs['Emission'], selected_obj_node_tree.nodes['Material Output'].inputs['Surface'])

				# TODO: Delete the PBSDF node

				# Remove from reflections of the windows for example
				bpy.data.objects[node_name].cycles_visibility.glossy = False
				bpy.data.objects[node_name].cycles_visibility.transmission = False
				bpy.data.objects[node_name].cycles_visibility.scatter = False
				bpy.data.objects[node_name].cycles_visibility.shadow = False

	# Normal?
	###########
	elif textureType == TextureType.NORMAL:
		shaderImg.image.colorspace_settings.is_data = True	
		# Normal node		 
		shaderNormalNode = mat_nodes.new('ShaderNodeNormalMap')
		shaderNormalNode.location = X_coord, Y_coord
		Y_coord = Y_coord-Y_stride
		
		# Set node parameter
		selected_obj_node_tree.links.new(shaderImg.outputs['Color'], shaderNormalNode.inputs['Color'])
		selected_obj_node_tree.links.new(shaderNormalNode.outputs['Normal'], principled_nodes.inputs['Normal'])
		
	# Roughness ?
	#######################
	elif textureType == textureType == TextureType.ROUGHNESS:
		shaderImg.image.colorspace_settings.is_data = True
		# Set node parameter
		selected_obj_node_tree.links.new(shaderImg.outputs['Color'], principled_nodes.inputs['Roughness'])
		
	# Specular?
	#######################
	elif textureType == TextureType.SPECULAR:
		shaderImg.image.colorspace_settings.is_data = True
		# Set node parameter
		#selected_obj_node_tree.links.new(shaderImg.outputs['Color'], principled_nodes.inputs['Specular'])
		
		#from there https://blender.stackexchange.com/questions/88792/how-to-plug-specular-map-into-principled-shader
		#TODO: change floor material, for the moment we considering inverting the Specular map
		if('floor' in node_name.lower() and not 'floor_lamp' in node_name.lower()):
		#add a new roughness node
			shaderInvertNode = mat_nodes.new('ShaderNodeInvert')
			selected_obj_node_tree.links.new(shaderImg.outputs['Color'], shaderInvertNode.inputs['Color'])
			# Set node parameter
			selected_obj_node_tree.links.new(shaderInvertNode.outputs['Color'], principled_nodes.inputs['Roughness'])
		else:
			selected_obj_node_tree.links.new(shaderImg.outputs['Color'], principled_nodes.inputs['Roughness'])

	# Metallic?
	###########
	elif textureType == TextureType.METALLIC:
		shaderImg.image.colorspace_settings.is_data = True
		selected_obj_node_tree.links.new(shaderImg.outputs['Color'], principled_nodes.inputs['Metallic'])

	# Height ?
	##########
	elif textureType == TextureType.HEIGHT:
		shaderImg.image.colorspace_settings.is_data = True
		# selected_obj_node_tree.links.new(shaderImg.outputs['Color'], principled_nodes.inputs['Base Color'])
		selected_obj_node_tree.links.new(shaderImg.outputs['Color'], selected_obj_node_tree.nodes['Material Output'].inputs['Displacement'])
	
	# Ambient Occlusion?
	####################
	#elif textureType == TextureType.AMBIENTOCCLUSION:
	
	# Texture coordinate
	shaderTexCoord = mat_nodes.new('ShaderNodeTexCoord')
	shaderTexCoord.location = X_coord-800, Y_coord

	# Shader mapping
	shaderMapping = mat_nodes.new( 'ShaderNodeMapping')
	shaderMapping.location = X_coord-500, Y_coord
	#node_tree.nodes["Mapping.005"].inputs[3].default_value
	#shaderMapping.scale[0] = material_tiling_x
	#shaderMapping.scale[1] = material_tiling_y
	shaderMapping.inputs['Scale'].default_value = (material_tiling_x,material_tiling_y,1)
	selected_obj_node_tree.links.new(shaderMapping.outputs['Vector'], shaderImg.inputs['Vector'])
	selected_obj_node_tree.links.new(shaderTexCoord.outputs['UV'], shaderMapping.inputs['Vector'])	

	# Feedback
	return True


def open_materials():
	global imported_objects
	
	# file has been imported, work with it
	# when import operator is used, all imported object are selected
	imported_objects += [o.name for o in bpy.context.selected_objects]
	for node_name in imported_objects:
		if bpy.data.objects[node_name].type == 'MESH':
			clear_object_materials(node_name)  # clear materials automatically created
			create_object_PBR_material(node_name)
			#	reset_xform(o)
	# convert all images to jpg
	for img in bpy.data.images:
		img.filepath = img.filepath.replace('.png', '.jpg')
		img.reload()
		
def replace_png2jpeg(convertConfig):
	global imported_objects
	
	print('Replacing all PNG files with JPEG files')
	
	unpacked_gltf_folder = convertConfig['output_folder']  + '/tmp/fbx2gltf/unpacked'
	print('Folder containing all unpacked images: ' + unpacked_gltf_folder)
	inputFiles = Path(unpacked_gltf_folder).glob("**/*.png")
	outputPath = unpacked_gltf_folder
	
	for f in inputFiles:
		outputFile = outputPath / Path(f.stem + ".jpg")
		im = Image.open(f)
		try:
			im.save(outputFile, quality=int(convertConfig['jpeg_texture_quality']))
		except OSError:
			print("Can't save image with transparency as JPEG with RGBA")
	
	#convert all images to jpg
	for img in bpy.data.images:
		img.filepath_raw = img.filepath_raw.replace('.png', '.jpg')
		img.filepath = img.filepath.replace('.png', '.jpg')
		img.reload()
	
	#open gltf file as a big text string
	unpacked_gltf_file = unpacked_gltf_folder + '/' + input_filename_without_ext + '.gltf'
	data = ''
	with open(unpacked_gltf_file, 'r') as file:
		data = file.read().replace('\n', '')
	data = data.replace('.png','.jpg')
	
	#rewrite the gltf file with .PNG replaced by .JPEG
	text_file = open(unpacked_gltf_file, "w")
	n = text_file.write(data)
	text_file.close()
	
	#delete all png files
	inputFiles = Path(unpacked_gltf_from_fbx).glob("**/*.png")
	for f in inputFiles:
		#shutil.copy2(f,out_GLTF_folder)
		os.remove(f)
	
	#for img in bpy.data.images:
	#	#create tmp folder
	#	# Create Dir
	#	print('output folder: ' + convertConfig['output_folder'])
	#	tmp_img_folder = convertConfig['output_folder']  + '/tmp/'
	#	print('Temporary image folder for PNG to JPEG conversion is: ' + tmp_img_folder)
	#	if not os.path.exists(tmp_img_folder):
	#		# try:
	#		os.makedirs(tmp_img_folder)
	#		# except OSError as exc: # Guard against race condition
	#		#	 if exc.errno != errno.EEXIST:
	#		#		 raise
	#	if 'Render Result' not in img.name and 'Viewing Node' not in img.name:
	#		#img.filepath_raw = tmp_img_folder + img.name + '.jpg'
	#		#print('Saving image named: ' + img.name + ' with filepath: ' + img.filepath_raw)
	#		#img.file_format = 'JPEG'
	#		filepath_raw_PNG = tmp_img_folder + img.name + '.png'
	#		filepath_raw_JPG = filepath_raw_PNG.replace('.png','.jpg')
	#		img.filepath_raw = filepath_raw_PNG
	#		print('Saving image named: ' + img.name + ' with filepath: ' + filepath_raw_PNG)
	#		img.file_format = 'PNG'
	#		img.save()
	#		#img.save()
	#		#bpy.context.window.scene.render.image_settings.quality = int(convertConfig['jpeg_texture_quality'])
	#		#img.save_render(filepath = img.filepath_raw, scene = bpy.context.scene)
	#		im = Image.open(filepath_raw_PNG)
	#		rgb_im = im.convert('RGB')
	#		print('PIL saving image to file: ' + filepath_raw_JPG + ', with quality: ' + str(convertConfig['jpeg_texture_quality']))
	#		rgb_im.save(filepath_raw_JPG, quality=int(convertConfig['jpeg_texture_quality']))
	#		#img = bpy.data.images.load(img.filepath_raw)
	#		img.filepath_raw = filepath_raw_JPG
	#		img = bpy.data.images.load(filepath_raw_JPG)
	#		img.reload()
			

		
def remove_shadow_plane():
	global imported_objects
	
	print('Removing shadow planes')
	
	for obj in bpy.data.objects:
		if "shadow" in obj.name:
			print('Found a shadow plane, removing it')
			# Deselect all
			bpy.ops.object.select_all(action='DESELECT')

			# Select the object
			bpy.data.objects[obj.name].select_set(True) # Blender 2.8x

			bpy.ops.object.delete() 
	

def list_unused_nodes():
	print('Remove unused Blender nodes')
	for mat in bpy.data.materials:
		mat_node = mat.node_tree.nodes
		for node in mat_node:
			if node.name == "Principled BSDF":
				if(len(node.inputs[0].links) == 0):
				#for link in node.inputs[0].links:
					mat_node.remove(node)

def set_single_sided():
	print('Set all materials to single-sided')
	#for mat in bpy.data.materials:
	#	mat.use_backface_culling = False
	for item in bpy.data.materials:
	   #Change Materials
	   #item.specular_hardness = 1
	   #item.game_settings.alpha_blend = 'CLIP'
	   item.use_backface_culling = True

def execute_cmd(os_str_cmd):
	process = subprocess.Popen(os_str_cmd, 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
	while True:
		output = process.stdout.readline()
		print(output.strip())
		# Do something else
		return_code = process.poll()
		if return_code is not None:
			print('RETURN CODE', return_code)
			# Process has finished, read rest of the output 
			for output in process.stdout.readlines():
				print(output.strip())
			break

def convert_textures_to_jpeg(jpeg_quality):
	print('Converting all input textures to JPEG, quality: ' + str(jpeg_quality))
	for file in glob.glob(texture_folder + '/' + "*.png"):
		im = Image.open(file)
		rgb_im = im.convert('RGB')
		rgb_im.save(file.replace("png", "jpg"), quality=jpeg_quality)
	
def configContainFileFormat(convertConfig, str):
	print(convertConfig['filetypes_to_convert'])
	#print('check: ' + len(convertConfig.filetypes_to_convert))
	
	for conf in convertConfig['filetypes_to_convert']:
		if(str.lower() in conf.lower()):
			print("Found " + str + " in file formats to convert")
			return True
	
	return False
	
def exportGLB(convertConfig,output_model,input_filename_without_ext,finalGLBexported):
	global output_tmp_root_folder
	print('Exporting GLB')
	output_model = input_filename_without_ext + ".glb"
	input_gltf_to_pack = output_tmp_root_folder + 'fbx2gltf/unpacked/' + input_filename_without_ext + '.gltf'
	print('Input GLTF file to pack to GLB: ' + input_gltf_to_pack)
	#bpy.ops.wm.save_as_mainfile(filepath=output_tmp_root_folder+"/tmpGLB.blend")
	#bpy.ops.wm.open_mainfile(filepath=output_tmp_root_folder+"/tmpGLB.blend")
	#bpy.ops.export_scene.gltf(export_format='GLB', filepath=input_gltf_to_pack)	
	##os.remove("./tmpGLB.blend")
	
	# unpack back the previously generated GLB
	#input_glb = convertConfig['output_folder'] + '/' + input_filename_without_ext + '.glb'
	
	out_GLB_folder = ''
	
	# we create a subfolder to receive the GLB file
	if(convertConfig['convert_textures_to_jpeg']):
		out_GLB_folder = convertConfig['output_folder'] + '/GLB-JPEG' 
	else:
		out_GLB_folder = convertConfig['output_folder'] + '/GLB' 
	
	if not os.path.exists(out_GLB_folder):
		os.makedirs(out_GLB_folder)
	
	os_str_cmd = current_exe_folder + '\\gltf.exe ' + ' Pack ' +  "\"" + input_gltf_to_pack +  "\""  +  ' ' +   "\""  + out_GLB_folder +  "\""  + '/'
	print('os_str_cmd: ' + os_str_cmd)
	print('Packing GLB')
	execute_cmd(os_str_cmd)
	
	os_str_cmd = current_exe_folder + '\\gltfpack.exe' + ' -noq -kn -ke ' + ' -i ' + "\"" + input_gltf_to_pack + "\"" + ' -o ' + "\"" + input_gltf_to_pack + "\""
	print('Optimizing GLB: ' + os_str_cmd)
	execute_cmd(os_str_cmd)
	
	#copy packed GLB as final GLB file
	#output_model = convertConfig['output_folder'] + '/' + input_filename_without_ext + ".glb"
	#print('Output model: ' + output_model)
	shutil.copy2(input_gltf_to_pack.replace('.gltf','.glb'), out_GLB_folder)
	
	finalGLBexported = True
	
def exportGLTF(convertConfig,output_model,input_filename_without_ext,finalGLBexported):
	print('Exporting GLTF')
	output_tmp_model = output_tmp_root_folder + '/' + input_filename_without_ext + ".gltf"
	
	#create a folder with the name of the model
	#gltf_folder = convertConfig['output_folder'] + '/' + input_filename_without_ext
	#if not os.path.exists(gltf_folder):
	#	# try:
	#	os.makedirs(gltf_folder)
	
	out_GLTF_folder = ''
	
	# we create a subfolder to receive the GLTF file
	if(convertConfig['convert_textures_to_jpeg']):
		out_GLTF_folder = convertConfig['output_folder'] + '/GLTF-JPEG' 
	else:
		out_GLTF_folder = convertConfig['output_folder'] + '/GLTF' 
	
	if not os.path.exists(out_GLTF_folder):
		os.makedirs(out_GLTF_folder)
	
	# copy everything from the 'Unpacked folder' to the out_GLTF_folder
	unpacked_gltf_from_fbx = convertConfig['output_folder']  + '/tmp/fbx2gltf/unpacked/'
	
	if(not convertConfig['convert_textures_to_jpeg']):
		inputFiles = Path(unpacked_gltf_from_fbx).glob("**/*.png")
		for f in inputFiles:
			shutil.copy2(f,out_GLTF_folder)
		
	inputFiles = Path(unpacked_gltf_from_fbx).glob("**/*.jpg")
	for f in inputFiles:
		shutil.copy2(f,out_GLTF_folder)
	
	inputFiles = Path(unpacked_gltf_from_fbx).glob("**/*.gltf")
	for f in inputFiles:
		shutil.copy2(f,out_GLTF_folder)
		
	inputFiles = Path(unpacked_gltf_from_fbx).glob("**/*.bin")
	for f in inputFiles:
		shutil.copy2(f,out_GLTF_folder)		
	
	return
	
	output_model = gltf_folder + '/' + input_filename_without_ext + ".gltf"
	#bpy.ops.wm.save_as_mainfile(filepath=output_tmp_root_folder+'/tmpGLTF.blend')
	#bpy.ops.wm.open_mainfile(filepath=output_tmp_root_folder+'/tmpGLTF.blend')
	
	#if(convertConfig['convert_textures_to_jpeg']):
	#	bpy.ops.export_scene.gltf(export_format='GLTF_SEPARATE', filepath=output_model, export_image_format='JPEG')
	#else:
	#	bpy.ops.export_scene.gltf(export_format='GLTF_SEPARATE', filepath=output_model)
	##os.remove("./tmpGLTF.blend")
	#os_str_cmd = current_exe_folder + '\\gltfpack.exe' + ' -noq -kn -ke ' + ' -i ' + output_model + ' -o ' + output_model
	#print('Optimizing GLTF: ' + os_str_cmd)
	#execute_cmd(os_str_cmd)
	
	##if we need to change the transparency of glass, we need to load back the PNG file
	#if(convertConfig['overwrite_glass_transparency']):
	#	#move the PNG of the glass
	#	inputFiles = Path(output_tmp_root_folder).glob("**/*.png")
	#	outputPath = gltf_folder
	#	
	#	for f in inputFiles:
	#		if 'glass' in f.name:
	#			shutil.copy2(f,gltf_folder)
	
	# unpack back the previously generated GLB
	input_glb = convertConfig['output_folder'] + '/' + input_filename_without_ext + '.glb'
	
	os_str_cmd = current_exe_folder + '\\gltf.exe ' + ' Unpack ' +  "\"" + input_glb +  "\"" + ' ' +  "\"" + gltf_folder + "\"" 
	print('os_str_cmd: ' + os_str_cmd)
	print('Unpacking GLB')
	execute_cmd(os_str_cmd)
	
	unpacked_gltf_from_fbx = fbx2gltf_result_folder + '/unpacked/' + input_filename_without_ext + '.gltf'
	
def exportOBJ(convertConfig,output_model,input_filename_without_ext,finalGLBexported):
	print('Exporting OBJ')
	
	out_OBJ_folder = ''
	
	# we create a subfolder to receive the OBJ file
	if(convertConfig['convert_textures_to_jpeg']):
		out_OBJ_folder = convertConfig['output_folder'] + '/OBJ-JPEG' 
	else:
		out_OBJ_folder = convertConfig['output_folder'] + '/OBJ' 
	
	if not os.path.exists(out_OBJ_folder):
		os.makedirs(out_OBJ_folder)
		
	output_model = out_OBJ_folder + '/' + input_filename_without_ext + ".obj"
	print('OBJ file : ' + output_model)
	bpy.ops.export_scene.obj(filepath=output_model)
	
	#search for the name of the material in the OBJ file, and replace the 9th line after it
	with open(output_model.replace('.obj','.mtl'),'w') as fp:
	
		#change the way textures are handled
		for m in bpy.data.materials:
		
			print('material name: ' + m.name + '\n')
			fp.write('newmtl ' + m.name + '\n')
			fp.write('Ns 225.000000' + '\n')
			fp.write('Ka 1.000000 1.000000 1.000000' + '\n')
			fp.write('Kd 0.800000 0.800000 0.800000' + '\n')
			fp.write('Ks 0.500000 0.500000 0.500000' + '\n')
			fp.write('Ke 0.000000 0.000000 0.000000' + '\n')
			fp.write('Ni 1.450000' + '\n')
			fp.write('d 1.000000' + '\n')
			fp.write('illum 2' + '\n')
			map_name = ''
			if(convertConfig['convert_textures_to_jpeg']):
				map_name = m.name + '_diffuse.jpg'
			else:
				map_name = m.name + '_diffuse.png'
			fp.write('map_Kd ' + map_name + '\n')
			
			#if 'metal' in map_name:
			#	try:
			#		shutil.copy2(convertConfig['texture_folder']+'/'+map_name,out_OBJ_folder + '/' + map_name)
			#	except FileNotFoundError as err:
			#		print('Error while copying file: ' + map_name)
			#	try:
			#		shutil.copy2(convertConfig['texture_folder']+'/'+map_name.replace('metal','metalness'),out_OBJ_folder + '/' + map_name)
			#	except FileNotFoundError as err:
			#		print('Error while copying file: ' + map_name.replace('metal','metalness'))				
			#else:
			#	shutil.copy2(convertConfig['texture_folder']+'/'+map_name,out_OBJ_folder + '/' + map_name)
			try:
				shutil.copy2(convertConfig['texture_folder']+'/'+map_name,out_OBJ_folder + '/' + map_name)
			except FileNotFoundError as err:
				print('Error while copying file: ' + map_name)
			
		
			nodes = m.node_tree.nodes
			#principled_node = t.nodes['Principled BSDF']
			# Get a principled node
			for n in nodes:
				if n.type == 'BSDF_PRINCIPLED':
					print('n.name: ' + n.name)
					for n2 in nodes:
						if n2.label == 'BASE COLOR':
							print('n2.name: ' + n2.name)
							principled = n
							base_color = n2 
			
							# Get the slot for the diffuse
							m.node_tree.links.new(base_color.outputs["Color"], principled.inputs['Base Color'])
		
	
	
	#bpy.ops.wm.save_as_mainfile(filepath=out_OBJ_folder+"/tmpGLB.blend")
	
	#f = open(out_OBJ_folder + '/' + 'tmp.mtl', "w")
	#f.write("Woops! I have deleted the content!")
	
							
	#search for the name of the material in the OBJ file, and replace the 9th line after it
	#with open(output_model.replace('.obj','.mtl')) as fp:
	#	line = fp.readline()
	#	print('MTL line: ' + line)
	#	
	#	while line:
	#		line = fp.readline()
	#		if line.startswith('newmtl'):
	#			material_name = line.replace('\n','')
	#			material_name = material_name.replace('newmtl ','')
	#			print('Material name: ' + material_name)
	#			while line != '':
	#				line = fp.readline()
	#				if line.startswith('map_'):
	#					line = 'map_Kd ' + material_name +'.png'
	#					shutil.copy2(convertConfig['texture_folder']+'/'+material_name +'.png',out_OBJ_folder + '/' + material_name +'.png')
	#					f.write(line)
	
	#f.close()
					
			
	
	## we need to change incorrects informations in the obj file
	#with(output_model, 
	
def exportUSDZ(convertConfig,output_model,input_filename_without_ext,finalGLBexported):
	global current_exe_folder
	print('Exporting USDZ')
	if(finalGLBexported == False):
		exportGLB(convertConfig,output_model,input_filename_without_ext,finalGLBexported)

	out_USDZ_folder = ''
	
	# we create a subfolder to receive the USDZ file
	if(convertConfig['convert_textures_to_jpeg']):
		out_USDZ_folder = convertConfig['output_folder'] + '/USDZ-JPEG' 
	else:
		out_USDZ_folder = convertConfig['output_folder'] + '/USDZ' 
	
	if not os.path.exists(out_USDZ_folder):
		os.makedirs(out_USDZ_folder)
	
	# we create a subfolder to receive the GLB file
	if(convertConfig['convert_textures_to_jpeg']):
		out_GLB_folder = convertConfig['output_folder'] + '/GLB-JPEG' 
	else:
		out_GLB_folder = convertConfig['output_folder'] + '/GLB' 
	
	if not os.path.exists(out_GLB_folder):
		os.makedirs(out_GLB_folder)
		
		
	output_model = out_GLB_folder + '/' + input_filename_without_ext + ".glb"
	print('USDZ file : ' + output_model)
	#bpy.ops.export_scene.obj(filepath=output_model)

		
	#current_exe_folder = current_exe_folder.replace(" ", "\ ")
	print('current_exe_folder: ' + current_exe_folder)
	#output_model = input_filename_without_ext + ".glb"
	print('output_model: ' + output_model)
	
	os_str_cmd = "\"" + current_exe_folder + '\\pxr_usd_min_alembic1710_py27_win64\\run_usdzconvert.cmd' + "\"" + ' ' +  "\"" + output_model +  "\""
	print('Converting to USDZ: ' + os_str_cmd)
	execute_cmd(os_str_cmd)
	shutil.move(output_model.replace('.glb','.usdz'),out_USDZ_folder)

def convert_FBX2GLTF(convertConfig):
	global current_exe_folder
	global glb_file_from_fbx
	global input_filename_with_ext
	global input_filename_without_ext
	
	# we will output the result of fbx2gltf in a subfolder of the '/tmp' folder
	fbx2gltf_result_folder = convertConfig['output_folder']  + '/tmp/fbx2gltf'
	#glb_file_from_fbx = convertConfig['filename_to_convert'].lower().replace("fbx","glb")
	glb_file_from_fbx =  fbx2gltf_result_folder + '/' + input_filename_without_ext + '.glb'
	print('TMP - glb_file_from_fbx: ' + glb_file_from_fbx)
	#os_str_cmd = current_exe_folder + '\\FBX2glTF-windows-x64.exe -b' + ' -i ' + "\"" + convertConfig['filename_to_convert'] + "\"" +  ' -o ' +  "\"" + glb_file_from_fbx + "\""
	os_str_cmd = current_exe_folder + '\\FBX2glTF-windows-x64.exe -b' + ' -i ' + "\"" + convertConfig['filename_to_convert'] + "\"" +  ' -o ' +  "\"" + glb_file_from_fbx + "\""
	print('os_str_cmd: ' + os_str_cmd)
	print('Converting to GLB: ' + glb_file_from_fbx)
	execute_cmd(os_str_cmd)
	
def unpackGLB2GLTF(convertConfig):
	global current_exe_folder
	global glb_file_from_fbx
	global unpacked_gltf_from_fbx
	
	fbx2gltf_result_folder = convertConfig['output_folder']  + '/tmp/fbx2gltf'
	glb_file_from_fbx =  fbx2gltf_result_folder + '/' + input_filename_without_ext + '.glb'
	
	os_str_cmd = current_exe_folder + '\\gltf.exe ' + ' Unpack ' +  "\"" + glb_file_from_fbx +  "\"" +  ' ' +  "\"" + fbx2gltf_result_folder +  "\"" + '/unpacked'
	print('os_str_cmd: ' + os_str_cmd)
	print('Unpacking GLB')
	execute_cmd(os_str_cmd)
	
	unpacked_gltf_from_fbx =  fbx2gltf_result_folder + '/unpacked/'  + input_filename_without_ext  + '.gltf'

	
	#optimize JPG
	#leanify
	

def generate_id(size=7, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def append_id(filename):
    name, ext = os.path.splitext(filename)
    return "{name}_{uid}{ext}".format(name=name, uid=generate_id(), ext=ext)

def modifyGlassTransparency(convertConfig):
	#first we need to check if there's 'glass' in a texture name, and create the RGBA version
	global imported_objects

	print('Modifying transparent values for material')

	# convert all images to jpg
	#for img in bpy.data.images:
		#img.filepath = img.filepath.replace('.png', '.jpg')
		#img.reload()		
	#	print(img.name)
	#	if 'glass' in img.name.lower():
	#		img_rgba = Image.new('RGBA', (img.width, img.height), color = 'red')
	#		img_rgba.putdata(img.getdata())
	#		img_rgba.putalpha(float(convertConfig['glass_transparency_value']))
	#		rgba_img_filepath = append_id(img.filepath)
	#		print('New image with alpha saved as: rgba_img_filepath')
	#		img_rgba.save(rgba_img_filepath)

	#go over all materials
	for m in bpy.data.materials:
		#only if there's 'glass in the name'
		if 'glass' in m.name:
			nodes = m.node_tree.nodes
			#principled_node = t.nodes['Principled BSDF']
			# Get a principled node
			principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
			base_color = next(n for n in nodes if n.label == 'BASE COLOR')
			img = base_color.image 
			#img.filepath = convertConfig['output_folder']  + '/tmp_glass_rgba.png'
			img.filepath_raw = convertConfig['output_folder'] + '/tmp' + '/' + m.name + '_rgba.png'
			img.file_format = 'PNG'
			img.save()
			img_rgb = Image.open(img.filepath)
			img_rgba = Image.new('RGBA', (img.size[0], img.size[1]), color = 'red')
			img_rgba.paste(img_rgb)
			img_rgba.putalpha(int(float(convertConfig['glass_transparency_value'])*255))
			rgba_img_filepath = append_id(img.filepath)
			img_rgba.save(rgba_img_filepath)
			print('New image with alpha saved as: ' +rgba_img_filepath)
			
			base_color.image = bpy.data.images.load(rgba_img_filepath)
			base_color.image.reload()
			
			# Get the slot for 'alpha'
			principled.inputs['Alpha'].default_value = float(convertConfig['glass_transparency_value'])
			m.blend_method = 'BLEND'
			m.node_tree.links.new(base_color.outputs["Alpha"], principled.inputs['Alpha'])
			
			#os.remove(rgba_img_filepath)
			files_to_delete.append(rgba_img_filepath)
			
def export_modifications_to_GLTF(convertConfig):
	
	unpacked_gltf_folder = convertConfig['output_folder']  + '/tmp/fbx2gltf/unpacked/'
	unpacked_gltf_file = unpacked_gltf_folder + '/' + input_filename_without_ext + '.gltf'

	#remove everything in the 'unpacked' folder
	files = glob.glob(unpacked_gltf_folder +'/*.*')
	for f in files:
		print('Filename : ' + f)
		os.remove(f)
			
	if(convertConfig['convert_textures_to_jpeg']):
		bpy.ops.export_scene.gltf(export_format='GLTF_SEPARATE', filepath=unpacked_gltf_file, export_image_format='JPEG')
	else:
		bpy.ops.export_scene.gltf(export_format='GLTF_SEPARATE', filepath=unpacked_gltf_file)
	
	bpy.ops.wm.save_as_mainfile(filepath=unpacked_gltf_folder+'/tmpGLTF.blend')		
	##os.remove("./tmpGLTF.blend")
	os_str_cmd = current_exe_folder + '\\gltfpack.exe' + ' -noq -kn -ke ' + ' -i ' + "\"" + unpacked_gltf_file + "\"" + ' -o ' + unpacked_gltf_file + "\""
	print('Optimizing GLTF: ' + os_str_cmd)
	execute_cmd(os_str_cmd)
	
def normalize_material_names():

	for m in bpy.data.materials:
		#only if there's 'glass in the name'
		if 'glass' in m.name:
			nodes = m.node_tree.nodes
			#principled_node = t.nodes['Principled BSDF']
			# Get a principled node
			principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
			base_color = next(n for n in nodes if n.label == 'BASE COLOR')
			img = base_color.image 
			#img.filepath = convertConfig['output_folder']  + '/tmp_glass_rgba.png'
			img.name = img.name.replace('_TMP_DEL_rgba','')

	#try to find back a texture name
	for m in bpy.data.materials:
		nodes = m.node_tree.nodes
		for n in nodes:
			if m.name is not None:
				for n in nodes:
					if n.label is not None and n.label is not '' and n.label == 'BASE COLOR':
						base_color = n
						img = base_color.image
						img.name = m.name

def clean_tmp_files(convertConfig):
	tmp_folder = convertConfig['output_folder']  + '/tmp/'
	#delete '/tmp' folder and all contents
	shutil.rmtree(tmp_folder, ignore_errors=False, onerror=None)
	
	#for f in files_to_delete:
	#	print('file to delete: ' + f)
	#	if '_rgba.png' in f:
	#		os.remove(f)
	
	#Clean all the PNG files generated for the Glass material
	files = os.listdir(convertConfig['output_folder'])
	
	for image in files:
		if image.lower().endswith(".png"):
			os.remove(os.path.join(convertConfig['output_folder'], image))

def createTempFolders(convertConfig, input_model):
	global input_filename_with_ext
	global input_filename_without_ext
	global input_file_filepath
	global output_tmp_root_folder
	
		
	input_filename_with_ext = os.path.split(input_model)[1]
	print('Filename with extension: ' + input_filename_with_ext + " ; " + input_filename_with_ext.split('.')[1])
	
	input_filename_without_ext = input_filename_with_ext.split('.')[0]
	print('Filename without extension: ' + input_filename_without_ext)
		
	input_file_filepath = os.path.split(input_model)[0]
	output_tmp_root_folder = convertConfig['output_folder']  + '/tmp/'
	
	print('Output folder: ' + convertConfig['output_folder'])
	print('Temporary folder is: ' + output_tmp_root_folder)
	if not os.path.exists(output_tmp_root_folder):
		# try:
		os.makedirs(output_tmp_root_folder)

def main():
	global model_file
	global texture_folder
	global model_folder
	global current_exe_folder
	global output_tmp_root_folder
	glb_file_from_fbx
	current_exe_folder = os.getcwd()
	
	##1. retrieve the JSON config file, passed as argument
	argv = sys.argv
	print(argv)
	argv = argv[argv.index("--") + 1:]	# get all args after "--"
	print(argv)	 # --> ['example', 'args', '123']
	
	input_model = argv[0]
	input_format = argv[1]
	
	print('Input model: ' + input_model)
	print('Input format: ' + input_format)
	
	input_model = input_model.replace("%20", " ")
	input_format = input_format.replace("%20"," ")
	
	convertConfig = json.loads(input_format)
	
	print("%%")
	print('Convert config:')
	print(convertConfig)
	print("%%")
	print(convertConfig['convert_textures_to_jpeg'])
	print(convertConfig['jpeg_texture_quality'])
	print(convertConfig['filetypes_to_convert'])
	print(convertConfig['remove_shadow_plane'])
	print(convertConfig['overwrite_glass_transparency'])
	print(convertConfig['glass_transparency_value'])
	print("%%")
	
	#2. create temp folders
	createTempFolders(convertConfig, input_model)
	
	#3. always convert the original FBX to a GLB file
	convert_FBX2GLTF(convertConfig)
	
	#4. unpack resulting GLB to GLTF
	unpackGLB2GLTF(convertConfig)

	# Textures Folder
	#if(FOLDER_TEXTURE_AUTO_NAMING):
	#	model_file = input_model
	#	texture_folder = os.path.dirname(os.path.abspath(model_file)) + '/textures/'
	#	debug_print('Model file path is: ' + model_file)
	#	print('Model file path is: ' + model_file)
	#	debug_print('Model file path absolute path: ' + os.path.abspath(model_file))
	#	print('Model file path absolute path: ' + os.path.abspath(model_file))
	#	debug_print('Texture folder is: ' + texture_folder)
	#	print('Texture folder is: ' + texture_folder)
		
	#5. we clear the default scene in blender (Cube, Light, Camera...)
	clear_default_scene()
	
	#6. test if we need to convert any image to JPEG
	if(convertConfig['convert_textures_to_jpeg']):
		replace_png2jpeg(convertConfig)
	
	#model_folder = os.path.dirname(os.path.abspath(model_file))
	#debug_print('Model folder: ' + model_folder)
	#print('Model folder: ' + model_folder)
	
	# we open the GLB file only
	#print('Working with file: ' + glb_file_from_fbx)
	#bpy.ops.import_scene.gltf(filepath=glb_file_from_fbx)	  
		
	#7. we open the unpacked GLB file only
	print('Working with file: ' + unpacked_gltf_from_fbx)
	bpy.ops.import_scene.gltf(filepath=unpacked_gltf_from_fbx)	 
	
	#8. corrected all the material names that have been erased by FBX2GLTF
	normalize_material_names()
	
	#open_materials()
	#9. correct transparency if necessary
	if(convertConfig['overwrite_glass_transparency']):
		modifyGlassTransparency(convertConfig)

	#10. clean unused nodes
	list_unused_nodes()
	
	#11. sete single sided for the faces, avoid some errors with objects for GLTF
	set_single_sided()
	
	#12. check if we need to remode the shadow plane
	if(convertConfig['remove_shadow_plane'] == True):
		remove_shadow_plane()
		
	#13. export all modifications to unpacked GLTF file
	export_modifications_to_GLTF(convertConfig)
	
	finalGLBexported = False
	
	output_model = ""	
	
	if(configContainFileFormat(convertConfig,'GLB')):
		exportGLB(convertConfig,output_model,input_filename_without_ext,finalGLBexported)
	if(configContainFileFormat(convertConfig,'GLTF')):
		exportGLTF(convertConfig,output_model,input_filename_without_ext,finalGLBexported)
	if(configContainFileFormat(convertConfig,'OBJ')):
		exportOBJ(convertConfig,output_model,input_filename_without_ext,finalGLBexported)		
	if(configContainFileFormat(convertConfig,'USDZ')):
		exportUSDZ(convertConfig,output_model,input_filename_without_ext,finalGLBexported)				
		
	#clean_tmp_files(convertConfig)
		
	return
	
main()