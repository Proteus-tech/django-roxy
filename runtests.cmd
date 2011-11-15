SET PROJECT_PATH=test-projects\latest-django\
echo %PYTHONPATH%
SET PYTHONPATH=%PYTHONPATH%;%PROJECT_PATH%;.
echo %PYTHONPATH%
python %PROJECT_PATH%manage.py test

