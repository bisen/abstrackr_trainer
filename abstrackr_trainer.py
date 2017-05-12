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
from abstrackr.lib.make_predictions_sklearn import make_predictions

import abstrackr.model as model

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

# studies = Session.query(model.Citation.id, model.Citation.project_id).filter_by(project_id = 6723)
# for s in studies:
#    ll = Session.query(model.Label).filter_by(study_id = s.id)
#    ll.update(dict(project_id = 6723))


def _create_reviews(p_id, iter_size, which_iter):
    u_id = 2629
    k_init = 400
    c_count = len(Session.query(model.Citation).filter_by(project_id = p_id).all())
    k_inc = c_count / 30
    for itercount in range(iter_size * which_iter , iter_size * which_iter + iter_size):
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
            #citation.pmid = c.pmid
            #citation.refman = c.refman
            citation.title = c.title
            citation.abstract = c.abstract
            #citation.authors = c.authors
            #citation.journal = c.journal
            #citation.publication_date = c.publication_date
            citation.keywords = c.keywords
            #citation.tasks = c.tasks
            #citation.priorities = c.priorities
            #citation.labels = c.labels
            model.Session.add(citation)
            Session.flush()

            citation_dict[citation.id] = c.id

            if c.id in r_sample:
                state_dict[citation.id] = 1
                for t in r_sample[c.id]:
                    label = model.Label()
                    label.project_id = new_review.id
                    label.study_id = citation.id
                    #label.user_id = t.user_id
                    #label.assignment_id = t.assignment_id
                    label.label = t.label
                    model.Session.add(label)

        # project_ids.append(new_review.id)
        print new_review.id
        Session.commit()

        num_iters =  1 + int( ceil(1.0 * (c_count - k_init) / k_inc ))

        for i in range(num_iters):

            r_sample = defaultdict(list)
            print "EXPERIMENT NO: " + str(itercount)
            make_predictions(new_review.id)

            ######################## here's where I keep records
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

            if i == num_iters - 1:
                break

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
                    state_dict[cc.id] = 1
                    for ll in Session.query(model.Label).filter_by(study_id=citation_dict[cc.id]).all():
                        label = model.Label()
                        label.project_id = new_review.id
                        label.study_id = cc.id
                        label.label = ll.label
                        model.Session.add(label)
            else:
                for pp in P_a:
                    state_dict[pp.study_id] = 2
                    for ll in Session.query(model.Label).filter_by(project_id=p_id).filter_by(study_id=citation_dict[pp.study_id]).all():
                        label = model.Label()
                        label.project_id = new_review.id
                        label.study_id = pp.study_id
                        label.label = ll.label
                        model.Session.add(label)
            Session.commit()
            print len(Session.query(model.Label).filter_by(project_id=new_review.id).all())
    return

def main(argv):
    _create_reviews(int(argv[0]), int(argv[1]), int(argv[2]))

if __name__ == "__main__": 
    main(sys.argv[1:])

