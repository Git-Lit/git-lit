import os
import logging
import shutil
import distutils
import glob
from os import path
from distutils import dir_util
#
class ed:
#Ici, c'est l'endroit pour affecter des attributs de classe, notamment ici le ed_repository

    def __init__(self, book):
#Dans le constructeur d'une classe, on declare tous les attributs des objets qui peupleront cette classe
        self.book = book
        self.book_id = self.book.book_id
        self.new_name_f = self.book.book_id+'_ed'

    def make(self,cufolder):
    #I would certainly like to have this new_name_f variable below as a global variable for all the class
        dir_to_create = os.path.join(cufolder,self.new_name_f)
        repository = os.makedirs(dir_to_create)

    def ed_structure(self,cufolder,ed_repository):
        dir_to_create = os.path.join(cufolder,self.new_name_f)
        distutils.dir_util.copy_tree(ed_repository,dir_to_create) 
        
    def move_markdown(self,cufolder,ed_repository):
        name_folder='*'
        name_file = self.book_id+'.md'
        chemin_fichier = os.path.join(cufolder,name_folder,name_file)
        print(chemin_fichier)
        new_name_file = '2016-01-16-'+self.book_id+'.md'
        fichier_a_faire = os.path.join(cufolder,self.new_name_f,'_posts',new_name_file)
        print(fichier_a_faire)
        for f in glob.glob(chemin_fichier):
            shutil.move(f,fichier_a_faire)    

    # def add_mdt_ed_repository(name):
          

def start_ed(book):
    processed_file = ed(book)
    ed_repository = 'ed'
    cufolder = os.path.dirname(os.path.abspath(__file__))
    processed_file.make(cufolder)
    repository_population = processed_file.ed_structure(cufolder,ed_repository)
    processed_file.move_markdown(cufolder, ed_repository)




        
