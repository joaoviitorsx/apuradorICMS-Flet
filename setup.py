from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os"], 
    "include_files": [".env"]
}

setup(
    name="ApuradorICMS",
    version="0.1",
    description="Exemplo de aplicação com cx_Freeze",
    options={"build_exe": build_exe_options},
    executables=[Executable("app.py", target_name="apuradorICMS.exe")]
)
