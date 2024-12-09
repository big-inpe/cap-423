import importlib
import pkg_resources

libraries = [
    "requests", "beautifulsoup4", "numpy", "pandas",
    "geopandas", "shapely", "pyproj", "rasterio",
    "pystac-client", "folium", "matplotlib"
]

# Abrir o arquivo requirements.txt para escrita
with open("requirements.txt", "w") as req_file:
    for lib in libraries:
        try:
            version = pkg_resources.get_distribution(lib).version
            req_file.write(f"{lib}=={version}\n")  # Escrever no arquivo
            print(f"{lib}: {version}")
        except Exception as e:
            print(f"{lib}: Not installed or version unavailable.")

