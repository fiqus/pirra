# Pirra - Facturas electronicas AFIP como Zeus manda

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Achille_a_Sciro2.JPG/220px-Achille_a_Sciro2.JPG" width="200" />

> Tetis, temiendo por la vida de su hijo si éste fuera llevado con los combatientes, resolvió esconderlo a la vista de los griegos. Así, corrió a Tesalia, donde Aquiles se educaba bajo la tutela del viejo Quirón; y, llevándolo consigo, lo vistió ocultamente con vestimentas de mujer y lo entregó a un confidente suyo, ordenándole que lo condujera a la isla de Esciro, sede del rey Licomedes, y que allí, bajo el nombre de Pirra, como si fuera una hija de ella, lo custodiara ocultamente [...](https://es.wikipedia.org/wiki/Aquiles_en_Esciro_(Hasse))


Deploy en hashicorp/bionic64 con Vagrant
------------------------

1. Instalar Ansible y VirtualBox

        sudo apt-get install ansible virtualbox

2. Instalar vagrant según https://www.vagrantup.com/intro/getting-started/install.html
        
3. Clonar repositorio

        git clone https://github.com/fiqus/pirra.git

4. Copiar el template de las variables de deploy al archivo de configuración:
 
        cp pirra/deploy/ansible/group_vars/extra-variables.template.yml pirra/deploy/ansible/group_vars/extra-variables.yml

5. Completar las variables del archivo 'extra-variables.yml' con la configuración local que se desee.

6. Ingresar a la carpeta de deploy ubicada en el root del proyecto

        cd deploy

7. Levantar el servidor localmente con Vagrant

        vagrant up

8. El servidor quedará corriendo en localhost:8080

Configuracion de entorno de desarrollo
--------------------------------------

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


