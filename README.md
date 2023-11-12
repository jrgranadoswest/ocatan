
# Catanova
Settlers of Catan AI

## Dev Setup

First, clone the repository and enter the directory.
Create a Python virtual environment & install requirements. Specifics of 
creating venv may vary; see [here](https://docs.python.org/3/library/venv.html) for help.
```
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## Running the program

To run the program with the visual display, simply start the python script 
first and then open index.html in a browser. 
```
python ./main.py
firefox ./frontend/index.html
```

## Nomenclature standards
Within the code, certain names are standardized to improve readability and 
maintainability.

Most resource hexes could be identified by different names, at the very least 
differing based on references to the environment portrayed by the hex, or the 
actual resource it produces (e.g. "Forest" hex vs "Lumber"/"Wood" hex).
Therefore, the following names and abbreviations have been used throughout the 
codebase to refer to the hexes and the resources they yield:
Brick   (B)
Grain   (G)
Lumber  (L)
Ore     (O)
Wool    (W)
Desert  (D)
Water   (E) (Sometimes useful to denote the shoreline locations; 'E' for empty)

Dev card names & abbreviations:
Knight (K)
VP Card (VP)
Road builder (RB)
Mono (M)
YOP (Y)
