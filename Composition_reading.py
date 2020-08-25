#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 14:57:34 2020

@author: isapoetzsch
"""
#Set up
import pandas as pd
import numpy as np
import os
import logging
from col_to_excel import col_to_excel
import sbol2
from sbol2 import Document, PartShop, SO_GENE
import re

cwd = os.path.dirname(os.path.abspath("__file__")) #get current working directory
path_filled = os.path.join(cwd, "darpa_template.xlsx")
path_blank = os.path.join(cwd, "templates/darpa_template_blank.xlsx")

#read in the whole sheet below metadata
startrow_composition = 9
sheet_name = "Composite Parts"
table = pd.read_excel (path_filled, sheet_name = sheet_name, 
                       header = None, skiprows = startrow_composition)

#Load Metadata and Quality Check
nrows = 8
use_cols = [0,1]
filled_composition_metadata = pd.read_excel (path_filled, sheet_name = sheet_name,
                              header= None, nrows = nrows, usecols = use_cols)
blank_composition_metadata = pd.read_excel (path_blank, sheet_name = sheet_name,
                              header= None, nrows = nrows, usecols = use_cols)
 
comparison = np.where((filled_composition_metadata == blank_composition_metadata)|(blank_composition_metadata.isna()), True, False)
excel_cell_names = []
for column in range(0, len(use_cols)):
    for row in range(0, comparison.shape[0]):
        col = use_cols[column]
        excel_cell_names.append(f"{col_to_excel(col+1)}{row+1}")
excel_cell_names = np.reshape(excel_cell_names, comparison.shape, order='F')
excel_cell_names = pd.DataFrame(excel_cell_names)
excel_cell_names.where(np.logical_not(comparison))

if not(comparison.all()) :
    logging.warning("Some cells do not match the template")
    for number in range(0, nrows-1) :
        if filled_composition_metadata.iloc[number, 0] != blank_composition_metadata.iloc[number, 0]:
            logging.warning(f"""The excel cell {excel_cell_names.loc[number, 0]} has been corrupted and 
                  should contain {blank_composition_metadata.iloc[number, 0]}""")
          

#Load Libraries required for Parts
libraries = dict()
if table.iloc[0][0] == "Libraries" and table.iloc[0][1] == "Abbreviations":
    for index, row in table.iloc[1:len(table)].iterrows():
        if row[0] == "Composite DNA Parts" or row.dropna().empty: 
            break
        else:
            #if there is no abbreviation, use full name as key
            if not pd.isnull(table.iloc[index][1]):
                libraries[table.iloc[index][1]] = table.iloc[index][0]
            else:
                libraries[table.iloc[index][0]] = table.iloc[index][0]


#Loop over all rows and find those where each block begins
compositions = dict()
list_of_rows = []
all_parts = []
labels = np.array(["Collection Name:", "Name:", "Description:", "Strain (optional)",
          "Integration Locus (optional)", "Part Sequence:"])
#loop over all rows in sheet
for index, row in table.iterrows():
    
    #check if six rows starting from current row equal the preset labels
    labs = np.asarray(table.iloc[index : index+6][0])
    comparison = labs == labels 
    
    #if labels do match
    if row[0] == "Collection Name:" and comparison.all() :
        collect_name = table.iloc[index][1]
        
        #see if the collection name already exists in compositions dictionary
        try:
            #if it does use the existing dictionary
            collection_dict = compositions[collect_name]
        except:
            #if not create a new one
            collection_dict = {}
            
        columns = 0
        #for every 'name' row cycle through the columns
        for column in range(1,len(table.iloc[index+1])): 
            part_name = table.iloc[index+1][column]
            #if the column isn't empty
            if type(part_name) is str:
                collection_dict[part_name] = {"Description" : table.iloc[index+2][column],
                                                  "Parts" : {}}
                columns += 1
        #add the index of collection name row to the list of rows
        #and add number of columns used
        list_of_rows.append((index, columns))  
                                                  
        #add new items to compositions dictionary
        compositions[collect_name] = collection_dict
    
            
# def get_parts(list_of_rows, table):
len_list_of_rows = len(list_of_rows)
for index, value in enumerate(list_of_rows):
    row_index = value[0]
    collect_name = table.iloc[row_index][1]
    #for column in the row with names in it
    for column in range(1,value[1]+1):
        part_name = table.iloc[row_index+1][column]
        
        #if it is the last block in the spreadsheet
        if index == len_list_of_rows-1:
            #read from the parts row to the end of the table
            parts = table.iloc[row_index+5: len(table)][column].dropna()
        else:
            #if not last block, read until next block
            parts = table.iloc[row_index+5: list_of_rows[index+1][0]][column].dropna()

        if len(parts) == 0:
            logging.warning(f"The design {part_name} in the collection {collect_name} was empty and thus removed")
            del compositions[collect_name][part_name]
                
        else:
            compositions[collect_name][part_name]['Parts'] = parts.tolist()
            all_parts+=parts.tolist()

#delete any collections with no composite parts
empty_collect = []
for key in compositions:
    if len(compositions[key]) == 0:
        empty_collect.append(key)
for key in empty_collect:
    logging.warning(f"The collection {key} was empty and thus removed")
    del compositions[key]
    
    
all_parts = set(all_parts) #set eliminates duplicates



#Check if Collection names are alphanumeric and separated by underscore
for key in compositions:
    old = key #for error warning
    title = key.replace('_', '') #remove underscore to use isalnum()
    if title.isalnum():
        print(f"Collection name {key} is valid")
    else: #replace special characters with numbers
        for letter in title:
            if ord(letter) > 122:
                #122 is the highest decimal code number for common latin letters or arabic numbers
                #this helps identify special characters like ä or ñ, which isalnum() returns as true
                #the characters that don't meet this criterion are replaced by their decimal code number separated by an underscore
                key = key.replace(letter, str( f"_{ord(letter)}"))
            else:
                letter = re.sub('[\w, \s]', '', letter) #remove all letters, numbers and whitespaces
                #this enables replacing all other special characters that are under 122
                if len(letter) > 0:
                    key = key.replace(letter, str( f"_u{ord(letter)}"))
        temp_collect = compositions[old]
        del compositions[old]
        compositions[key] = temp_collect
        print(f"Collection name {old} was not valid and replaced by {key}")


doc = Document()
sbol2.Config.setOption('sbol_typed_uris', False)

for library in libraries:
    library = sbol2.PartShop(libraries[library])
    for part in all_parts:
        try:
            library.pull(part, doc)
        except:
            print(f"This part {part} was not in library {library}")


for collection in compositions:
    for design in compositions[collection]:
        composite_design = doc.componentDefinitions.create(design)
        composite_design.assemblePrimaryStructure(compositions[collection][design]["Parts"])
        composite_design.compile()
        composite_design.sequence

        if type(compositions[collection][design]["Description"]) is str:
            composite_design.description = compositions[collection][design]["Description"]

doc.write("Compositions1.xml")

with open("Compositions1.xml", "r") as file:
    data = file.read()
    
with open("Compositions1.xml", "w") as file:
    data = data.replace("<prov:endedAtTime>2017-03-06T15:00:00+00:00</prov:endedAtTime>", "<prov:endedAtTime>2017-03-06T15:00:00.000+00:00</prov:endedAtTime>")
    file.write(data)