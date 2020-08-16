# C3D - V0.2 - Alpha
3D File Format Converter
##DON'T USE THIS APP IN PRODUCTION YET, IT'S NOT PROPERLY TESTED!

!(./Documentation/title_screen.jpg)

# How to use
C3D is a 3D file format converter.
To run it, double-click on ##C3D_V1_0.exe##
C3D can take some times to fully display.

It takes .FBX files as inputs, and outputs either .GLB, .GLTF, .USDZ or .OBJ

The project uses various open-souce libs and apps.

To use C3D on a 3D file, you must first click on the *Choose Input file* button. You then click on the *Choose output folder* button.

You must click at least on one output format (either *OBJ*, *GLTF*, *GLB* or *USDZ*). You can choose several of them.

After choosing the output file format(s), you can choose the convert the textures of the 3D model to *JPEG files*, and specify a *quality level* for the compression.

By clicking on *Remove Shadow plane*, you will rip from the file model hierarchy any plane embedded in the model that could act as a *shadow catcher*.

You can specify that *Glass* material will be trasnparent (in fact, any material having *glass* in its name), and overwrite the *Glass Transparency* value. The value is going to be written as the alpha value of the diffuse's PNG file. 

When everything is set, you can click on *Convert file*.

In the output folder, a new folder, per file format, is going to be created, hosting the converted file.

!(./Documentation/output_folder.jpg)

# How is it created
The GUI of the app is written in HTML.
The HTML app is then integrated with a Python module, ##eel##, as an single .exe file. 
Behind the scene, C3D call [Blender](https://www.blender.org/) to operates on the 3D files.
A python file (`fbx_2_other.py`) specify the various actions that Blender will apply on the 3D model.

[FBX2GLTF](https://github.com/facebookincubator/FBX2glTF) is used to convert FBX files to GLTF.

[USDZCONVERT_Windows] (https://github.com/tappi287/usdzconvert_windows) is used to convert GLB files to USDZ.

[glTF-Shell-Extensions](https://github.com/Pseudopode/glTF-Shell-Extensions) is used, in its command line variant, to Pack and Unpack GLTF/GLB files.

[MeshOptimizer](https://github.com/zeux/meshoptimizer) is used to optimize the gltf/glb files.

# How to compile
For the moment, it's best to have the command line also displayed along the GUI version, to help debugging the app.

The build the app with the visible command line, double on the `debug_create_app.bat`.

If you want to try the app without the command line as visible, you can click on `create_app.bat`.

# Hierarchy
[TO DO]
'C3D-root'/: source code + batch files + fbx_2_other.py (to copy to the 'dist' folder)
./web/: html + images + js + CSS
./dist/: C3D_V1_0.exe + fbx_2_other.py + Newtonsoft.Json.dll + gltf.exe + gltfpack.exe
./dist/pxr_usd_min_alembic1710_py27_win64/: USDZConvert
./dist/blender_281: contain a 'standard' Blender unzipped distribution. ##YOU NEED TO UNPACK ONE BLENDER DISTRIBUTION HERE, TO MAKE C3D WORKS!##

# JSON documentation
To exchange commands, the C3D app is using a JSON file, passed on the command line to Blender.
IF you don't want to use the GUI of C3D, you can still pass a JSON string manually.

[TO DO] : document the JSON string.

# Conversion steps
[TODO] : documentation.

# Current app limitations
* C3D only works for the moment with an FBX file as input
* C3D doesn't properly works if there is a space in the aprent path somewhere
* FBX2GLTF doesn't take into account the normal maps, and Blender doesn't correct it for the moment
* GLTF files have a temporary bug, where the Glass PNG file isn't copied back in the GLTF-* folder
* Works only on Windows
* The 'tmp' folder, where everything is temporarily stored to work with isn't deleted yet
* JPEG/PNG files aren't yet minified/stripped
* The OBJ files are using MTL to describe the materials. Blender can't output properly images in the MTL if they aren't connected directly to the 'Principled BSDF'.
* Update the batch files that generates the .exe to also copy the `fbx_2_other.py`.
* USDZCONVERT_windows embedd its own blender distribution. In the future, it could good to use the one in Blender.