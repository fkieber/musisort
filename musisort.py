#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

"""
Arrangement de plusieurs répertoires contenant de la musique
============================================================

Ce programme prend le contenu de plusieurs répertoires contenant
de la musique et le fusionne vers un autre répertoire.

La fusion se fait de façon à prendre un fichier de chaque répertoire,
un après l'autre et de le placer dans le répertoire de destination.
Le nom des fichiers ainsi que le nom du morceau du TAG du fichier
sont préfixés par un n° de série pour respecter l'ordre.
Si un répertoire ne contient pas assez de fichiers, ceux-ci sont repris
depuis le début.
Exemple : 

Rép1        Rep2        Rep3        Dest
-----------------------------------------------
fich11.mp3  fich21.mp3  fich31.mp3  01_fich11.mp3
fich12.mp3  fich22.mp3  fich32.mp3  02_fich21.mp3
fich13.mp3              fich33.mp3  03_fich31.mp3
                        fich33.mp3  04_fich12.mp3
                        fich34.mp3  05_fich22.mp3
                        fich35.mp3  06_fich32.mp3
                                    07_fich13.mp3
                                    08_fich21.mp3
                                    10_fich33.mp3
                                    11_fich11.mp3
                                    12_fich22.mp3
                                    13_fich34.mp3
                                    14_fich12.mp3
                                    15_fich21.mp3
                                    16_fich35.mp3

"""

# Idées ======================================================================

# Copie des fichier par liens matériels ou symboliques (ATTENTION, dans ce cas
# les TAGS sont modifiés sur le fichier d'origine !!! )

# Inclure de façon aléatoire les fichiers d'un répertoire.

# Répartir les fichiers des différents répertoires :
# 1. Selon le nombre
# 2. Selon la durée des morceaux

# Éviter les doublons en se basant sur les tags, le nom...

# Mode mini-verbose :
# Affichage minimaliste du travail effectué :
# R01-001, R02-001, R03-001, R01-002, etc.
# Rnn = Répertoire nn
# nnn = n° du morceau dans le répertoire.

# Modules importés ===========================================================
import os, sys, fnmatch, re, random
import argparse
import shutil
from mutagen.easyid3 import EasyID3

# Gestion graphique
from Tkinter import *
import tkFileDialog, tkMessageBox

# Configuration ==============================================================
version="0.3.0"

# Constantes =================================================================

# Noms pour les aides
nm_src="SOURCES"
nm_dst="DEST"

# Fichiers traités (en minuscules S.V.P.)
files_ext = ('*.mp3', '*.flac', '*.ogg', '*.aac')

# Liste des abréviations des tags pour le renommage des fichiers
lst_tags = {
  'a': 'artist', 
  't': 'album', 
  'n': 'tracknumber', 
  'i': 'title'}

# filtre pour les noms de fichier (expression régulière)
#name_filter = r'[^' + string.letters + string.digits + r' \-.]'
name_filter = r'[?*\/:]|'

# Valeur de --verbose pour l'affichage 'debug'
_dbg_vbv = 4

# Fonctions ==================================================================

def px(txt):
   """Print and exit
      Fonction de débogage.
      Imprime le texte puis quitte le programme
   """
   
   print (txt)
   sys.exit(0)

# Classes ====================================================================

