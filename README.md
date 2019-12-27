(Working progress)

# Pirra - Facturas electronicas AFIP como Zeus manda

Configuracion de entorno
------------------------

1. Instalar paquetes del sistema necesarios

        sudo apt-get install openssl libssl-dev swig libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev libpq-dev redis-server python-dev
        #si se agrega algo aca agregarlo tambien a las tasks de ansible
        
2. Instalar pip y virtualenv

        sudo apt install python3-pip
        sudo pip3 install virtualenv virtualenvwrapper

3. Crear y activar virtualenv

        mkvirtualenv -p python3 pirra
        workon pirra

4. Si mkvirtualenv no funciona entonces

        sudo pip3 install virtualenv
        virtualenv env
        . env/bin/activate

5. Instalar paquetes de python

        pip3 install -r requirements/dev.txt

6. Copiar template de settings
        
        cp pirra_web/settings/dev.template.py pirra_web/settings/dev.py
        # editar lo que quieran cambiar de settings en pirra_web/settings/dev.py

7. Instalar requerimientos npm
        
        npm install

8. Configurar y Crear BD

    considerar que la versión de postgres que se necesita utilizar es la 9.4
        
        sudo apt-get install postgresql
        sudo -u postgres psql postgres
        \password postgres # elegir un password y poner el mismo en pirra_web/settings/dev.py
        #salir de psql (ctrl+d)
        sudo -u postgres createdb pirra
        python manage.py migrate
        
    O se puede utilizar docker-compose
        
       docker-compose up

9. Crear un superusuario
        
        python manage.py createsuperuser

10. Crear empresa

        python manage.py init_empresa [NRO_DOC] [EMPRESA]        
        
10. Cargar los datos de aplicacion AFIP (para tener tipos de comprobante, moneda, etc)

        python manage.py loaddata afip/fixtures/initial_data.json 
        # elegir el schema public


11. Cargar datos del padron de inscripcion a la afip

        python manage.py load_padron --limit 1000 #carga solamente los primeros 1000

12. Correr el server de prueba

        python manage.py runserver
        npm run watch

13. Para ver el sistema corriendo entrar a localhost:8000 (no funciona si usan 127.0.0.1:8000)

Migraciones
-----------

* Generar nuevas migraciones

        python manage.py makemigrations

* Ejecutar migraciones (cada vez que traemos cambios de git):
        
        python manage.py migrate 


