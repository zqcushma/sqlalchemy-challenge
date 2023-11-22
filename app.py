# Why are we being forced to use snake style on the rubric? Is camel case not alright?
# Import the dependencies.
from flask import Flask, jsonify
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.automap import automap_base


#################################################
# Database Setup
#################################################
# Create engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the database tables into classes
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a scoped session
# This helps make queries across all the methods defined below
session = scoped_session(sessionmaker(bind=engine))

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
# Define the homepage route
@app.route("/")
def home():
    return (
        f"Welcome to the Climate App API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date"
    )

#Moved variables for use across multiple paths
mostRecent = session.query(func.max(Measurement.date)).scalar()
yearAgo = dt.datetime.strptime(mostRecent, '%Y-%m-%d') - dt.timedelta(days=365)

# Define the precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Query the last 12 months of precipitation data
    prcpData = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= yearAgo).order_by(Measurement.date).all()

    # Convert the query results to a dictionary
    prcpDict = {date: prcp for date, prcp in prcpData}

    # Return the JSON representation of the dictionary
    return jsonify(prcpDict)

# Define the stations route
@app.route("/api/v1.0/stations")
def stations():
    stationList = session.query(Station.station).distinct().all()
    stationArray = [result[0] for result in stationList]
    return jsonify(stationArray)

# Define the tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    activeStations = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    mostActive = activeStations[0][0]

    tobsQuery = session.query(Measurement.tobs).filter(Measurement.station == mostActive).filter(Measurement.date >= yearAgo).all()

    tobsList = [tobs[0] for tobs in tobsQuery]
    
    return jsonify(tobsList)

# Define the start and start-end route
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end=None):
    try:
        # Convert start and end dates to datetime objects
        startDate = dt.datetime.strptime(start, '%Y-%m-%d')
        endDate = dt.datetime.strptime(end, '%Y-%m-%d') if end else None

        # Query TMIN, TAVG, and TMAX for the specified date range
        if endDate:
            tempResults = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
                .filter(Measurement.date >= startDate, Measurement.date <= endDate)\
                .all()
        else:
            tempResults = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
                .filter(Measurement.date >= startDate)\
                .all()

        # Create a dictionary with the temperature information
        tempDict = {
            'TMIN': tempResults[0][0],
            'TAVG': tempResults[0][1],
            'TMAX': tempResults[0][2]
        }

        # Return the JSON representation of the temperature dictionary
        return jsonify(tempDict)

    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD format."}), 400
    
if __name__ == "__main__":
    app.run(debug=True)