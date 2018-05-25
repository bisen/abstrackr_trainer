import pubmedpy
import time
import csv
import sys
import os
from math import ceil

from paste.deploy import appconfig
from pylons import config

from abstrackr.config.environment import load_environment
from abstrackr.model.meta import Session
from abstrackr.lib.exporter import Exporter

import abstrackr.model as model

from sqlalchemy import and_
from sqlalchemy.orm import load_only
from sqlalchemy import func
from sqlalchemy.orm import Load
from sqlalchemy import desc

from random import randrange
from random import sample

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from collections import defaultdict

reload(sys)

sys.setdefaultencoding('utf-8')

conf = appconfig('config:development.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

# studies = Session.query(model.Citation.id, model.Citation.project_id).filter_by(project_id = 6723)
# for s in studies:
#    ll = Session.query(model.Label).filter_by(study_id = s.id)
#    ll.update(dict(project_id = 6723))


def _create_reviews(p_id):
    _exporter = Exporter(id=p_id,file_type='csv')
    _exporter.set_fields(["(internal) id", "(source) id", "pubmed id", "keywords",
                        "abstract", "title", "journal", "authors", "tags", "notes"])
    _exporter.create_export()
    return

p_ids = [73, 493, 2045, 2266, 2453, 2566, 3076, 3415, 3599, 4164, 4167, 4337, 4420, 4877, 5014, 5024, 10173, 10178, 10179, 10180, 10181, 10182, 10183, 10184]

def main():
    for pid in p_ids:
        _create_reviews(pid)

if __name__ == "__main__": 
    main()
