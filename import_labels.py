import csv
import os
import sys
import datetime

from os.path import dirname, abspath, join, isfile
sys.path.insert(0, os.getcwd())

from paste.deploy import appconfig
from pylons import config

from abstrackr.config.environment import load_environment
from abstrackr.model.meta import Session
import abstrackr.model as model

from sqlalchemy import and_
from sqlalchemy.orm import load_only
from sqlalchemy import func
from sqlalchemy.orm import Load
from sqlalchemy import desc

reload(sys)

sys.setdefaultencoding('utf-8')

conf = appconfig('config:development.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

def import_csv_with_labels(project_id, csv_file_location):
    project = Session.query(model.Project).filter_by(id = project_id).first()
    
    with open(csv_file_location) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        users, assignments = parse_csv_header(next(csv_reader), project)

        for row in csv_reader:
            parse_csv_row(row, users, assignments, project)
        
        Session.commit()

def parse_csv_header(header, project):
    users = []
    assignments = []
    for uname in header[1:]:
        user = Session.query(model.User).filter_by(username = uname).first()
        users.append(user)
        assignment = Session.query(model.Assignment).filter_by(project_id = project.id).filter_by(user_id = user.id).first()
        assignments.append(assignment)
    return users, assignments
         
def parse_csv_row(row, users, assignments, project):
    source_id = row[0]
    citation = Session.query(model.Citation).filter_by(project_id = project.id).filter_by(pmid = source_id).first()
    for index, label_val in enumerate(row[1:]):
        if label_val:
            user = users[index]
            assignment = assignments[index]
            label = model.Label()
            label.project_id = project.id
            label.study_id = citation.id
            label.assignment_id = assignment.id
            label.user_id = user.id
            label.labeling_time = 1
            label.first_labeled = datetime.datetime.utcnow()
            label.label_last_updated = datetime.datetime.utcnow()
            label.label = label_val
            model.Session.add(label)
            print "Created label " + label_val + " by user " + user.username + " for " + str(citation.id)

def main(argv):
    import_csv_with_labels(argv[0], argv[1])

if __name__ == "__main__":
    main(sys.argv[1:])
