mkdir myapi
cd myapi
python -m venv venv
--------------------------
--- window ----
venv\Scripts\activate
---- mac || linux ------
source venv/bin/activate
--------------------------
pip install flask

-----> create file <-----
app/__init__.py
app/config.py
app/extension.py

===================
How to run 
source .venv/bin/activate
python wsgi.py     