class File:
# ----------------------------------------------------------------------------
   """ Description d'un fichier
      
      Paramètres à la création :
         p_path : Chemin vers le fichier
         p_name : Le nom du fichier
      
      Propriétés :
         path : Chemin complet du fichier (avec le nom)
         name : nom du fichier (sans le chemin)
         ext  : Extension du fichier (avec le '.' devant)
         tags : Liste des tags du fichier avec ses valeurs
      
      Fonctions : 
         lec_tag : Lecture des tags d'un fichier
         get_name : Formation d'un nom à partir des tags
         new_file : Retourne le nouveau nom du fichier en fonction des tags 
            et des arguments de la ligne de commande.
         new_artist : Retourne le nouvel artiste du morceau en fonction des tags 
            et des arguments de la ligne de commande.
         new_album : Retourne le nouvel album du morceau en fonction des tags 
            et des arguments de la ligne de commande.
         new_title : Retourne le nouveau titre du morceau en fonction des tags 
            et des arguments de la ligne de commande.
   """
   
   def __init__(self, p_path, p_name):
   # -------------------------------------------------------------------------
      
      self.name = p_name
      self.path = p_path + '/' + p_name
      self.tags = self.lec_tag()
      self.ext  = os.path.splitext(p_name)[1]
      
   def lec_tag(self):
   # -------------------------------------------------------------------------
      
      """Lecture des TAGs du fichier passé en paramètre
         Au retour, un dictionnaire :
         { tagid, valeur_du tag }
         tagid est transformé pour correspondre aux lettres du programme
         (voir lst_tags)
      """
      
      global args
      
      # Préparation du dictionnaire en sortie
      tags = lst_tags.fromkeys(lst_tags.keys())
      
      # Récup infos ID3 et formation du nouveau nom
      try:
         audio = EasyID3(self.path)
      except:
         # En cas d'erreur, on retourne le dictionnaire vide
         return tags
      
      # Extraction des tags
      if args.verbose >= _dbg_vbv:
         print """Liste des tags pour %s :
            %s""" % (self.path, audio.valid_keys.keys())
      ak = audio.keys()
      
      # Si aucun tag , on retourne le dictionnaire vide
      if len(ak) <= 0:
         return tags
      
      # Pour chaque tag accepté
      for k in lst_tags.keys():
         
         # Prendre sa valeur
         kn = lst_tags[k]
         
         # Est-il dans le fichier ?
         if kn in ak:
            
            # Oui, prendre sa valeur
            kv = audio.get(kn)[0]
            
            # Compléter les nombres par des zéros
            if kn == 'tracknumber':
               kv = kv.rjust(3, '0')
         
         # Pas ce tag, le mettre à blanc
         else:
            kv = ''
         
         # Remplacer la valeur dans le dictionnaire de retour
         tags[k] = kv

      if args.verbose >= _dbg_vbv:
         print """Valeur des tags retenus pour %s
            %s""" % (self.path, tags)

      # Retourne le fruit de tout ce dure travail
      return tags
      
   def get_name(self, motif, sequ):
   # -------------------------------------------------------------------------
      
      """Génère un nom à partir des TAGS du fichier en cours
         Entrée : 
            motif : motif des tags. Exemple : '%a-%i'.
            sequ  : n° de séquence pour le tag %s.
      """
      
      # Par facilité, lire les données en cours
      tags = self.tags
      
      # On ajoute le n° de séquence
      tags['s'] = "%04d" % sequ
      
      # tags qu'on veut
      name = motif
      
      # Pour chaque tag accepté
      for k in tags.keys():
         
         # Prendre sa valeur
         kv = tags[k]
         
         # Remplacer les tags qu'on veut
         name = name.replace('%' + k, kv)
         
      # Enlever les caractères indésirables
      to_name = re.sub(name_filter, '', name)

      # Retourne le fruit de tout ce dur travail
      return to_name
         
   def new_name(self, sequ):
      
      """Retourne le nouveau nom du fichier en fonction des tags 
            et des arguments de la ligne de commande."""
      
      # Si le nom doit être transformé, on le fait
      if args.file_name <> '':
            return self.get_name(args.file_name, sequ) + self.ext
      
      # Sinon, on garde le même nom
      else:
         return self.name

   def new_artist(self, sequ):
      
      """Retourne le nouvel artiste du morceau en fonction des tags 
            et des arguments de la ligne de commande."""
      
      # S'il doit être transformé, on le fait
      if args.artist <> '':
            return self.get_name(args.artist, sequ)
      
      # Sinon, on garde le même
      else:
         if args.ctags:
            return ''
         else:
            return self.tags['a']

   def new_album(self, sequ):
      
      """Retourne le nouvel album du morceau en fonction des tags 
            et des arguments de la ligne de commande."""
      
      # S'il doit être transformé, on le fait
      if args.album <> '':
            return self.get_name(args.album, sequ)
      
      # Sinon, on garde le même
      else:
         if args.ctags:
            return ''
         else:
            return self.tags['t']

   def new_title(self, sequ):
      
      """Retourne le nouveau titre du morceau en fonction des tags 
            et des arguments de la ligne de commande."""
      
      # S'il doit être transformé, on le fait
      if args.title <> '':
            return self.get_name(args.title, sequ)
      
      # Sinon, on garde le même
      else:
         if args.ctags:
            return ''
         else:
            return self.tags['i']

