mig:
	python3 manage.py makemigrations
	python3 manage.py migrate

admin:
	python3 manage.py createsuperuser

update:
	python3 manage.py makemessages -l uz
	python3 manage.py makemessages -l en

compile:
	python3 manage.py compilemessages



