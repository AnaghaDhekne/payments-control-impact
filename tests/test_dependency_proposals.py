import json
import pytest
from copy import deepcopy
from scripts.run_dependency_review import demo
from scripts.dependency_proposals import build_prompt, validate_proposals, apply_reviews
from scripts.score_dependency_review import score


def test_pending_and_rejected_edges_do_not_change_impact():
    d = demo(); case, batch = d['case'], d['batch']
    assert apply_reviews(case, batch, [])['final'] == []
    review = {**d['result']['review_audit'][0], 'decision': 'REJECT'}
    assert apply_reviews(case, batch, [review])['final'] == []
    assert case['visible_metadata']['edges'] == []
    assert d['result']['final'][0]['path'] == ['R-ADDRESS', 'C-ADDRESS']


@pytest.mark.parametrize('field,value', [('ticket_quote', 'invented'), ('control_quote', ''),
                                        ('source', 'UNKNOWN'), ('relationship', 'MADE_UP')])
def test_bad_proposals_are_rejected(field, value):
    d = demo(); proposal = {**d['batch']['proposals'][0], field: value}
    batch = validate_proposals(d['case'], json.dumps({'proposals': [proposal]}))
    assert not batch['proposals']
    assert len(batch['validation_rejections']) == 1


def test_stale_and_duplicate_reviews_fail_closed():
    d = demo(); case = deepcopy(d['case'])
    case['change_ticket']['text'] += ' Modified.'
    with pytest.raises(ValueError, match='Stale'):
        apply_reviews(case, d['batch'], [])
    review = d['result']['review_audit'][0]
    with pytest.raises(ValueError, match='duplicate'):
        apply_reviews(d['case'], d['batch'], [review, review])
    with pytest.raises(ValueError, match='reviewer'):
        apply_reviews(d['case'], d['batch'], [{**review, 'reviewer': ''}])


def test_prompt_excludes_hidden_answers_and_manifest():
    case = demo()['case']; case['degradation_manifest'] = {'removed_edge_ids': ['SECRET-EDGE']}
    case['ground_truth'] = 'SECRET-LABEL'
    prompt = build_prompt(case)
    assert 'SECRET' not in prompt


def test_scoring_counts_rejected_review_work_and_incorrect_approvals():
    d = demo(); result = d['result']
    labels = {'affected_control_ids': ['C-ADDRESS'], 'key_control_ids': ['C-ADDRESS'],
              'correct_proposal_ids': []}
    metrics = score(result, labels)
    assert metrics['key_miss_recovery_rate'] == 1
    assert metrics['incorrect_approved_edges'] == 1
    assert metrics['total_review_items'] == 2
    result = {**result, 'final': [], 'review_audit': [{**result['review_audit'][0], 'decision': 'REJECT'}]}
    assert score(result, labels)['proposal_reviews'] == 1
    assert score(result, labels)['key_miss_recovery_rate'] == 0
