# Description
This utility can be used to download data about courses and student submissions from [Canvas Learning Management System](https://www.instructure.com/canvas/) by Instructure.  


# Getting Started
## Dependencies
To run the program, install the dependencies listed in the requirements.txt file:  
`pip install -r requirements.txt --user`  
Note that the requirements include [CanvasAPI](https://github.com/ucfopen/canvasapi), which is the library used in this utility to download json data and files.  

## Canvas API
To export data from Canvas LMS you need two pieces of information: 
* API KEY, which can be generated in your Canvas log in page under Profile > Settings > Approved Integrations
* API URL i.e. your organization's Canvas Base URL, which is the URL of your Canvas LMS page where you log in to

You need administration privileges on the courses you want to export. 

## Running the script

Export all data:  

`python export.py`

Print out course, assignment, submission IDs and files without downloading them:  

`python export.py --no_download`

## Optional Configuration
This script will prompt the user for getting the API URL and API KEY. 
However, you can configure create a .env in this repository using the example file example_dotenv:
`cp example_dotenv .env`

The parameters that can be configured in .env are:
- Canvas API URL
- Canvas API key
- Output directory (default: "export")
- Comma separated list of Course IDs that should be skipped
- Comma separated list of Assignment IDs that should be skipped

Tip: run `python export.py --no_download` to get the Course IDs and Assignment IDs without downloading them

## Export
The exported data include raw json data that can be downloaded using [Canvas API](https://canvasapi.readthedocs.io/en/latest/index.html), and submission attachments to submissions. 
In particular, the exported json files include: courses, assignments, submissions. The rubrics and full rubric assessments are included in the exported files

## Reading the data using Python
Check the [Process_export.ipynb](https://github.com/aless80/canvas-lms-data-export/blob/master/Process_export.ipynb) notebook and an example of dataframes extracted to the pickle file *example_dataframes.pkl*:
```
with open('example_dataframes.pkl', 'rb') as f: 
	df_files, df_rubrics, df_rubricsubmitted = pickle.load(f)
```

## Possible further development
* Consider to save announcements, discussions, pages, modules, other attachment files
* Consider to implement anonymization

## Credits
[David Katsandres](https://github.com/davekats)'s script [canvas-student-data-export](https://github.com/davekats/canvas-student-data-export). 
