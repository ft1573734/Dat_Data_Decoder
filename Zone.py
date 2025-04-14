import re
from xml.sax.handler import DTDHandler
from tqdm import tqdm
import numpy as np
from collections import defaultdict

"""
# Class Zone_3D:
# A data structure used for storing a zone for a 3D model
# The main components are as follows
# Elements: #Elements (#: Number of)
# Faces: #Faces
# Nodes: #Nodes
# ZoneType: Self-explainatory
# Parameters:
#   X, Y, Z: float[Nodes] arrays
#   U, V, W, P, K, E: float[Elements] arrays
"""

class Zone_3D:
    
    Zone_name = ''
    Zone_type = ''
    Element_count = ''
    Face_count = ''
    Node_count = ''
    Node_Coordinates = []
    Element_Variables = []
    Element_Coordinates = []
    NCPF = []
    FN = []
    LE = []
    RE = []

    def generateMesh(self):
        
        return 

    def __init__(self, raw_content, var_count):
        
        # Construting the line of DT=(...)
        splitter_DT = 'DT=('
        for i in range(0, var_count):
            splitter_DT += 'DOUBLE'
            if i < var_count - 1:
                splitter_DT += ' '
        splitter_DT += ')'
        
        sections = raw_content.split(splitter_DT)
        _vars = sections[1]
        
        # Extracting header
        _header = sections[0]
        # Extracting Zone name
        lines = _header.split('\n')
        self.Zone_name = lines[0].replace('"', '')
        # Extracting Node, Element, Face counts & Zonetype
        for line in lines:
            if line.strip().startswith('Nodes'):
                line = line.replace(' ', '')
                parts = line.split(',')
                for part in parts:
                    pairs = part.split('=')
                    if pairs[0] == 'Nodes':
                        self.Node_count = int(pairs[1])
                    elif pairs[0] == 'Elements':
                        self.Element_count = int(pairs[1])
                    elif pairs[0] == 'Faces':
                        self.Face_count = int(pairs[1])
                    else:
                        self.Zone_type = pairs[1]
                        
        # Extracting parameter values
        
        vals_components = _vars.split("#")
          
        DT = vals_components[0]
        
        for i in range(1, len(vals_components)):
            component = vals_components[i]
            if component.startswith(' node count per face'):
                # Since each face is stored in a single line, we can directly acquire the node count per face
                # by counting each line. Therefore, we don't need to keep NCPF for now.
                continue
            elif component.startswith(' face nodes'):
                face_nodes = component
            elif component.startswith(' left elements'):
                left_elements = component
            elif component.startswith(' right elements'):
                right_elements = component


        '''
        Decoding DT:
        '''
        # Processing DT
        print("Decoding DT:")
        DT_array = DT.replace("\n","").replace("   ","  ").replace("  "," ").strip().split(" ")
        
        N = self.Node_count
        E = self.Element_count
        
        if len(DT_array) != 3*N + (var_count - 3)*E:
            print("WARINING, The length of DT could be wrong.")

        N = self.Node_count
        E = self.Element_count
        F = self.Face_count
        
        visited_element = 0
        for i in tqdm(range(0, var_count)):
            if i < 3:
                tmp_var_txt = DT_array[visited_element: visited_element + N]
                visited_element += N
                tmp_var_double = np.zeros(N, dtype=np.float64)
                for i in range(0, N):
                    tmp_var_double[i] = np.float64(tmp_var_txt[i])
                self.Node_Coordinates.append(tmp_var_double)
            else:
                tmp_var_txt = DT_array[visited_element: visited_element + E]
                visited_element += E
                tmp_var_double = np.zeros(E, dtype=np.float64)
                for i in range(0, E):
                    tmp_var_double[i] = np.float64(tmp_var_txt[i])
                self.Element_Variables.append(tmp_var_double)
                

            
        '''
        Decoding node_count_per_face:
        '''
        # print("Decoding NCPF:")
        # self.NCPF = self.decode_regular_part(node_count_per_face)

        '''
        Decoding face_nodes:
        '''
        print("Decoding FN:")
        self.FN = self.decode_face_nodes(face_nodes)
        
        '''
        Decoding left_elements:
        '''
        print("Decoding LE:")
        self.LE = self.decode_regular_part(left_elements, self.Face_count)
        
        '''
        Decoding right_elements:
        '''
        print("Decoding RE:")
        self.RE = self.decode_regular_part(right_elements, self.Face_count)

        self.decode_element_centroids()

    def decode_regular_part(self, array_in_text, N):
        lines = array_in_text.split("\n")[1:]
        values_in_txt = []
        for line in tqdm(lines):
            if len(line) == 0:
                continue
            tokens = line.strip().replace("   ","  ").replace("  "," ").split(" ")
            for token in tokens:
                values_in_txt.append(token)
        
        if len(values_in_txt) != N:
            print("Error, decoding regular array wrong.")
        
        result = np.zeros(N, dtype = np.int64)
        for i in range(0, N):
            result[i] = np.int64(values_in_txt[i])
            
        return result
    
    def decode_face_nodes(self, array_in_text):
        lines = array_in_text.split("\n")[1:]
        result = []
        for line in tqdm(lines):
            if len(line) == 0:
                continue
            processed_line = []
            elements = line.strip().split(' ')
            for element in elements:
                processed_line.append(np.int64(element))
            result.append(processed_line)
            
        return result
        

    def decode_element_centroids(self):
        face_centroids = np.zeros((self.Face_count,3), dtype=np.float64)
        
        X = self.Node_Coordinates[0]
        Y = self.Node_Coordinates[1]
        Z = self.Node_Coordinates[2]
        
        print("Loading faces:")
        #for face_nodes in tqdm(zone.FN):
        for i in tqdm(range(0, self.Face_count)):
            nodes_on_each_face = self.FN[i]
            centroid = np.zeros(3)
            #sum x,y,z 
            for i in nodes_on_each_face:
                # The FN index starts with 1, therefore we need '-1'.
                centroid[0] += X[i-1]
                centroid[1] += Y[i-1]
                centroid[2] += Z[i-1]
            # compute average
            centroid = centroid/len(nodes_on_each_face)
            # print(centroid)
            face_centroids[i] = centroid
            
        print("Loading mesh cells:")
        # # The first step is to find the faces of each cell using LE (left element) and RE (right element)
        # min_LE = np.min(self.LE)
        # max_LE = np.max(self.LE)
        # min_RE = np.min(self.RE)
        # max_RE = np.max(self.RE)
        # if (max_RE - min_RE) != (max_LE - min_LE):
        #     print("ERROR, Left Element & Right Element do not match.")
        #     exit()
            
        # # WARNING: For unknown reasons some of the LE/RE values starts with 1 instead of 0. 
        # # Therefore, we need to check LE/RE values and adjust to 0-initiated arrays.
        # unified_LE = np.subtract(self.LE, min_LE)
        # unified_RE = np.subtract(self.RE, min_RE)

        element_faces = defaultdict(set)
        print("Processing left elements:")
        for i in tqdm(range(0, len(self.LE))):
            e = self.LE[i]
            # element '0' represents the boundary element, omit it during computation
            if e == 0: 
                continue
            
            # The effective numbering of elements starts with 0,
            # for the sake of unified representation, we number elements starting 0
            e = e - 1 
            if e in element_faces:
                e = e - 1 # for the sake of unity, we number elements starting 0
                # since e is a left element of face i, i naturally becomes a face of e
                element_faces[e].add(i)
            else:
                # if i is not in the dictionary, create a new face
                element_faces[e] = {i}
                
        # The same process repeats for the right elements
        print("Processing right elements:")
        for i in tqdm(range(0, len(self.RE))):
            e = self.RE[i]
            # element '0' represents the boundary element, omit it during computation
            if e == 0: 
                continue
            # The effective numbering of elements starts with 0,
            # for the sake of unified representation, we number elements starting 0
            e = e - 1 
            if e in element_faces:
                #since e is a right element of face i, i naturally becomes a face of e
                element_faces[e].add(i)
            else:
                element_faces[e] = {i}
        
        ''' Un-comment the following lines if adjacency information is needed. '''
        # # When processing LE and RE, the adjacency relationship is also formed.
        # # Manually constructing a adjaceny matrix with shape zone_fluid.Elements * zone_fluid.Elements, and zone_fluid.LE or *.RE NNZs.
        # # This is a sparse matrix, stored in COO format        
        # rows = np.zeros(len(unified_LE)) #len(unitifed_LE) & len(unified_RE) are interchangable.
        # cols = np.zeros(len(unified_LE))
        # data = np.zeros(len(unified_LE))
        # for i in tqdm(range(0, len(unified_LE))):
        #     rows[i] = unified_LE[i]
        #     cols[i] = unified_RE[i]
        #     data[i] = 1
        #     #for symmetry
        #     rows[i] = unified_RE[i]
        #     cols[i] = unified_LE[i]
        #     data[i] = 1

        # #adj_matrix = coo_matrix((data, (rows, cols)), shape=(zone_fluid.Elements, zone_fluid.Elements))
        # #Adjacency = []
        

        # #for i in tqdm(range(0,adj_matrix.shape[0])):
        #     #records the neighbours of this row
        #     #tmp_adj = []
        #     #tmp_row = adj_matrix.getrow(i) #The coo_matrix.getrow() func returns a row in CSR format, therefore-
        #     #for j in range(0, len(tmp_row.indices)): #-we only need to fetch the csr_matrix.indices for the position of each nnz element
        #         #tmp_adj.append(j)
        #     #Adjacency.append(np.asarray(tmp_adj))
            
        
        #Now that the faces of each element is set, we can compute the geometric centers of each cell
        print("Loading X, Y, Z:")
        Element_X = np.zeros(self.Element_count)
        Element_Y = np.zeros(self.Element_count)
        Element_Z = np.zeros(self.Element_count)
        for i in tqdm(range(0,self.Element_count)):
            tmpFaces = element_faces.get(i)
            centroid = np.zeros(3)
            for f in tmpFaces:
                centroid[0] += face_centroids[f][0]
                centroid[1] += face_centroids[f][1]
                centroid[2] += face_centroids[f][2]
            for j in [0,1,2]:
                centroid[j] = centroid[j]/len(tmpFaces)
            Element_X[i] = centroid[0]
            Element_Y[i] = centroid[1]
            Element_Z[i] = centroid[2]
        
        self.Element_Coordinates.append(Element_X)
        self.Element_Coordinates.append(Element_Y)
        self.Element_Coordinates.append(Element_Z)
        

