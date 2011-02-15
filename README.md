studiVZ backup tool
===================

Dieses Programm erstellt ein Backup der eigenen studiVZ-Daten.
Mehr Infos gibts unter [http://itooktheredpill.dyndns.org/2011/goodbye-studivz/](http://itooktheredpill.dyndns.org/2011/goodbye-studivz/)

Wenn euch die Software gefällt bzw. nützt, freut sich der Autor über flattr:

[![Flattr this](http://api.flattr.com/button/button-static-50x60.png)
](https://flattr.com/thing/64757c282dfa2d2fbfd8b085bfe2ac95/Goodbye-studiVZ)

Aufruf
======

    ./studivz.py email password [what]

Wobei ``what`` eine kommaseparierte Kombination aus folgenden Einträgen ist:

 * ``self``: eigene Fototags, -alben und Pinnwand
 * ``profiles``: Profile der Freunde
 * ``tags``: Tagged Fotos der Freunde
 * ``albums``: Fotoalben der Freunde
 * ``friends``: Freundeslisten der Freunde (limitiert auf Name, Profilbild und Uni)
 * ``pinboards``: Pinnwandeinträge der Freunde

Ein Beispiel:

    ./studivz.py email password self,profiles,tags

Zu beachten: Gerade ``pinboards`` und ``albums`` benötigen viele Requests, sodass man schnell an das
Request-Limit (siehe Limitations) stößt.

Limitations
===========
 * Captions von Bildern sind verkürzt, da nicht jede einzelne Bilderseite geladen wird
   (ansonsten käme man zu schnell an das Downloadlimit, das den Account sperrt)
 * Die eigene Mailbox wird nicht geladen, dafür gibt’s [freepops](http://www.freepops.org) mit dem [studiVZ-Plugin](http://www.andremartin.de/StudiVzPlugin/)
 * Bilder müssen im Anschluss „manuell“ (z.B. mit wget) geladen werden 
 * Captchas müssen manuell gelöst werden. Sie treten aber nicht häufig auf.
 * Ein Request-Limit verhindert das komplette Downloaden bei zu vielen aufzurufenden Seiten
   Es tritt dann ein HTTP-Fehler mit dem Code 402 auf, studiVZ hat dann den Account für 24h gesperrt
   Als Workaround hilft nur: die 24h aussitzen und dann das Programm erneut starten.
   Da die Daten gecached werden, muss keine Seite mehrfach runtergeladen werden.
 * Anführungszeichen im Namen der Freunde führen zu Problemen. Hintergrund:
   Die Freundesliste wird aus den JSON-Daten vom studiVZ geladen, HTML-Entities werden aber schon
   vorher geparst, so dass die Anführungszeichen von JS und dem geparsten Namen nicht zu unterscheiden
   sind und zu einem Parser-Fehler führen (Siehe Issue:#2). Momentanes Workaround:
   Den entsprechenden Namen im HTML-Quelltext der Zip-Datei (``Messages/WriteMessage``) per Hand fixen.

TODO
====
 * HTML-Seite bauen, die die entstandene JSON-Datei liest und eine statische Version seines
   alten studiVZ-Profils darstellt
 * Verbesserung des Parsers für Profilinformationen
 * Import Tool für Diaspora um die Daten dort weiterzuverwenden sofern möglich

License
=======
Die Software wird unter der [GNU-AGPL-3.0](http://www.gnu.org/licenses/agpl.html) verbreitet.

