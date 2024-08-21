# Videos_sensores_genero_edad_data

Este es el programa de software de una solución de HW y SW que se desarrolla para reproducir videos a partir de la detección de presencia a partir de sensores IR de distancia ubicados en estanterias de productos. La solución tambien requiere para su funcionamiento, estar combinada y trabajar en conjunto con el HW de detección y control que se construyó para la detección de una mano que se acerque a tomar un producto en la estanteria, y una vez detectada, se reproduce el video asociado al producto que se procede a tomar de la estanteria.

Una vez es disparada la detección se reproduce el video correspondiente al producto que esta en X posición en la estanteria, el cual tiene asignado un sensor y gracias a una cámara de video web con lente ojo de pez que es conectada tambien al computador y que tambien es necesaria como HW para qeu el programa ejecute, y que a la vez es conectada a computador, se hace una detección del rostro de la persona y se realiza una clasificación de género y de rango de edad de la persona.  No se almacena información visual (fotos) de la persona a la que se le hace la detección de rostro.

El programa escribe en tiempo real en un archivo .csv con fecha y hora la data detectada. Es la unica información que se almacena.

El programa esta escrito en Python 3 y  se ejecuta en un ambiente virtual de este. Tambien rqueire que en un tareminal que se corre aparte, pero en paralelo, ejecute primero un socket de MPV (que es el reproductor escogido para la reproduccion de los videos que ejecuta el programa). En la terminal, se debe llegar a la misma ubbicación donde esta el programa que se va a ejecutar y alli debe ejectarse el comando siguiente para ejecutar el socket en un ambiente de Windows: mpv --idle --input-ipc-server=\\.\pipe\mpvsocket

Una vez activado el sockect de MPV, ya es posible poner en ejecución el programa de python .py con el codigo desarrollado.

