from genericpath import isdir
import Zone
import numpy as np
from tqdm import tqdm, tqdm_gui
import os
#from scipy.sparse import coo_matrix


class CAE_Decoder:
    #Func: Decode_dat_file
    #Inputs:
    #   path: the path of the dat file.
    #   return: the decoded CAE data structure.
    #   description: Decode a given CAE data. The file structure of the .dat file is default.
    
    Title = ''
    Variables = []
    Var_count = -1
    Zones = []
    
    def __init__(self):
        
        return


    def Decode_dat_file(self, path):
        file_object = open(path, 'r', encoding="UTF-8")
        raw_content = file_object.read()
        file_object.close()
        
        paragraphs = raw_content.split("ZONE  T=")
        
        # Processing header first, extracting title and variables:
        header_lines = paragraphs[0].split("\n")
        for line in header_lines:
            line = line.strip()
            # Extracting title
            if line.startswith('TITLE'):
                tokens = line.split('=')
                self.Title = tokens[1].replace('"', '')
            
            # Extracting variables
            if line.startswith('VARIABLES'):
                tokens = line.split('=')
                _vars = tokens[1].replace('"', '').split(' ')
                for var in _vars:
                    self.Variables.append(var)
                self.Var_count = len(self.Variables)
        
        # Each of the remaining paragraphs represent a ZONE, process them using the same logic:
        for i in range(1, len(paragraphs)):
            if i > 1:
                # Thus far we only decode the first Zone, i.e. fluid zone. The rest of the zones have problem understanding their organization
                # consider the rest as future works.
                break
            #Decoding Each Zone
            paragraph = paragraphs[i]
            zone = Zone.Zone_3D(paragraph, self.Var_count)
            self.Zones.append(zone)

        return


def print_array(arr, N, name):
    with open(name + ".txt", "w") as f:
        f.write(f"{N}\n")
        for item in arr:
            f.write(f"{item}\n")

def main(input_path = None):
    PRINT_DAT = True
    if input_path is not None:
        path = input_path
    else:
        path = 'tecplot\\'
    print("Decoding Post-processing data")
    if not os.path.exists(path):
        print(f"Error, path does not exist: {path}")
        return
    elif not os.path.isdir(path):
        print(f"Error, please input the directory to which the .dat files are located: {path}")
        
    for file in os.listdir(path):
        filepath = os.path.join(path, file)
        if os.path.isfile(filepath):  # Process Files only

            # Check if the filename ends with .dat
            if filepath.lower().endswith('.dat'):
                print(f"Processing file: {filepath}")
                data = CAE_Decoder()
                data.Decode_dat_file(file)
                # Thus far, only the fluid zone is our interest
                fluid_zone:Zone.Zone_3D = data.Zones[0]
        

                if PRINT_DAT:
                    decoded_path = 'Decoded_Data\\'
                    print('Outputting decoded .dat file')
                    if os.path.exists(decoded_path) == False:
                        os.mkdir(decoded_path)
                    path_written_to = decoded_path + filepath +'\\'
                    if os.path.exists(path_written_to):
                        print('WARNING, data corresponding to timestep ' + filepath + ' has been already generated. Shutting down...')
                        return
                    else:
                        os.mkdir(path_written_to)
                    for i in range(0,3): # 3 dimensions
                        print_array(fluid_zone.Element_Coordinates[i], fluid_zone.Element_count, path_written_to + 'Element_'+ data.Variables[i])
                        print_array(fluid_zone.Node_Coordinates[i], fluid_zone.Node_count, path_written_to + 'Node_'+ data.Variables[i])
                    for i in range(3, data.Var_count):
                        print_array(fluid_zone.Element_Variables[i - 3], fluid_zone.Element_count, path_written_to + 'Element_'+ data.Variables[i])
            
                    print("DONE!!!")
                    
                
            
        
    else:
        print(f"Warning: '{filepath}' is not a .dat file, ignoring...")
    

if __name__ == "__main__":
    main()
