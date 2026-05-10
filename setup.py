from cx_Freeze import setup, Executable

setup(
    executables=[
        Executable("main.py"),
        Executable("startup_manager.py")
    ]
)
