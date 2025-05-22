# Capture node notes
This script integrates the connection and capture of the cameras, as well as the previsualization of those.

## Setup
Run the following commands to setup the virtual environment in VS_Code.

**Notes**
The SDK of the Itala cameras can produce certain incompatibilities with visualization libraries, such as matplotlib.
The working setup on a windows 11 machine is the following: 
* Install the latest version of [Itala SDK](https://www.opto-e.com/en/products/itala-g-series#downloads)
* Install Python 3.12
* Create virtual environment
    * Ctrl+Shift+P
    * Install modules in requirements.txt
```
pip install -r requirements.txt
```
* Install the itala module located on the install path of the sdk
    * note that the absolute path of the wheel (*.whl) could differ.
```
pip install "C:\Program Files\Opto Engineering\Itala SDK\Development\bindings\itala-1.4.3-cp311-abi3-win_amd64.whl"
```

## Usage
Follow and comments in ```captureNode.py```
