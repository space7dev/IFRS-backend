# Deployment instructions
- Make sure you have installed all dependencies including gunicorn in the virtual environment
---

### FILES TO BE UPDATED
For Development:
- gunicorn/gunicorn_dev.py
- systemctl/dev.service
- nginx/dev.nginx.conf

For Staging:
- gunicorn/gunicorn_stage.py
- systemctl/staging.service
- nginx/staging.nginx.conf

For production:
- gunicorn/gunicorn_prod.py
- systemctl/production.service
- nginx/prod.nginx.conf

---

#### gunicorn_conf.py
 TO UPDATE: ``user`` `` bind``


### production.service
TO UPDATE:
- ``Description`` short description
- ``User``
- ``Group``
- ``WorkingDirectory`` root working directory of your project
- ``ExecStart``  PATH_TO_PROD_VIRTUALENV, PATH_TO_PROD_GUNICORN_CONF_FILE, PATH_FOR_LOGFILE

### MAKE SURE YOU HAVE CREATED ``LOG`` FOLDER ALREADY AND YOU UPDATED ALL FILES PATHS ACCORDINGLY IN EVERY FILE

---

- `cd /etc/systemd/system`
- `sudo ln -s /home/django/sites/<project>/src/deployment/systemctl/staging.service`
- `sudo ln -s /home/django/sites/<project>/src/deployment/systemctl/staging.socket`
- Check /run to see if the .sock file is created
- To see if the gunicorn process is running: `sudo systemctl status staging.service`

- Go into the nginx config directory `cd /etc/nginx/sites-enabled`
- Remove the default and then link to our config in the deployment directory: `sudo ln -s /home/django/sites/<project>/src/deployment/nginx/nginx-stage.conf`
- Check the file paths inside the nginx.conf file to match the project paths
- Test your Nginx configuration for syntax errors by typing `sudo nginx -t`
- Restart nginx service by typing `sudo systemctl restart nginx`

---

### INSTALL SSL CERTBOT
follow the steps
- `sudo apt-get update`
- `sudo apt-get install software-properties-common`
- `sudo add-apt-repository universe`
- `sudo add-apt-repository ppa:certbot/certbot`
- `sudo apt-get update`

Now install certbot package for nginx
- `sudo apt-get install certbot python-certbot-nginx`
- Run this command to get a certificate and have Certbot edit your Nginx configuration automatically to serve it, turning on HTTPS access in a single step.

- `sudo certbot --nginx`


