#!/usr/bin/env python
# # -*- coding: utf-8 -*-


"""
This is the module of deepclouds introducing all const defines
used in the package.
"""


__author__ = "Daniel Koguciuk"
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Daniel Koguciuk"
__email__ = "daniel.koguciuk@gmail.com"
__status__ = "Development"


import os


ROOT_DIR = os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
"""
The root directory of the deepclouds package.
"""

DATA_DIR = os.path.join(ROOT_DIR, "data")
"""
Data directory for the modelnet data to be downloaded and stored.
"""

DATA_MODELNET40_URL = 'https://shapenet.cs.stanford.edu/media/modelnet40_ply_hdf5_2048.zip'
"""
URL to the modelnet data.
"""

DATA_MODELNET40_DIR = os.path.join(DATA_DIR, 'modelnet40_ply_hdf5_2048')
"""
Extracted modelnet data directory.
"""

CLASS_NAMES_FILE = os.path.join(DATA_MODELNET40_DIR, 'shape_names.txt')
"""
File with class names.
"""

DATA_SHAPENET55_DIR = os.path.join(DATA_DIR, 'shapenet_core55_1024')
"""
Directory with shapenet_core55 containing h5 files.
"""

DATA_MODELNET40_SAMPLED_DIR = os.path.join(DATA_DIR, 'modelnet40_downsampled')
"""
Downsampled ModelNet40 data directory.
"""

LOGS_DIR = os.path.join(ROOT_DIR, "logs")
"""
Directory for logs for tensorboard.
"""

MODELS_DIR = os.path.join(ROOT_DIR, "models")
"""
Directory for models saving and restoring.
"""

# Create all needed dirs
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)
if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)
if not os.path.exists(MODELS_DIR):
    os.mkdir(MODELS_DIR)
