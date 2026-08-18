cOpsBackups
A repository for backing up data from ArcGIS Online which is collected for the Catchment Operations group, and associated data quality checks to ensure the data is sound and meets quality requirements. This has been developed by Willie McKay in May 2024.

Features
Downloads authoratative Catchment Operations group data from ArcGIS Online and writes date stamped backups to the network (\gisdata\gis\Department\Environmental_Management\CatchmentOperations\Backups)
Performs quality assurance checks to allow data owners to spot if any records may be missing, both geometrically and in attributes
Emails data owners a report of records in the dataset as well as storing date stamped logs based on the above quality assurance checks
Installation
To use this script first clone the repository onto your local machine.
Right click in your folder of choice and select GIT Bash Here and enter

git clone https://github.com/williemckay/weeds-processing.git

Note

Look at me I can include notes!

Dependancies
Insert some words about both data and package/system dependancies

Contribution Guidelines
To contribute to this repository please adhere to the branching strategy as outlined below and make sure you do frequent commit's with meaningful messages.

Branching Strategy
Below are the strategies listed with using branches for this repository

Rules about the main branch
The main branch has to be stable and documented
A new branch is to be created for any development, enhancements, and bug fixes as listed in the Issues tab
1 branch should
It is only when the branch is tested and stable that it can be merged back into the master branch
Use of Issues
The issues tab is to be used to log any bugs, enhancements or development ideas to the codebase in this repository. An issue in here is to be used at a scale where it can bbe addressed and fixed as a branch to be merged back onto the master after fixing