class RepSrc:
# ----------------------------------------------------------------------------
   """ Répertoire source.
      
      Paramètres à la création :
         src : Chemin du répertoire source
         jumb: Doit-on mélanger les fichiers ?
      
      Propriétés :
         spath = Chemin où se trouvent les fichiers
         nbr  = Nombre de fichiers
         end  = True si tous les fichiers ont été lu par get
         files = liste d'objets "file" dont chaque entrée correspond à un
            fichier. Cette liste est triée par nom de fichier (sans le chemin).
      
      Fonctions :
         get_file : Lecture du fichier en cours
         next : Passage au fichier suivant
      
   """
   
   def __init__(self, src, jumb=False):
   # -------------------------------------------------------------------------
      
      # La source est-elle un chemin  ?
      if not os.path.isdir(src):
         print("*** Erreur : " + src + " n'est pas un répertoire valide.")
         sys.exit(2)
      
      # Sauver le chemin source
      src = os.path.normpath(src)
      self.spath = src
      
      # Extraire la liste des fichiers à traiter
      wld = os.listdir(src)
      
      # Parcourir cette liste pour stocker les fichiers musicaux
      fl = []
      for nm in wld:
         for tf in files_ext:
            if fnmatch.fnmatch(nm.lower(), tf):
               fl.append(nm)
               break;
      
      # Garder le nombre de fichiers
      self.nbr = len(fl)
      
      # Erreur si aucun fichier à traiter
      if self.nbr == 0:
         print("Il n'y a pas de fichiers " + ', '.join(files_ext) + 
            " dans " + src)
         sys.exit(2)
      
      # Tri ou mélange de la liste des fichiers
      if jumb:
         random.shuffle(fl)
      else:
         fl.sort()
      
      # Stocker les infos fichier
      self.files = []
      for nm in fl:
         self.files.append(File(src, nm))
      
      # Se placer sur le premier fichier
      self.idx = 0
      
      # On n'est pas encore à la fin
      self.end = False
   
   def get_file(self):
   # -------------------------------------------------------------------------
      
      """Retourne le fichier en cours"""
      
      return self.files[self.idx]
      
   def next(self):
   # -------------------------------------------------------------------------
      
      """Passe au prochain élément
         Renvoi True, si fin atteinte"""
      
      # Passer au suivant
      self.idx += 1
      
      # Si dépassement, reboucler
      if self.idx >= self.nbr:
         self.idx = 0
         self.end = True
      
      # Retour des données
      return self.end


