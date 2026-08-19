# Weeds Processing
A repository for doing processing of weeds data collected by the redeveloped weeds app released in October 2025 in lieu of being able to do this processing at the data with attribute rules in AGOL. This has been initially developed by Willie McKay in October 2025, with updates being done in August 2026 to comply with data standards for importing inspection records to IRIS.  The intent is for this to be a temporary solution until the organisation implements an ArcGIS enterprise system which can house the attribute rules as part of the dataset. 

## Features
* Updates data fields not required to be filled in by pest plant officers that can be auto populated to allow for a better UI for them and certainty and consistency of data which is entered
* Copies base site ID from site table to inspection record to ensure integrity of joins between the site and inspection tables
* Updates contacts in site table from changes made in inspection table
* Uses heartbeat package to notify via email when server processes have not worked
* A batch file for running as a scheduled task in the OperationTasks server
* Events of the script are logged to logWeedsProcessing.log which is part of this repository

## Installation
To use this script first clone the repository onto your local machine.
Right click in your folder of choice and select GIT Bash Here and enter

> git clone https://github.com/williemckay/weeds-processing.git


## Dependancies
* For this to run the heartbeat package by Willie McKay needs to be installed on C:\Scripts\shared of the machine running the script.  This package keeps an eye on scheduled scripts to ensure that they have run and sends alerts by email when they don't
* This script was created in an environment running ArcGIS Pro 3.1.  In other versions of ArcGIS Pro, outputs should be checked to ensure all operations are running

## Contribution Guidelines
To contribute to this repository please adhere to the branching strategy as outlined below and make sure you do frequent commits with meaningful messages.  
Currently Willie McKay and Courtney Tregurtha-Nairn are the 2 developers who are responsible for this repository, with the Biosecurity Pest Plants team being the owners of the dataset.  Any enhancements must come through this team.

### Branching Strategy
Below are the strategies listed with using branches for this repository

### Rules about the main branch
1. The main branch has to be stable and documented as this is the production code which is running live
2. A new branch is to be created for any development, enhancements, and bug fixes as listed in the Issues tab
3. It is only when the branch is tested and stable that it can be merged back into the master branch

### Use of Issues
The issues tab is to be used to log any bugs, enhancements or development ideas to the codebase in this repository. An issue in here is to be used at a scale where it can be addressed and fixed as a branch to be merged back onto the master after fixing
