# Anywall Python

## Update per utilizzo WebRTC
-Ora utilizziamo Daphne per l'avvio del server, che permette di utilizzare le Websockets senza errori

-Per la condivisione schermo da altre macchine, c'è bisogno di attivare HTTPS (WiP)

### Attivazione HTTPS
https://github.com/FiloSottile/mkcert?tab=readme-ov-file#windows

https://chocolatey.org/install

```
mkcert -install

mkcert *ip della macchina*
```

Utilizzare i file .pem generati nella configurazione di nginx:


Linea di avvio daphne in monitor.py:
```
subprocess.run([
            "daphne",
            "-b" , "",
            "-p", "8000",
            "anywall.asgi:application"
        ], check=True)
```

###Spunti per WiP:
Sostituire ws:// con wss://

Attivare varie flag in settings.py, come:
```
# DEBUG = True
DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*ip della macchina*']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
        'CONFIG': {
            "hosts": [("*ip della macchina*", 6379)],
        },
    },
}

WS_PORT = 8000

CSRF_TRUSTED_ORIGINS = ['*ip della macchina*']

```


Creare custom middleware:
```
# middleware.py
from django.utils.deprecation import MiddlewareMixin

class CustomHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        return response

# settings.py
MIDDLEWARE = [
    ...
    'your_project.middleware.CustomHeadersMiddleware',
    ...
]
```


Aggiungere 
```
if not request.is_secure():
    return redirect('https://' + request.get_host() + request.get_full_path())
```
Alle views



Usare Nginx

https://nginx.org/en/download.html

Estrarre contenuto in C://nginx/

Esempio onfigurazione Nginx (dovrebbe fare da proxy al 127.0.0.1 di Daphne):
```
server {
    listen 80;
    server_name *ip della macchina*;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name *ip della macchina*;

    ssl_certificate C:/path/to/*ip della macchina*.pem;
    ssl_certificate_key C:/path/to/*ip della macchina*-key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

```
Startare nginx
```
start nginx
```
Stoppare nginx
```
nginx -s stop
```
Ricaricare conf senza stoppare nginx 
```
nginx -s reload
```



## Installazione Oracle Linux 9.3
Scaricare la ISO tramite questo link: https://yum.oracle.com/ISOS/OracleLinux/OL9/u3/x86_64/OracleLinux-R9-U3-x86_64-dvd.iso

Creazione support di instalalzione: https://docs.oracle.com/en/learn/usb-media/#installing-oracle-linux-on-compatible-machines

IMPORTANTE: Durante l'installazione, selezionare 'User Creation' e tickare 'Make this user administrator'


## Build e configurazione
Su ambiente Oracle Linux 9, partendo da un'installazione pulita:

### Update e installazione kernel 5.14.0-362.24.1.0.1.el9_3 (unico kernel indifviduato funzionante con NVIDIA drivers)
```
su

yum -y update

yum install epel-release

yum install kernel-5.14.0-362.24.1.0.1.el9_3.x86_64

grubby --set-default /boot/vmlinuz-5.14.0-362.24.1.0.1.el9_3.x86_64

reboot
```

### Git
```
su
dnf install git

git clone https://github.com/gcongedi/Anywall2Windows.git
cd Anywall2Windows/
git checkout delta
cd ..
```

### Pacchetti linux richiesti
è consigliabile installare la maggior parte dei pacchetti tramite l'installer presente a https://crismaitalia-my.sharepoint.com/personal/documentale_crismaitalia_it/_layouts/15/onedrive.aspx?ct=1727877994763&or=Teams%2DHL&ga=1&id=%2Fpersonal%2Fdocumentale%5Fcrismaitalia%5Fit%2FDocuments%2FProgetti%2FAnywall%2FInstaller

Per ambiente di sviluppo, scaricare anche i seguenti e continuare con la procedura:
```
dnf install epel-release
dnf install mesa-libGL-devel
dnf install mesa-libGLU-devel
yum install freeglut-devel
dnf install gcc-c++
dnf install python3-devel



nano /etc/ld.so.conf
add line:
/usr/lib64/

ldconf

/home/*user*/.bashrc
Add line:
export LD_LIBRARY_PATH=/usr/lib64/:$LD_LIBRARY_PATH

updatedb
locate libGLU.so
```

Se dovessero verificarsi altri errori al runtime, reinstallare pyOpenGl
```
pip uninstall pyOpenGL
pip install pyOpenGL
```

## Installazione MySQL

MySQL installation on Oracle Linux 9:

Download package from https://dev.mysql.com/downloads/file/?id=528548
```
dnf install mysql84-community-release-el9-1.noarch.rpm
dnf module disable mysql
dnf install -y mysql-community-server
dnf install mariadb-connector-c-devel.x86_64

systemctl start mysqld
systemctl enable mysqld

sudo grep 'temporary password' /var/log/mysqld.log
mysql -uroot --connect-expired-password -hlocalhost -p'{password_temporanea}' -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'Anywall24\!';"
mysql -uroot -hlocalhost -p'{password}' -e "CREATE DATABASE IF NOT EXISTS myDatabase;"
```

### Creazione virtual environment
```

su *user*
python3 -m venv env
source env/bin/activate

pip install -r Anywall2Windows/dev/requirements.txt
```

### Avvio
è da avviare sempre come utente non su
```
cd Anywall2Windows/
pwd
/path/to/Anywall2Windows/
export PYTHONPATH=PYTHONPATH:/path/to/Anywall2Windows/django/anywall/
```

### Abilitazione gnome extensions
Se si è avviato l'installer citato sopra
```
Riavviare e runnare fix_windows.py come utente non su 
```

## Build eseguibile
pip install pyinstaller

pyinstaller main.spec

./dist/Anywall