class OutPut:
# ----------------------------------------------------------------------------
   """ Gestion de la sortie.
      
      Paramètres à la création :
         dst : Chemin de la destination.
      
      Propriétés :
         dst = Chemin où se trouvent les fichiers
         cpt = Nombre de fichiers
         typ = Type de sortie 1=m3u, 2=m3u8, 3=rép
      
      Fonctions :
         out : Sortie d'un fichier
      
   """
   
   def __init__(self, p_dst):
   # -------------------------------------------------------------------------
      # Normaliser le chemin
      self.dst = os.path.normpath(p_dst)

      # Init compteurs
      self.cpt = 0                 # Compteur et numéroteur de fichiers
      
      # prendre l'extension
      dst_ext = os.path.splitext(self.dst)[1]

      # La destination est une liste de lecture
      if dst_ext in ('.m3u', '.m3u8'):
         
         if dst_ext == '.m3u':
            self.typ = 1
         else:
            self.typ = 2
         
         # La destination existe-t-elle ?
         if os.path.exists(self.dst):
            
            # Si ce n'est pas un fichier, erreur
            if not os.path.isfile(self.dst):
               print(("*** Erreur : Le fichier '%s' du paramètre %s "
                  "n'est pas valide.\n" % (p_dst, nm_dst)))
               sys.exit(2)
               
            # Erreur si pas de forçage.
            if not args.force:
               print(("*** Erreur : Le fichier '%s' du paramètre %s existe.\n"
                  "Utiliser l'option --force pour le remplacer." % (p_dst, nm_dst)))
               sys.exit(2)
            
      # La destination est un répertoire   
      else:
         
         self.typ = 3
         
         # La destination existe-t-elle ?
         if not os.path.exists(self.dst):
            
            # Ai-je le droit de le créer ?
            if not args.force:
               print(("*** Erreur : Le chemin '%s' du paramètre %s n'existe pas.\n"
                  "Utiliser l'option --force pour le créer." % (p_dst, nm_dst)))
               sys.exit(2)
               
            # Création du répertoire destination
            try:
               os.makedirs(self.dst)
            except OSError as err:
               print("*** Erreur chemin " + p_dst + " : " + str(err))
               sys.exit(2)

         # La destination est-elle un chemin  ?
         if not os.path.isdir(self.dst):
            print("*** Erreur : " + p_dst + " n'est pas un répertoire valide.")
            sys.exit(2)

         # La destination est-elle vide ?
         self.l_dst = os.listdir(self.dst)
         if len(self.l_dst) > 0:

           # Ai-je le droit de la vider ?
           if not args.force:
             print(("*** Erreur : Le chemin '%s' du paramètre %s contient des fichiers.\n"
               "Utiliser l'option --force pour les remplacer." % (p_dst, nm_dst)))
             sys.exit(2)
   
   def clear(self):
   # -------------------------------------------------------------------------
      """Vidage du répertoire
      """
      
      # Seulement la première fois
      if self.cpt == 0:
         
         # Pour un répertoire, 
         if self.typ == 3:
            
            # on le vide
            for f in self.l_dst:
               try:
                  os.remove(self.dst + '/' + f)
               except OSError as err:
                  print("*** Erreur : Suppression impossible de " + self.dst + '/' + f + " : " + str(err))
                  sys.exit(2)
                  
         # Pour une liste de lecture, on l'ouvre
         else:
            self.listf = open(self.dst, 'w')
   
   def out(self, src, num_src):
   # -------------------------------------------------------------------------
      """Sortie d'un fichier
      """
      
      # Vidage
      self.clear()
      
      # Lecture du fichier à traiter
      f1 = src.get_file()
      
      # Un fichier de plus
      self.cpt += 1
      
      # Pour répertoire
      if self.typ == 3:
         
         # Formation du nom du fichier de destination
         f2 = self.dst + '/' + f1.new_name(self.cpt)
         
         # Transcodage
         if args.codec == 1:
            f2 = f2.encode('utf_8', 'ignore')
         elif args.codec == 2:
            f2 = f2.encode('iso8859_15', 'ignore')

         # Affichage
         w_msg = "Copie de '%s' vers '%s'" % \
               (nm_src + '-' + str(num_src + 1) + '/' + f1.name, 
               f1.new_name(self.cpt))
         
         # Copie
         try:
            
            # Copie physique
            if args.verbose >= 1:
               print(w_msg)
            shutil.copyfile(f1.path, f2)

         except IOError as err:
            print("*** Erreur : copie impossible de %s : %s" % 
            (f1.path, str(err)))
            sys.exit(2)
         
         # Traitement des tag ID3 ............................................
         
         # Init gestion des tags
         audio = EasyID3(f2)
         
         # Effacement des anciens tag si demandé
         if args.ctags:
            audio.delete()
         
         # Mise à jour des tags
         audio['artist'] = f1.new_artist(self.cpt)
         audio['album']  = f1.new_album(self.cpt)
         audio['title']  = f1.new_title(self.cpt)
         
         # Sauvegarde des tags
         audio.save()

      # Pour liste de lecture
      else:
      
         # Affichage
         w_msg = "Ajout de '%s'" % \
               nm_src + '-' + str(num_src + 1) + '/' + f1.name
         
         # Ajout dans la liste
         if args.verbose >= 1:
            print(w_msg)
         self.listf.write(f1.path + "\n")
      

   def close(self):
   # -------------------------------------------------------------------------
      """Fermeture de la liste de lecture
      """
      
      if self.typ <> 3:
         self.listf.close()


# Traitement =================================================================

