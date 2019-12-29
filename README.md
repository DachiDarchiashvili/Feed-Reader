# Prerequisites
------

`Python >= 3.7`   
`Django >= 3.0.1`   
`postgres >= 12.x`   

# Setup Project 
------

```bash
$ git clone <project_repo>
```

Install dependencies from `requirements.txt` file

```bash
$ cd <project_directory>/
```

```bash
$ pip install -r requirements.txt
```

# Dockerize
------

## 1. Build an image from a Dockerfile

General command: `docker build -t [image_title]:[tag] [context]`

##### Just run: `$ docker build -t feed_reader .`

or `$ docker build -f Dockerfile -t feed_reader .`

## 2. Run containers

```bash
$ docker-compose up -d pgdb
$ docker-compose up -d feed_reader
$ docker-compose up -d nginx
$ docker-compose up -d feed_fetcher
```

or `docker-compose up -d`

## 3. Run migrations and configure staticfiles in feed_reader shell

To run these commands: `$ docker exec -ti feed_reader sh`

```bash
$ python manage.py migrate --settings feed_reader.settings.prod
$ python manage.py collectstatic --settings feed_reader.settings.prod
```

## 4. Restart nginx container

`$ docker-compose restart nginx`

## 5. Done

**check logs:**
`$ docker logs -f feed_fetcher`
