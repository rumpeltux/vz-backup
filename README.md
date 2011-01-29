studiVZ backup tool
===================

Dieses Programm erstellt ein Backup der eigenen studiVZ-Daten.
Mehr Infos gibts unter [http://itooktheredpill.dyndns.org/2011/goodbye-studivz/](http://itooktheredpill.dyndns.org/2011/goodbye-studivz/)

Limitations
===========
 * Captions von Bildern sind verkürzt, da nicht jede einzelne Bilderseite geladen wird
 * Die eigene Mailbox wird nicht geladen, dafür gibt’s [freepops](http://www.freepops.org) mit dem [studiVZ-Plugin](http://www.andremartin.de/StudiVzPlugin/)
 * Bilder müssen im Anschluss „manuell“ (z.B. mit wget) geladen werden 
 * Captchas werden erkannt, müssen aber ggf. manuell gelöst werden. Sie treten aber nicht häufig auf.
 * Captchas werden nicht gelöst
 * Ein Request-Limit verhindert das komplette Downloaden bei zu vielen aufzurufenden Seiten
   Es tritt dann ein HTTP-Fehler mit dem Code 402 auf, studiVZ hat dann den Account für 24h gesperrt
   Als Workaround hilft nur: die 24h aussitzen und dann das Programm erneut starten.
   Da die Daten gecached werden, muss keine Seite mehrfach runtergeladen werden.

TODO
====
 * HTML-Seite bauen, die die entstandene JSON-Datei liest und eine statische Version seines
   alten studiVZ-Profils darstellt
 * Verbesserung des Parsers für Profilinformationen und HTML Entities
 * Import Tool für Diaspora um die Daten dort weiterzuverwenden sofern möglich

License
=======
Die Software wird unter der [GNU-AGPL-3.0](http://www.gnu.org/licenses/agpl.html) verbreitet.

