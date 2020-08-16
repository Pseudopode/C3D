import eel, os, random
import subprocess
import tkinter as Tk
from tkinter import *

from tkinter import filedialog
from tkinter.filedialog import askopenfilename

import json
from enum import Enum

import PIL

def serialize_config(obj):
	output_str = "{"
	output_str = output_str + '"filename_to_convert"' + " : " + "\"" + obj.filename_to_convert.replace(" ","%20")+ "\""  + ","
	output_str = output_str + '"filepath"' + " : " + "\"" + obj.filepath.replace(" ","%20") + "\"" + ","
	output_str = output_str + '"texture_folder"' + " : " + "\"" + obj.texture_folder.replace(" ","%20") + "\""  + ","
	output_str = output_str + '"filetypes_to_convert"' + ": ["
	
	filetype_str = ""
	for filetype in obj.filetypes_to_convert:
		#if(filetype == "OBJ"):
		#	filetype_str = filetype_str + '"OBJ"' + "," 
		#if(filetype == "GLTF"):
		#	filetype_str = filetype_str + '"GLTF"' + "," 
		#if(filetype == "GLB"):
		#	filetype_str = filetype_str + '"GLB"' + "," 		
		#if(filetype == "USDZ"):
		#	filetype_str = filetype_str + '"USDZ"' + "," 	
		filetype_str = filetype_str +"\"" + filetype + "\"" + ","

	if(filetype_str.endswith(",")):
		filetype_str = filetype_str[:-1]
	
	print("Choosen filetype: " + filetype_str)
	
	output_str = output_str + filetype_str
	
	output_str = output_str +"]" + ","
	output_str = output_str + '"output_folder"' + " : " + "\"" + obj.output_folder.lower().replace(" ","%20") + "\"" + ","
	output_str = output_str + '"convert_textures_to_jpeg"' + " : " + str(obj.convert_textures_to_jpeg).lower() + ","
	output_str = output_str + '"jpeg_texture_quality"' + " : " + str(obj.jpeg_texture_quality).lower() + ","
	output_str = output_str + '"remove_shadow_plane"' + " : " + str(obj.remove_shadow_plane).lower() + ","
	output_str = output_str + '"overwrite_glass_transparency"' + " : " + str(obj.overwrite_glass_transparency).lower() + ","
	output_str = output_str + '"glass_transparency_value"' + " : " + "\"" + str(obj.glass_transparency_value).lower() + "\""
	output_str = output_str + "}"
	
	#sanity check
	output_str = output_str.replace("\\","/")
	
	print('Test: ' + output_str)
	
	return output_str

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

convertConfig = ConvertConfig(filename_to_convert="", filepath="", texture_folder="", filetypes_to_convert=[], output_folder="", convert_textures_to_jpeg=False, jpeg_texture_quality=80, remove_shadow_plane=False, overwrite_glass_transparency=False, glass_transparency_value=0.5)


######

#from https://github.com/samuelhwilliams/Eel/issues/86
from pathlib import Path

HOME = str(Path.home())

create_obj_fileformat = False
create_usdz_fileformat = False
create_gltf_fileformat = False
create_glb_fileformat = False

file_format = ""


	

@eel.expose
def get_root():
    return HOME
    
@eel.expose
def get_path_infos(path):
    try:
        files = os.listdir(path)
        real_files = [f for f in files if os.path.isfile(os.path.join(path, f))]
        real_dirs = [f for f in files if os.path.isdir(os.path.join(path, f))]
    except PermissionError:
        eel.alert_error("Can't read this files")
        return {"dirs": [], "files": []}
    except Exception as e:
        #do some things
        return {"dirs": [], "files": []}
    return {"dirs": real_dirs, "files": real_files}
	
@eel.expose
def btn_ChooseFilePathClick():
	root = Tk()
	root.withdraw()
	root.wm_attributes('-topmost', 1)
	folder = filedialog.askopenfilename()
	return folder
	
@eel.expose
def btn_ChooseOutputFolderPathClick():
	root = Tk()
	root.withdraw()
	root.wm_attributes('-topmost', 1)
	folder = filedialog.askdirectory()
	return folder
	
###

eel.init('web')

@eel.expose
def setOBJFileFormat(val):
	global convertConfig
	#create_obj_fileformat = val
	#file_format = file_format + ";OBJ"
	print('setOBJFileFormat: ' + str(val))
	if(val):
		convertConfig.filetypes_to_convert.append("OBJ")
	else:
		if( 'OBJ' in convertConfig.filetypes_to_convert):	
			convertConfig.filetypes_to_convert.remove("OBJ")
	return

	
