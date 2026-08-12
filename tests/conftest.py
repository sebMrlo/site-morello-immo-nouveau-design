# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# rend importables les modules à la racine du repo (facture_gen, parser, facture)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
