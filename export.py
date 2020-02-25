from canvasapi import Canvas
import traceback
import json
import sys
import getopt
import os
import string

# Command options
unixOptions = ""
gnuOptions = ["no_download", "verbose"]
# No downloads, just print IDs
NO_DOWNLOAD = False
# Verbosity
VERBOSE = False
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
# Comma separated string with Assignment IDs that should be skipped
ASSIGNMENTS_TO_SKIP = ''


def makeValidFilename(input_str):
    # Remove invalid characters
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    input_str = "".join(c for c in input_str if c in valid_chars)

    # Remove leading and trailing whitespace
    input_str = input_str.lstrip().rstrip()

    return input_str

def json_to_file(content, output_dir, filename, msg = ''):
    try:
        print(msg, end="")
        if NO_DOWNLOAD is True:
            pass
        else:
            #print(msg + ' to %s/%s' % (output_dir, filename))
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

def download_file(url, output_dir, filename, msg = ''):
    try:
        print(msg, end="")
        if NO_DOWNLOAD is True:
            pass
        else:
            #print(msg + ' to %s/%s' % (output_dir, filename))
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


def download_course(course):
    try:
        # Download course json
        course_output_dir = OUT_DIR + "/" + course.term['name'] + "/" + course.course_code + "/"
        msg = 'Downloading json for course %s "%s" \n' % (course.id, course.attributes['name'])
        json_to_file(course.attributes, course_output_dir, "course_" + str(course.id) + ".json", msg)


        # Loop through Assignments
        assignments = course.get_assignments()
        for assignment in assignments:
            # Skip assignment IDs
            skip_assignments = globals()['ASSIGNMENTS_TO_SKIP'].split(',')
            if str(assignment.id) in skip_assignments:
                continue
            download_assignment(course, assignment)

    except Exception as e:
        print("\033[1mFile download gave the following error:\033[0m")
        print(e)

def download_assignment(course, assignment):
    # Download assignment json
    assignment_dir = OUT_DIR + "/" + course.term['name'] + "/" + course.course_code + "/assignment_" + str(assignment.id) + "/"
    msg = '  Downloading json for assignment %s "%s" \n' % (assignment.id, assignment.attributes['name'])
    json_to_file(assignment.attributes, assignment_dir, "assignment_" + str(assignment.id)+'.json', msg)

    # Loop through Submissions and download them
    submissions = assignment.get_submissions(include=['submission_comments','full_rubric_assessment'])  #include: 'course', 'user', 'submission_history'
    for submission in submissions:
        submission_dir = assignment_dir + "submission_" + str(submission.id) + "/"
        download_submission(submission, submission_dir)

def download_submission(submission, output_dir):
    # Download submission json and any attachment
    msg = '    Downloading json for submission %s' % str(submission.id)
    msg += "\n" if VERBOSE else "\r"
    json_to_file(submission.attributes, output_dir, "submission_" + str(submission.id) + '.json', msg)

    if hasattr(submission, "attachments"):
        for attachment in submission.attachments:
            msg = '      Downloading attachment: %s' % str(attachment['display_name'])
            msg += "\n" if VERBOSE else "\r"
            download_file(attachment['url'], output_dir + "attachments/", str(attachment['display_name']), msg)

    # Loop through comments and download them
    for sub_comment in submission.submission_comments:
        comment_dir = output_dir + "comment_" + str(sub_comment['id']) + "/"
        sub_comment['submission_id'] = submission.id
        download_assignment_comment(sub_comment, comment_dir)


def download_assignment_comment(comment, output_dir):
    # Download comment json and any attachment
    msg = '    Downloading json for comment %s' % str(comment['id'])
    msg += "\n" if VERBOSE else "\r"
    #json_to_file(comment, output_dir, "comment_" + str(comment['id']) + '.json', msg)
    if "attachments" in comment.keys():
        for sub_comment_attachment in comment['attachments']:
            msg = '        Downloading attachment: %s' % str(sub_comment_attachment['display_name'])
            msg += "\n" if VERBOSE else "\r"
            download_file(sub_comment_attachment['url'], output_dir + 'attachments/', sub_comment_attachment['display_name'], msg)

def get_user_id(canvas):
    # Canvas User ID
    user = canvas.get_user('self')
    return user.id

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
        skip_courses = globals()['COURSES_TO_SKIP'].split(',')

        for course in courses:
            if str(course.id) in skip_courses:
                continue

            #course_output_dir = OUT_DIR + "/" + course.term['name'] + "/" + course.course_code + "/"
            #downloadCourseJSON(course, course_output_dir)

            #print("  Downloading files for course %s \"%s\"" % (course.id, course.name))
            download_course(course)

    except Exception as e:
        print("\033[1mSkipping entire course due to the following error:\033[0m")
        print(e)

    print("\nProcess complete. All canvas data exported!")

if __name__ == "__main__":
    try:
        arguments, values = getopt.getopt(sys.argv[1:], unixOptions, gnuOptions)
        for currentArgument, currentValue in arguments:
            if currentArgument in ("--no_download"):
                print("Skip any download, just print IDs\n")
                globals()['NO_DOWNLOAD'] = True
            if currentArgument in ("--verbose"):
                globals()["VERBOSE"] = True
        main()
    except Exception as e:
        print("Exiting due to uncaught exception:")
        print(e)
        print(traceback.format_exc())