@eel.expose
def setGLTFFileFormat(val):
	global convertConfig
	#create_gltf_fileformat = val
	#file_format = file_format + ";GLTF"
	print('setGLTFFileFormat: ' + str(val))
	if(val):
		convertConfig.filetypes_to_convert.append("GLTF")
	else:
		if( 'GLTF' in convertConfig.filetypes_to_convert):	
			convertConfig.filetypes_to_convert.remove("GLTF")
	return
	
@eel.expose
def setGLBFileFormat(val):
	global convertConfig
	#create_glb_fileformat = val
	#file_format = file_format + ";GLB"
	print('setGLBFileFormat: ' + str(val))
	if(val):
		convertConfig.filetypes_to_convert.append("GLB")
	else:
		if( 'GLB' in convertConfig.filetypes_to_convert):	
			convertConfig.filetypes_to_convert.remove("GLB")
	return
	
@eel.expose
def setUSDZFileFormat(val):
	global convertConfig
	#create_usdz_fileformat = val
	#file_format = file_format + ";USDZ"
	print('setUSDZFileFormat: ' + str(val))
	if(val):
		convertConfig.filetypes_to_convert.append("USDZ")
	else:
		if( 'USDZ' in convertConfig.filetypes_to_convert):
			convertConfig.filetypes_to_convert.remove("USDZ")
	return
	
@eel.expose
def setTexturesToJPEG(val):
	global convertConfig
	#TODO: assert val is BOOL
	print('setTexturesToJPEG: ' + str(val))
	convertConfig.convert_textures_to_jpeg = val
	return
	
@eel.expose
def setJPEGQuality(val):
	global convertConfig
	#TODO: assert val is INT
	print('setJPEGQuality: ' + str(val))
	convertConfig.jpeg_texture_quality = val
	return
	
@eel.expose
def setShadowPlaneIsRemoved(val):
	global convertConfig
	#TODO: assert val is BOOL
	print('setShadowPlaneIsRemoved: ' + str(val))
	convertConfig.remove_shadow_plane = val
	return	
	
@eel.expose
def setOverwriteGlassTransparencyValue(val):
	global convertConfig
	#TODO: assert val is BOOL
	print('setOverwriteGlassTransparencyValue: ' + str(val))
	convertConfig.overwrite_glass_transparency = val
	return

@eel.expose
def setGlassTransparencyValue(val):
	global convertConfig
	#TODO: assert val is FLOAT
	print('setGlassTransparencyValue: ' + str(val))
	convertConfig.glass_transparency_value = val
	return
	
@eel.expose
def setOutputFolder(val):
	global convertConfig
	#TODO: assert val is STR
	print('setOutputFolder: ' + str(val))
	convertConfig.output_folder = val
	print('Output folder for converted 3D file is: ' + val)
	return	
	
@eel.expose
def pick_file(folder):
	if os.path.isdir(folder):
		return random.choice(os.listdir(folder))
	else:
		return 'Not valid folder'
		
@eel.expose
#def apply_blender_conv(file_to_open,file_format):
def apply_blender_conv(file_to_open):
	global convertConfig
	
	#### DIRTY HACK !!
	tmp_val = convertConfig.overwrite_glass_transparency
	convertConfig.overwrite_glass_transparency = convertConfig.glass_transparency_value
	convertConfig.glass_transparency_value = tmp_val
	#### END OF DIRTY HACK !!
	
	print("File to open: " + file_to_open)
	print("File format: " + file_format)
	
	
	convertConfig.filename_to_convert = file_to_open
	
	texture_folder = os.path.dirname(os.path.abspath(file_to_open)) + '/textures/'
	convertConfig.texture_folder = texture_folder
	
	model_folder = os.path.dirname(os.path.abspath(file_to_open))
	convertConfig.filepath = model_folder
	
	json_config = serialize_config(convertConfig)
	print("")
	print("$")
	print(json_config)
	print("$")
	print("")
	
	#subprocess.call(["blender_bat.bat", file_to_open, file_format])
	
	#sanitize spaces in folder paths
	file_to_open = file_to_open.replace(" ", "%20")
	
	subprocess.call(["blender_bat.bat", file_to_open, json_config])	
	return
	
eel.start('index.html', size=(1030, 800))
