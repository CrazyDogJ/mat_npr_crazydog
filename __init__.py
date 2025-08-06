import bpy
from . import main_panel

include_files = {
    main_panel,

}

def register():
    for file in include_files:
        file.register()

def unregister():
    for file in include_files:
        file.unregister()

if __name__ == "__main__":
    register()