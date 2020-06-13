# silenc-detected
Detección de silencios de audios y recorte de audios por silencios con python

El script ejecuta secuencialmente los siguientes bloques de código:

* Lee todos los ficheros con formato .wav que se encuentran dentro del directorio audios/pending (si el directorio no está creado debe hacerlo)

* Analiza cada fichero de audio y detecta todos los bloques de silencios que tiene

* Analiza los bloques que se encuentren entre 4:30 y 5:30, al encontrar los bloques tomará el bloque que tenga el silencio más largo

* Se armarán bloques hasta llegar al final del audio y finalmente se recortaran en bloques entre 4:30 y 5:30

**NOTA:**
Los ficheros procesados se moverán al directorio audios/cut/name_audio/name_audio.wav junto con los ficheros recortados
