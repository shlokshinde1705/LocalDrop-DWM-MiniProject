"""
Test Suite: Data Mining Machine Learning Module Verification
Verifies Classification accuracy, K-Means clustering, and Apriori association rules.
"""

import pytest
from mining import classification, clustering, association


def test_classification_pipeline():
    res = classification.run_classification(force_refresh=True)
    assert res['status'] == "SUCCESS"
    assert 'decision_tree' in res
    assert 'naive_bayes' in res

    dt_acc = res['decision_tree']['metrics']['accuracy']
    nb_acc = res['naive_bayes']['metrics']['accuracy']

    assert dt_acc >= 85.0, f"Decision tree accuracy ({dt_acc}%) should exceed 85%"
    assert nb_acc >= 70.0, f"Naive Bayes accuracy ({nb_acc}%) should exceed 70%"
    assert len(res['relevance_ranking']) >= 5, "Should have ranked features"


def test_clustering_pipeline():
    res = clustering.run_clustering(force_refresh=True)
    assert res['status'] == "SUCCESS"
    assert res['k_selected'] == 3
    assert len(res['cluster_profiles']) == 3
    assert res['silhouette_score_k3'] > 0.40, "Silhouette score for k=3 should indicate good separation"

    # Verify cluster profiles contain expected keys
    for cp in res['cluster_profiles']:
        assert 'centroid_orders' in cp
        assert 'centroid_spending' in cp
        assert 'title' in cp


def test_association_pipeline():
    res = association.run_association(force_refresh=True)
    assert res['status'] == "SUCCESS"
    assert res['total_rules_discovered'] > 0, "Apriori must discover non-empty association rules"
    assert len(res['rules']) > 0

    top_rule = res['rules'][0]
    assert top_rule['lift'] >= 1.0, "Lift metric must be >= 1.0"
    assert top_rule['confidence'] > 0.0
