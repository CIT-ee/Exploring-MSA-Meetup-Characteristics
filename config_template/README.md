## Overview

This is a template to use for setting up your config files needed to make the source code for this repository work as expected. To get started, after cloning the repository, run the following command: `cp -r config_template config`. Once the proper config directory is created, feel free to adjust/change the contents of the different constituent files to suit your needs. You may choose to remove the *config_template* directory after but note that every pull from the repository will reinitialize the directory. Please refrain from modifying its contents without prior notification.

## Details

 The description of the usage of the different underlying files is provided below:
 
1. `resources.py`: Primarily consists of a dictionary of paths useful at various points in the source code of this repository. You may set the DATA_PATH environment variable (pointing to the root of the directory housing the data files) explicitly on command line or as part of an `.env` file. However, please make sure the variable has been properly exported, failing which the paths defined in this file will not work as expected. The paths defined in this template adhere to the overall project's structure, especially with regards to the data files with suitable storage under the *raw*, *interim*, *external* and *filtered* subdirectories.

2. `api_specs.py`: Primarily consists of a dictionary of API related parameters and other information that may prove useful in the execution of the source code in the repository. Each key on the first level in the dictionary is an alias for the endpoint (*locations* and *events* were used as referenced in the source code). 

    The *locations* key has an dictionary of api endpoint fields where the key is the name of the dataframe column and the value is the field name. 

    The *events* key points to a dictionary of dictionaries wherein each key is an alias to a subcategory of information you are interested in scraping from that endpoint - *topics* and *attendance* are used in the source code. 

    Each of these *sub-category* dictionaries consist of two properties `only` and `fields`, each of which points to a list of field names/keywords. See [Meetup API documentation](https://www.meetup.com/meetup_api/) for information on what keywords to use.
