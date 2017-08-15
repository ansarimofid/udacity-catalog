# Catalog App
  It's a flask based app which shows Item stored in different categories. 
  It implements the CRUD in the app. Along with this it also user third party authentication if someone want to make any changes to the item details or wants to add any items.
  
## Runnig the App
  
##Running
#### Step 1
* Install the dependencies
```Shell
pip install -r requirements.txt
```
#### Step 2
* Setting Environment variable to run the app

Run
```Shell
export FLASK_APP=/Users/ansarimofid/PycharmProjects/catalog/catalog.py
```
```Shell
export FLASK_DEBUG=1   
```
#### Step 3
Run the App
```Shell
flask run 
```
* access the site at ```http://127.0.0.1:5000/```