def parse_args():
# Gestion des paramètres ......................................................
   
   """Définition, parcours et pré-contrôle des options de la ligne de commande
   """
   
   global jumble

   # Définition des paramètres
   parser = argparse.ArgumentParser(
     description="""Arrange les fichiers musicaux des répertoires %s1,
      %s2, etc. vers le répertoire %s selon les options du programme. 
      """ % (nm_src, nm_src, nm_dst))

   parser.add_argument("-V", "--version", action='version', version='%(prog)s ' + version)

   parser.add_argument("-1", "--once", dest='nfill',
     action="store_true",
     help="""Ne complète pas %s en dupliquant les fichier de %s
      si ceux-ci ne sont pas assez nombreux.""" %
       (nm_dst, nm_src))

   parser.add_argument("-s", "--stack", 
     action="store_true",
     help="""Empile les fichiers au lieu de les intercaler.
      Commence par tous les fichiers de %s1 puis continue avec ceux de 
      %s2, etc..""" % (nm_src, nm_src))

   parser.add_argument("-f", "--force", 
     action="store_true",
     help="Force l'écrasement des fichiers de %s." % nm_dst)

   g_codec = parser.add_mutually_exclusive_group()
   g_codec.add_argument("-u", "--utf", dest="codec", 
     action="store_const", const=1,
     help="""Encodage des noms au format UTF-8.""")

   g_codec.add_argument("-e", "--latin", dest="codec", 
     action="store_const", const=2,
     help="""Encodage des noms au format LATIN-1.""")

   parser.add_argument('-v', '--verbose', 
     action='count', default=0,
     help="""Affichage d'informations supplémentaire.
      Peut être répété pour afficher plus d'informations.""")

   parser.add_argument("-d", "--dest", 
     help="""Destination du tri. Si %s est un répertoire, 
      les fichiers de %s sont copié vers celui-ci.
      Si ce paramètre est absent, le répertoire en cours est pris.
      Si ce répertoire n'existe pas, utilisez l'option --force pour le créer.
      Si ce répertoire contient des fichiers,
      utilisez l'option --force pour les remplacer.
      Si %s est un fichier .m3u ou .m3u8 
      une liste de lecture sera créée en fonction de l'extension.
      Si ce fichier existe, utilisez l'option --force pour le remplacer""" % (nm_dst, nm_src, nm_dst))

   parser.add_argument("-r", "--repeat", type=int, nargs='*', 
     default=[],
     help="""Répétition des répertoires en entrée.
      Chaque chiffre représente le nombre de fois qu'un
      répertoire %s correspondant doit être répété.
      Par défaut il est répété une seule fois.
      Si l'on désire répété 2 fois le deuxième répertoire,
      par exemple, il faut précisé 1 pour le premier (-r 1 2).""" % (nm_src))

   parser.add_argument("-j", "--jumble", type=int, nargs='*', 
     default=[],
     help="""Mélange des répertoires en entrée.
      Chaque chiffre représente le répertoire %s qu'il faut mélanger.
      Les répertoires non précisé dans cette liste sont triés par nom de
      fichier.""" % (nm_src))

   parser.add_argument(nm_src, nargs='+',
     help="""Répertoire(s) en entrée.
      Seul les fichiers musicaux (%s) des répertoires %s sont 
      traités.""" % (', '.join(files_ext), nm_src))

   g_tags = parser.add_argument_group(title='tags', 
      description="""Liste des tags à modifier.
      Permet de réaffecter la valeur des "Tags".
      Ces options sont une chaîne de caractères composée 
      de plusieurs caractères de remplacement. %a=artiste, 
      %t=titre album, %n=n° de piste, %i=intitulé du morceau,
      %s=n° de séquence généré par le programme. Celui-ci commence
      par 1 et est incrémenté à chaque fichier. Ce n° permet de respecter
      l’ordre de tri.
      Les autres caractères sont interprétés tel quels.
      (Ces options sont sans effet en cas de sortie vers une liste .m3u ou .m3u8).""")
   
   g_tags.add_argument("-a", "--artist", 
     default='',
     help="""Nouvelle valeur pour le tag 'artiste'.""")

   g_tags.add_argument("-t", "--album", 
     default="Musisort",
     help="""Nouvelle valeur pour le tag 'titre album'.
     Par défaut "%(default)s".""")

   g_tags.add_argument("-i", "--title", 
     default="%s_%i - %a",
     help="""Nouvelle valeur pour le tag 'intitulé du morceau'.
     Par défaut "%(default)s".""")

   g_tags.add_argument("-m", "--file-name", 
     default="%s_%i - %a",
     help="""Nouvelle valeur pour le nom du fichier.
     Chaîne de caractère avec laquelle le fichier sera renommé.
     Le fichier conservera son extension.
     Par défaut le fichier sera nomé : "%(default)s".""")

   g_tags.add_argument("-z", "--clear_tags", dest="ctags",
     action="store_true",
     help="""Spécifie si les "Tags" des fichiers de %s
      doivent êtres effacés avant d'y stocker les nouveaux
      Tag.""" % nm_dst)

   # Lecture et affichage des paramètres -----------------------------------------
   args = parser.parse_args()

   # Liste des arguments
   if args.verbose >= 2:
      print("Options :")
      keys = vars(args).keys()
      for k in keys:
         print ("\t%s = %s" % (k, str(eval('args.' + k))))
      

   # Si repeat saisi, vérifier qu'il y ait correspondant avec les sources et ...
   nbs = len(args.SOURCES)
   nbr = len(args.repeat)
   if nbr > nbs:
      print("""*** Erreur : Il y a trop de valeurs dans l'option --repeat
         par rapport au nombre de sources""")
      sys.exit(2)
      
   # compléter avec des 1 les manquants
   if nbr < nbs:
      for i in range(nbr, nbs):
         args.repeat.append(1)
   
   # Si jumble saisi, vérifier qu'il y ait correspondance avec les répertoires
   # en remplissant la liste des répertoires "jumblés"
   jumble = []
   for j in range(nbs):
      jumble.append(False)
   for j in args.jumble:
      if j <= 0 or j > nbs:
         print("*** Erreur : Valeur %s du paramètre --jumble hors limite" % j)
         sys.exit(2)
      if jumble[j - 1]:
         print("*** Erreur : Valeur %s du paramètre --jumble en double" % j)
         sys.exit(2)
      jumble[j -1] = True
   
   # Plus besoin des arguments de la ligne de commande
   del parser
   
   return args

