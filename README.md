# musisort
Make your music mix from multiple sources



This python 2 script takes the contents of several directories 
containing Music and merges it into another directory.

The merge is done to take a file from each SOURCE directory,
and place them in the DEST directory.

## Usage

```
usage: musisort [-h] [-V] [-1] [-s] [-f] [-u | -e] [-v] [-d DEST]
                [-r [REPEAT [REPEAT ...]]] [-j [JUMBLE [JUMBLE ...]]]
                [-a ARTIST] [-t ALBUM] [-i TITLE] [-m FILE_NAME] [-z]
                SOURCES [SOURCES ...]

positional arguments:
  SOURCES               Input directory(s). Only music files
                         (* .mp3, * .flac, * .ogg, * .aac) of the SOURCES directories
                         are treated.

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -1, --once            Do not complete DEST by duplicating the
                        SOURCES if there are not enough of them.
  -s, --stack           Stack files instead of inserting them.
                        Start with all files from SOURCES1
                        Continues with those of SOURCES2, etc.
  -f, --force           Forces the DEST files to be overwritten.
  -u, --utf             Encoding of names in UTF-8 format.
  -e, --latin           Encoding of names in LATIN-1 format.
  -v, --verbose         Display of additional information. May be
                        Repeated to display more information.
  -d DEST, --dest DEST  Destination of sorting. If DEST is a directory, the
                        SOURCE files are copied to it. If this
                        Parameter is absent, the current directory is
                        taken. If this directory does not exist, use
                        The --force option to create it. If this directory
                        Contains files, use the --force option to
                        Replace them. If DEST is a .m3u or .m3u8 file
                        A playlist will be created based on
                        The extension. If this file exists, use the option
                        --force to replace it
  -r [REPEAT [REPEAT ...]], --repeat [REPEAT [REPEAT ...]]
                        Répétition des répertoires en entrée. Chaque
                        chiffre représente le nombre de fois qu'un
                        répertoire SOURCES correspondant doit être
                        répété. Par défaut il est répété une seule
                        fois. Si l'on désire répété 2 fois le deuxième
                        répertoire, par exemple, il faut précisé 1 pour le
                        premier (-r 1 2).
  -j [JUMBLE [JUMBLE ...]], --jumble [JUMBLE [JUMBLE ...]]
                        Mélange des répertoires en entrée. Chaque chiffre
                        représente le répertoire SOURCES qu'il faut
                        mélanger. Les répertoires non précisé dans cette
                        liste sont triés par nom de fichier.

tags:
  Liste des tags à modifier. Permet de réaffecter la valeur des "Tags".
  Ces options sont une chaîne de caractères composée de plusieurs
  caractères de remplacement. %a=artiste, %t=titre album, %n=n° de piste,
  %i=intitulé du morceau, %s=n° de séquence généré par le programme.
  Celui-ci commence par 1 et est incrémenté à chaque fichier. Ce n°
  permet de respecter l’ordre de tri. Les autres caractères sont
  interprétés tel quels. (Ces options sont sans effet en cas de sortie
  vers une liste .m3u ou .m3u8).

  -a ARTIST, --artist ARTIST
                        Nouvelle valeur pour le tag 'artiste'.
  -t ALBUM, --album ALBUM
                        Nouvelle valeur pour le tag 'titre album'. Par défaut
                        "Musisort".
  -i TITLE, --title TITLE
                        Nouvelle valeur pour le tag 'intitulé du morceau'.
                        Par défaut "%s_%i - %a".
  -m FILE_NAME, --file-name FILE_NAME
                        Nouvelle valeur pour le nom du fichier. Chaîne de
                        caractère avec laquelle le fichier sera renommé. Le
                        fichier conservera son extension. Par défaut le
                        fichier sera nomé : "%s_%i - %a".
  -z, --clear_tags      Spécifie si les "Tags" des fichiers de DEST doivent
                        êtres effacés avant d'y stocker les nouveaux Tag.
```

## Implementation

Just put the scrypt in /usr/local/bin fo rexemple.

## Dependencys
media-libs/mutagen  (https://github.com/quodlibet/mutagen)
