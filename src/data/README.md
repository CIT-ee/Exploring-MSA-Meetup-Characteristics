## Overview

This directory houses scripts related to creating and validating the data sources associated with this project - *make_dataset.py* and *validate_dataset.py*

**NOTE:** These scripts require a environment variable called *PROJECT_PATH* which you can set by running the following command - `export PROJECT_PATH=<path to project dir>`

## Details

* `make_dataset.py`: This script has methods useful for building the data sources associated with this project. To start the data building process, simply run `cd <project_dir>` and then `python src/data/make_dataset.py`. By default, the script will scrape the */find/locations* endpoint of the **Meetup API**. There are several optional arguments that you can supply to the script, as described below:

    * To change the endpoint, run `python src/data/make_dataset.py --endpoint <endpoint_name>`
    * To specify a subcategory of data to scrape from the same endpoint, run `python src/data/make_dataset.py --query <query_name>`
    * To enable checkpointing, run `python src/data/make_dataset.py --chkpnt_freq <chkpnt_freq_num>`. This will write the scraped data to disk after every *checkpnt_freq_num* iterations
    * To resume from a previous checkpoint, run `python src/data/make_dataset.py --resume <resume_bool>`
    
* `validate_dataset.py`: **TODO**
