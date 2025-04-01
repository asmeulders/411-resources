#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

##########################################################
#
# Boxer Management
#
##########################################################

create_boxer() {
  name=$1
  weight=$2
  height=$3
  reach=$4
  age=$5

  echo "Creating boxer ($name - $age)..."
  curl -s -X POST "$BASE_URL/add-boxer" -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\", \"weight\":\"$weight\", \"height\":$height, \"reach\":\"$reach\", \"age\":$age}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Boxer created successfully."
  else
    echo "Failed to create boxer."
    exit 1
  fi
}

delete_boxer_by_id() {
  boxer_id=$1

  echo "Deleting boxer by ID ($boxer_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-boxer/$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer deleted successfully by ID ($boxer_id)."
  else
    echo "Failed to delete boxer by ID ($boxer_id)."
    exit 1
  fi
}

get_boxers() {
  echo "Getting boxers in the ring..."
  response=$(curl -s -X GET "$BASE_URL/get-boxers") # what is this supposed to be for boxers. "get-all-songs-from-catalog" originally
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxers retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxers JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get Boxers."
    exit 1
  fi
}

get_boxer_by_id() {
  boxer_id=$1

  echo "Getting boxer by ID ($boxer_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-id/$boxer_id") # "get-song-from-catalog-by-id" originally
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by ID ($boxer_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON (ID $boxer_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get boxer by ID ($boxer_id)."
    exit 1
  fi
}

get_boxer_by_name() {
  name=$1

  echo "Getting boxer by name (Name: '$name')..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-name?name=$(echo $name | sed 's/ /%20/g')") # get-song-from-catalog-by-compound-key
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by name."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON (by name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get boxer by boxer."
    exit 1
  fi
}

############################################################
#
# Ring Management
#
############################################################

enter_ring() {
  name=$1
  weight=$2
  height=$3
  reach=$4
  age=$5

  echo "Adding boxer to ring: $name..."
  response=$(curl -s -X POST "$BASE_URL/enter-ring" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\", \"weight\":\"$weight\", \"height\":$height\", \"reach\":\"$reach\". \"age\":$age}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer added to ring successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to add boxer to the ring."
    exit 1
  fi
}

clear_ring() {
  echo "Clearing boxers from the ring..."
  response=$(curl -s -X POST "$BASE_URL/clear-boxers")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxers cleared successfully."
  else
    echo "Failed to clear boxers from the ring."
    exit 1
  fi
}


############################################################
#
# Start fight
#
############################################################

fight() {
  echo "Starting the fight..."
  response=$(curl -s -X POST "$BASE_URL/fight")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "The fight has begun."
  else
    echo "Failed to start the fight."
    exit 1
  fi
}

######################################################
#
# Leaderboard
#
######################################################

# Function to get the boxer leaderboard sorted by wins or win_pct
# get_boxer_leaderboard() { 
#   echo "Getting boxer leaderboard sorted by wins or win percentage..."
#   response=$(curl -s -X GET "$BASE_URL/leaderboard?sort=wins")
#   if echo "$response" | grep -q '"status": "success"'; then
#     echo "Boxer leaderboard retrieved successfully."
#     if [ "$ECHO_JSON" = true ]; then
#       echo "Leaderboard JSON (sorted by wins or win percentage):"
#       echo "$response" | jq .
#     fi
#   else
#     echo "Failed to get boxer leaderboard."
#     exit 1
#   fi
# }
# Function to get the boxer leaderboard sorted by wins or win_pct
get_boxer_leaderboard() {
  echo "Getting boxer leaderboard sorted by wins or win percentage..."
  sort_by=${1:-wins} 

  if [[ "$sort_by" != "wins" && "$sort_by" != "win_pct" ]]; then
    echo "Invalid sort parameter: '$sort_by'. Must be 'wins' or 'win_pct'."
    exit 1
  fi

  response=$(curl -s -X GET "$BASE_URL/leaderboard?sort=$sort_by")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON (sorted by $sort_by):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get boxer leaderboard."
    exit 1
  fi
}

# Initialize the database
sqlite3 db/boxers.db < sql/init_db.sql

# Health checks
check_health
check_db


##############################
#
# Testing
#
##############################

# Create boxers
create_boxer "Muhammad Ali" 236 191 198 38
create_boxer "Mike Tyson" 220 178 180 22
create_boxer "Rocky Balboa" 200 180 188 28

#Delete boxers
delete_boxer_by_id 3

#Retrieve boxers
get_boxers
get_boxer_by_id 2
get_boxer_by_name "Muhammad Ali"

#ring management
enter_ring "Muhammad Ali" 236 191 198 38
enter_ring "Mike Tyson" 220 178 180 22
clear_ring

#start fight
enter_ring "Muhammad Ali" 236 191 198 38
enter_ring "Mike Tyson" 220 178 180 22
fight

#leaderboard
get_boxer_leaderboard #no arguments defaults to wins 
get_boxer_leaderboard win_pct 

echo "All tests passed successfully!"
