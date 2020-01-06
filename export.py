from canvasapi import Canvas
import requests
import traceback
import json
import os
import string

# Canvas API URL
API_URL = ""
# Canvas API key
API_KEY = ""
# My Canvas User ID
USER_ID = 0000000
# Canvas' requester object
requester = None
# Directory in which to download course information to (will be created if not present)
OUT_DIR = "export"
# Comma separated string with Course IDs that should be skipped
COURSES_TO_SKIP = ''


def makeValidFilename(input_str):
    # Remove invalid characters
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    input_str = "".join(c for c in input_str if c in valid_chars)

    # Remove leading and trailing whitespace
    input_str = input_str.lstrip().rstrip()

    return input_str

def json_to_file(content, output_dir, filename):
    try:
        json_str = json.dumps(content, indent=4)

        # Create directory if not present
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filename = makeValidFilename(str(filename))

        with open(output_dir + filename, "w") as out_file:
            out_file.write(json_str)

    except Exception as e:
        print("\033[1mSkipping json dump of %s%s due to the following error:\033[0m" % (output_dir, filename))
        print(e)

def downloadCourse(course, output_dir):
    json_to_file(course.attributes, output_dir, "course_" + str(course.id) + ".json")
    # Consider to save announcements, discussions, pages, modules

def download(url, output_dir, filename):
    """
    Download the file in a url to specified location.

    :param url: URL to download from.
    :param location: The path to download to.
    :type location: str
    """
    try:
        response = requester.request("GET", _url=url)

        # Create directory if not present
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filename = makeValidFilename(str(filename))

        with open(output_dir + filename, "wb") as file_out:
            file_out.write(response.content)

    except Exception as e:
        print("\033[1mSkipping download of %s%s file due to the following error:\033[0m" % (output_dir, filename))
        print(e)
        print('')

def downloadCourseFiles(course):
    try:
        assignments = course.get_assignments()
        for assignment in assignments:
            # Download assignment json
            assignment_dir = OUT_DIR + "/" + course.term['name'] + "/" + course.course_code + "/assignment_" + str(assignment.id) + "/"
            print('    Downloading json for assignment "%s" to %s' % (assignment.attributes['name'], assignment_dir + str(assignment.id) + '.json'))
            json_to_file(assignment.attributes, assignment_dir, "assignment_" + str(assignment.id)+'.json')

            # Download submissions and their attachments
            submissions = assignment.get_submissions(include=['submission_comments','full_rubric_assessment']) #'course', 'user', 'submission_history', '
            for submission in submissions:
                submission_dir = assignment_dir + "submission_" + str(submission.id) + "/"
                json_to_file(submission.attributes, submission_dir, "submission_" + str(submission.id) + '.json')

                if hasattr(submission, "attachments"):
                    for attachment in submission.attachments:
                        download(attachment['url'], submission_dir + "attachments/", str(attachment['display_name']))

                # Download comments and their attachments
                for sub_comment in submission.submission_comments:
                    # Download comment json
                    comment_dir = submission_dir + "comment_" + str(sub_comment['id']) + "/"
                    json_to_file(sub_comment, comment_dir, "comment_" + str(sub_comment['id']) + '.json')
                    if "attachments" in sub_comment.keys( ):
                        for sub_comment_attachment in sub_comment['attachments']:
                            download(sub_comment_attachment['url'], comment_dir, sub_comment_attachment['display_name'])

    except Exception as e:
        print("\033[1mFile download gave the following error:\033[0m")
        print(e)


def main():
    print("Welcome to the Canvas Data Export Tool\n")

    #Read from .env file
    if os.path.isfile(".env"):
        with open('.env', 'r') as f:
            for line in f:
                try:
                    var_val = line.split('=')
                    if len(var_val) !=2:
                        print("\033[1mCould not process entry in .env file:\033[0m " + line)
                        continue
                    globals()[var_val[0]] = var_val[1].rstrip('\n')
                except Exception as e:
                    print("\033[1mCould not read .env due to the following error:\033[0m")
                    print(e)

    # Canvas API URL
    if globals()['API_URL'] == '':
        global API_URL
        API_URL = input("Enter your organization's Canvas Base URL. This is probably https://canvas.instructure.com or https://{schoolName}.instructure.com) ")

    # Canvas API key
    if globals()['API_KEY'] == '':
        print("\nWe will need a valid API key for your user. You can generate one in Canvas once you are logged in.")
        global API_KEY
        API_KEY = input("Enter a valid API key for your user: ")
    
    # Canvas User ID
    global USER_ID
    user_info = requests.get(API_URL + "/api/v1/users/self/profile?access_token=" + API_KEY)
    USER_ID = json.loads(user_info.text)['id']

    print("\nConnecting to canvas\n")
        
    # Initialize a new Canvas object
    canvas = Canvas(API_URL, API_KEY)
    global requester
    requester = canvas._Canvas__requester

    print("Creating output directory: " + OUT_DIR + "\n")
    # Create directory if not present
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    try:
        print("Getting list of all courses\n")
        courses = canvas.get_courses(include="term")

        # Skip course IDs
        globals()['COURSES_TO_SKIP'].split(',')
        skip = globals()['COURSES_TO_SKIP'].split(',')

        for course in courses:
            if str(course.id) in skip:
                continue

            course_output_dir = OUT_DIR + "/" + course.term['name'] + "/" + course.course_code + "/"
            downloadCourse(course, course_output_dir)

            print("  Downloading files for course %s \"%s\"" % (course.id, course.name))
            downloadCourseFiles(course)

    except Exception as e:
        print("\033[1mSkipping entire course due to the following error:\033[0m")
        print(e)

    print("\nProcess complete. All canvas data exported!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Exiting due to uncaught exception:")
        print(e)
        print(traceback.format_exc())