import os
import pdg

# путь к проекту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# pdg.sqlite лежит рядом с этим файлом
os.environ["PDG_DATA"] = BASE_DIR

# создаётся ОДИН РАЗ на worker
PDG_API = pdg.connect()

