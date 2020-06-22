#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 14:57:34 2020

@author: isapoetzsch
"""
#Playground
import pandas as pd
import numpy as np
import os
import math
import logging
import col_to_excel
from col_to_excel import col_to_excel
import sbol2
from sbol2 import Document, Component, ComponentDefinition
from sbol2 import BIOPAX_DNA, Sequence, SBOL_ENCODING_IUPAC


cwd = os.path.dirname(os.path.abspath("__file__")) #get current working directory
path_blank = os.path.join(cwd, "darpa_template_blank.xlsx")
path_filled = os.path.join(cwd, "darpa_template.xlsx")


table = pd.read_excel (path_filled, sheet_name = "Composite Parts", header = None)
    
list1 = []
d = dict()
for index, row in table.iterrows():
    if row[0] == "Collection Name:":
        d[index] = None
        list1.append(index)
        for entry in list1:
            while not all(table.iloc[row] == None):
                d[entry] == index
        