def main():
# Programme principal ---------------------------------------------------------
   
   """Programme principal"""
   
   global args
   
   # Analyse ligne de commande
   args = parse_args()
   
   # Extraction destination ...................................................

   # Fichier de destination non saisi, prendre '.'
   if args.dest == None:
      p_dst = '.'
   else:
      p_dst = args.dest
   
   # Créer la destination
   out = OutPut(p_dst)

   # Extraction sources .......................................................
   reps=[]
   nb_src = 0
   end_src = []   # Pour savoir si tous les répertoires ont été traités
   for r in args.SOURCES:
      reps.append(RepSrc(r, jumble[nb_src]))
      nb_src += 1
      end_src.append(False)
   
   # Vidage du répertoire de destination ......................................
   
   # Copie des fichiers .......................................................
   n_src = 0               # Compteur/indexe sur sources
   sv_rpt = args.repeat[:] # Pour décompter la répétition des sources
   while True:
      
      # Récupération de la source
      isrc = reps[n_src]
      
      # Si --no-fill et répertoire traité, ne rien faire
      if not args.nfill or not isrc.end:
         
         # Copie du fichier .................................................
         out.out(isrc, n_src)

      # Passage à la source suivante ------------------------------------------
      
      isrc.next()
      
      # Gestion de la fin
      if isrc.end:
         end_src[n_src] = True
      if False not in end_src:
         break
      
      # Pour un simple empilement, on reste sur la même source jusqu'à la fin
      if args.stack:
         if isrc.end:
            sv_rpt[n_src] -= 1
            if sv_rpt[n_src] > 0:   # En cas de répétition on revient au début
               isrc.end = False
            else:
               n_src += 1
      
      # Sinon, on passe à la source suivant à chaque fois
      else:
         # On ne passe à la suivante que s'il ne faut pas la répéter
         sv_rpt[n_src] -= 1
         if sv_rpt[n_src] <= 0:   
            n_src += 1
            if n_src >= nb_src:
               n_src = 0
               sv_rpt = args.repeat[:]
   
   # Terminé
   out.close()
   
# Lancement programme principal
if __name__ == '__main__':
    main()
