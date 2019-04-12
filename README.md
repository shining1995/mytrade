# fuzz-manager

## Deploy

Run the following commands to install requirements:

```
sudo apt install -y python-pip mysql-server mysql-client libmysqlclient-dev
sudo pip install -r requirements.txt
sudo systemctl enable mysql
sudo systemctl start mysql
```

Config mysql connection in `config.ini`.

## Start

```
python app.py
```
