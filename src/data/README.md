## Overview

This directory houses scripts related to creating and validating the data sources associated with this project - *make_dataset.py* and *wrangle_dataset.py*

**NOTE:** These scripts require a environment variable called *PROJECT_PATH* which you can set by running the following command - `export PROJECT_PATH=<path to project dir>`

## Details

* `make_dataset.py`: This script has methods useful for building the data sources associated with this project. To start the data building process, simply run `cd <project_dir>` and then `python src/data/make_dataset.py` with the necessary accompanying arguments. The general structure of the command is shown below:

   ```
   python src/data/make_dataset.py [OPTIONS]

   DESCRIPTION
       --endpoint          the meetup api endpoint to scrape
       --query             namespace for set of optional subfields
       --batch=INT         batch idx to operate on
       --chkpnt_freq=INT   frequency at which to perform checkpoints
       --resume=BOOLEAN    flag: resume from checkpoint or not
   ```
    
* `wrangle_dataset.py`: This script has general purpose methods to manipulate existing data sources like break datasets into batches, consolidate batches into a master dataset and add MSA data to an existing dataset.

   ```
   python src/data/make_dataset.py [OPTIONS]

   DESCRIPTION
       --op                operation to perform
       --endpoint          the meetup api endpoint to scrape
       --query             namespace for set of optional subfields
       --batch=INT         batch idx to operate on
   ```
