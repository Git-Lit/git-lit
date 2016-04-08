import os
import shutil
import distutils
from os import path
from distutils import dir_util

class ed:
#Ici, c'est l'endroit pour affecter des attributs de classe, notamment ici le ed_repository

	def __init__(self, book):
#Dans le constructeur d'une classe, on declare tous les attributs des objets qui peupleront cette classe
	  self.book = book
          self.book_id = self.book.book_id
	def make(self,cufolder):
	#I would certainly like to have this new_name_f variable below as a global variable for all the class
          new_name_f = self.book_id+'_ed'
	  dir_to_create = os.path.join(cufolder,new_name_f)
	  repository = os.makedirs(dir_to_create)

	def ed_structure(self,cufolder,ed_repository):
	  new_name_f = self.book_id+'_ed'
	  dir_to_create = os.path.join(cufolder,new_name_f)
	  distutils.dir_util.copy_tree(ed_repository,dir_to_create)  	

	# def add_mdt_ed_repository(name):
          

def start_ed(book):
	processed_file = ed(book)
	ed_repository = 'ed'
	cufolder = os.path.dirname(os.path.abspath(__file__))
	processed_file.make(cufolder)
	repository_population = processed_file.ed_structure(cufolder,ed_repository)




		
