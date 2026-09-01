================================================================================
YOLOv8 Training Module README
================================================================================

Directory Overview
------------------
This directory contains the machine learning training pipeline for the SEEZY object detection system. It is designed to fine-tune a YOLOv8 architecture on a custom dataset of supermarket products to generate weights for edge inference.

File Overview
-------------
* YOLOv8 Training.ipynb: A Jupyter Notebook (optimized for Google Colab) that handles dataset configuration, model initialization, hyperparameter definition, PyTorch GPU training, and exporting the final trained weights.

Setup & Installation
--------------------
* Designed to run in a Google Colab environment with Hardware Acceleration (GPU) enabled.
* Requires mounting Google Drive to access the persistent dataset and to save training checkpoints/results.
* Dependencies: `ultralytics`, `torch`.

How to Use / Execution
----------------------
* Open the notebook in Google Colab, mount the drive, and execute the cells sequentially.
* The script dynamically generates the `data.yaml` file mapping the dataset paths and class names before initiating the training loop.

Dependencies & Interactions
---------------------------
* Requires a strictly formatted YOLO dataset (images/labels split into train/val directories).
* Outputs `.pt` (PyTorch) and `.onnx` (Open Neural Network Exchange) files. These exported weights are the direct dependencies for both the Windows Inference and Linux Inference modules.