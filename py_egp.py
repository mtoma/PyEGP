import xml.etree.ElementTree as ET
from collections import defaultdict
from anytree import Node, RenderTree, AsciiStyle
import pprint
import tempfile
import zipfile
import shutil
import os
import os.path
import sys

_pp = pprint.PrettyPrinter(indent=4)

def _etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(_etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

def _extract_node_info(node_id, root, project_unpacked_folder):
#	print("extract_node_info:["+node_id+']')
    elements = root.findall(f".//*[ID='{node_id}']/..")
#	print(str(elements))
    node_info = {}
    for elem in elements:
        d = _etree_to_dict(elem)
#		_pp.pprint(d)
        try:
#			print(d['Element']['Element']['Label'])
            node_info['label'] = d['Element']['Element']['Label']
            node_info['type'] = d['Element']['Element']['Type']
            
#            print(project_unpacked_folder+'/'+node_id+'/'+'code.sas')
            if os.path.isfile(project_unpacked_folder+'/'+node_id+'/'+'code.sas'):
                node_info['code'] = open(project_unpacked_folder+'/'+node_id+'/'+'code.sas', 'r').read()
            else:
                code_id = ''
                code_id = d['Element']['SubmitableElement']['JobRecipe']['JobRecipe']['code']
                print('code_id:['+code_id+']')
                code_elements = root.findall(f".//*[ID='{code_id}']/..")
                print(code_elements)
                code_d = _etree_to_dict(code_elements[0])
    #			pp.pprint(code_d)
                node_info['code'] = code_d['Element']['TextElement']['Text']
    #			node_info['code'] = 'CODE FOUND'
        except KeyError as e:
            if str(e) != "'Element'" and str(e) != "'SubmitableElement'": print('KeyError:'+str(e))
                
    return node_info

class PyEGP:
	__unpacked_egp_folder = None
	__root_id = None
	__nodes_info = None
	
	def __init__(self, sas_egp_file_name):
		print("epg file:["+sas_egp_file_name+"]")
		dir_name, file_name = os.path.split(sas_egp_file_name)
		print('temp folder:['+tempfile.gettempdir()+']')
		shutil.rmtree(tempfile.gettempdir()+'/'+file_name, ignore_errors=True)
		os.makedirs(tempfile.gettempdir()+'/'+file_name)
		with zipfile.ZipFile(sas_egp_file_name, 'r') as zip_ref:
			zip_ref.extractall(tempfile.gettempdir()+'/'+file_name)
			
		self.__unpacked_egp_folder = tempfile.gettempdir()+'/'+file_name
		self.__tree = ET.parse(self.__unpacked_egp_folder+'/project.xml')
		
	def __scan_egp_file(self):
		root = self.__tree.getroot()
		elements = root.findall(".//Element[@Type='SAS.EG.ProjectElements.Link']")
#		print(str(elements))
		from_list = []
		to_list = []
		nodes_info = {}
		tree_nodes = []
		for element in elements:
			d = _etree_to_dict(element)
			try:
#				_pp.pprint(d)
				if d['Element']['Log']['LinkFrom'] and d['Element']['Log']['LinkTo']:
					if d['Element']['Log']['LinkFrom'] not in from_list: from_list.append(d['Element']['Log']['LinkFrom'])
					if d['Element']['Log']['LinkTo'] not in to_list: to_list.append(d['Element']['Log']['LinkTo'])
					
					if d['Element']['Log']['LinkFrom'] not in nodes_info:
						node_info = _extract_node_info(d['Element']['Log']['LinkFrom'], root, self.__unpacked_egp_folder)
						if 'label' in node_info:
							nodes_info[d['Element']['Log']['LinkFrom']] = Node(node_info['label'], task_id=d['Element']['Log']['LinkFrom'], info=node_info)

					if d['Element']['Log']['LinkTo'] not in nodes_info:
						node_info = _extract_node_info(d['Element']['Log']['LinkTo'], root, self.__unpacked_egp_folder)
						if 'label' in node_info:
							nodes_info[d['Element']['Log']['LinkTo']] = Node(node_info['label'], task_id=d['Element']['Log']['LinkTo'], info=node_info)
					
					if nodes_info[d['Element']['Log']['LinkTo']].parent != None:
						if nodes_info[d['Element']['Log']['LinkFrom']].info['type'] in ['TASK']:
							nodes_info[d['Element']['Log']['LinkTo']].parent = nodes_info[d['Element']['Log']['LinkFrom']]
					else:
						nodes_info[d['Element']['Log']['LinkTo']].parent = nodes_info[d['Element']['Log']['LinkFrom']]
			
			except KeyError as e:
				pass
			except Exception as e:
				print(f'EXCEPTION ({type(e).__name__}):'+str(e))
				pass
			
		self.__nodes_info = nodes_info
#		_pp.pprint(self.__nodes_info)

		max_tree_size = 0
		for task_id in from_list:
			if task_id not in to_list and task_id in self.__nodes_info:
				tree_size = 0
				for pre, _, node in RenderTree(self.__nodes_info[task_id], style=AsciiStyle):
					tree_size+=1
					
				if tree_size > max_tree_size:
					max_tree_size = tree_size
					self.__root_id = task_id

#		print("ROOT ID:["+self.__root_id+']')
		
	def print_main_project(self):
		if not self.__nodes_info: self.__scan_egp_file()
		for pre, _, node in RenderTree(self.__nodes_info[self.__root_id], style=AsciiStyle):
			print("%s%s" % (pre, node.name))

	def get_list_of_tasks(self):
		return [node for pre, _, node in RenderTree(self.__nodes_info[self.__root_id])]
'''
	
	
'''
