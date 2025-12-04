# how to run

First make sure you are running the solr container same way as Milestone2


## To run the backend

First install the dependencies
~~~
cd backend
pip3 install -r requirements.txt
~~~
then run the main
~~~
python3 main.py
~~~

## To run the frontend

NOTE: make sure you have node installed in your machine

First install the dependencies:

~~~
cd frontend
npm install
~~~

Then run it 
~~~
npm run dev
~~~

you can run using docker by running:
~~~
docker-compose up --build
~~~

![application view](image.png)