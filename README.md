# How to run

- Create a virtual python environment and activate it
```
python -m venv myenv
source myenv/bin/activate
```

- Install the dependencies
```
pip install -r requirements.txt
```

- Install the Playwright's browsers
```
python -m playwright install
```

- Run the script (example)
```
python diseases_cleveland.py
```

# Websites that may be useful if more data is needed

- https://my.clevelandclinic.org/health/diseases?dFR[type][0]=diseases

- https://en.wikipedia.org/wiki/Category:Lists_of_diseases

- https://www.nhsinform.scot/illnesses-and-conditions/a-to-z/

- https://www.mayoclinic.org/diseases-conditions/index?letter=A
