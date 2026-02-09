from flask import Flask
from models.database import db
from controllers.controllers import controllers_bp  
from flask_migrate import Migrate  

app = Flask(__name__) 
app.debug = True 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz_master.sqlite3"
app.secret_key = "your_secret_key"  

db.init_app(app)
migrate = Migrate(app, db)  
app.register_blueprint(controllers_bp)  

if __name__ == "__main__":
    app.run()

