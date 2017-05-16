import time
import csv
import os
import sys
sys.path.insert(0, os.getcwd())
from math import ceil

from paste.deploy import appconfig
from pylons import config

from abstrackr.config.environment import load_environment
from abstrackr.model.meta import Session
from abstrackr.lib.make_predictions_sklearn import make_predictions
import abstrackr.model as model
import pubmedpy

from sqlalchemy import and_
from sqlalchemy.orm import load_only
from sqlalchemy import func
from sqlalchemy.orm import Load
from sqlalchemy import desc

from random import randrange
from random import sample

from collections import defaultdict

reload(sys)

sys.setdefaultencoding('utf-8')

conf = appconfig('config:development.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

def _create_reviews(p_id, iter_size, which_iter):
    u_id = 2629
    k_init = 400
    c_count = len(Session.query(model.Citation).filter_by(project_id = p_id).all())
    k_inc = 500

    for itercount in range(iter_size * which_iter , iter_size * which_iter + iter_size):
        ### THIS is the code for one run of the experiment
        
        ## labeled citation counter
        labeled_citation_counter = 0

        labels = Session.query(model.Label).filter_by(project_id = p_id).all()
        user = Session.query(model.User).filter_by(id = u_id).first()
        citations = Session.query(model.Citation).filter_by(project_id = p_id).all()
        print len(citations)
        c_count = len(citations)
        r_sample = defaultdict(list)

        sample_indexes = sample(range(c_count), k_init)
        C_r = []
        for ii in sample_indexes:
            C_r.append(citations[ii])
        for cc in C_r:
            for ll in Session.query(model.Label).filter_by(project_id=p_id).filter_by(study_id=cc.id).all():
                r_sample[ll.study_id].append(ll)

        new_review = model.Project()
        new_review.leaders.append(user)
        new_review.initial_round_size = 0
        new_review.tag_privacy = True

        Session.add(new_review)
        Session.flush()

        state_dict = defaultdict(int)
        citation_dict = {}    

        for c in citations:
            citation = model.Citation()
            citation.project_id = new_review.id
            citation.title = c.title
            citation.abstract = c.abstract
            citation.keywords = c.keywords
            model.Session.add(citation)
            Session.flush()

            citation_dict[citation.id] = c.id

            if c.id in r_sample:
                labeled_citation_counter += 1
                state_dict[citation.id] = 1
                for t in r_sample[c.id]:
                    label = model.Label()
                    label.project_id = new_review.id
                    label.study_id = citation.id
                    label.label = t.label
                    model.Session.add(label)

        print new_review.id
        Session.commit()

        ## i is a counter for the current increment
        i = 0

        while True:

            ## we want to change the increment size if there are a certain number of citations is labeled
            if labeled_citation_counter > 15000:
                k_inc = 2000
            elif labeled_citation_counter > 5000:
                k_inc = 1000
            else:
                k_inc = 500

            r_sample = defaultdict(list)
            print "EXPERIMENT NO: " + str(itercount)
            make_predictions(new_review.id)

            ######################## here's where I record the results
            preds_for_review = Session.query(model.Prediction).filter(model.Prediction.project_id == new_review.id).all()
            path_to_preds_out = os.path.join("_exports", "predictions_%d_%d_of_%d.csv" % (p_id, i, itercount))
            with open(path_to_preds_out, 'w+') as fout:
                csv_out = csv.writer(fout)
                preds_file_headers = ["citation_id", "title", "predicted p of being relevant", "'hard' screening prediction*", "state"]
                csv_out.writerow(preds_file_headers)
                sorted_preds = sorted(preds_for_review, key=lambda x : x.predicted_probability, reverse=True)

                for pred in sorted_preds:
                    citation = Session.query(model.Citation).filter(model.Citation.id == pred.study_id).first()
                    #citation = self._get_citation_from_id(pred.study_id)
                    citation_title = citation.title.encode('ascii', 'ignore')
                    row_str = [citation.id, citation_title, pred.predicted_probability, pred.prediction, state_dict[citation.id]]
                    csv_out.writerow(row_str)
            ######################### ---------------------------

            P_a = []
            for pa in Session.query(model.Prediction).filter_by(project_id=new_review.id).order_by(model.Prediction.predicted_probability.desc()).all():
                if state_dict[pa.study_id] == 0:
                    P_a.append(pa)
                    if len(P_a) == k_inc:
                        break

            if len(P_a) == 0:
                print "~~~NO PREDS!!!"
                ccc = [label for label in Session.query(model.Citation.id).filter_by(project_id=new_review.id).filter(~model.Citation.labels.any()).limit(k_inc)]
                print len(ccc)
                for cc in ccc:
                    labeled_citation_counter += 1
                    state_dict[cc.id] = 1
                    for ll in Session.query(model.Label).filter_by(study_id=citation_dict[cc.id]).all():
                        label = model.Label()
                        label.project_id = new_review.id
                        label.study_id = cc.id
                        label.label = ll.label
                        model.Session.add(label)
            else:
                for pp in P_a:
                    labeled_citation_counter += 1
                    state_dict[pp.study_id] = 2
                    for ll in Session.query(model.Label).filter_by(project_id=p_id).filter_by(study_id=citation_dict[pp.study_id]).all():
                        label = model.Label()
                        label.project_id = new_review.id
                        label.study_id = pp.study_id
                        label.label = ll.label
                        model.Session.add(label)
            Session.commit()

            i += 1
            if labeled_citation_counter >= c_count:
               break 
            
            print len(Session.query(model.Label).filter_by(project_id=new_review.id).all())
    return

def main(argv):
    _create_reviews(int(argv[0]), int(argv[1]), int(argv[2]))

if __name__ == "__main__": 
    main(sys.argv[1:])

